import discord
import asyncio

from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

from Utilities import Checks, AssetCreation, PageSourceMaker, Links

import random
import math

class PvP(commands.Cog):

    def __init__(self, client):
        self.client = client

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('PvP is ready.')

    #INVISIBLE
    def getAction(self, strategy):
        reaction = random.randint(1,100)
        
        if reaction <= strategy['attack']:
            return 'attacked'
        elif reaction <= strategy['attack'] + strategy['block']:
            return 'blocked'
        elif reaction <= strategy['attack'] + strategy['block'] + strategy['parry']:
            return 'parried'
        elif reaction <= strategy['attack'] + strategy['block'] + strategy['parry'] + strategy['heal']:
            return 'recovered'
        else:
            return 'bided their time'

    def calcDamage(self, action, attack):
        dealt = attack + random.randint(1,10)
        taken = 1

        if action == 'blocked':
            dealt *= .1
            taken *= .05

        elif action == 'parried':
            dealt *= .5
            taken *= .5

        elif action == 'recovered' or action == 'bided their time':
            dealt = 0
            taken *= .875

        return dealt, taken

    def checkCrit(self, crit, damage, attack, acolyte1, acolyte2):
        is_crit = random.choices(['Normal', 'Crit'], [100-crit, crit])
        if is_crit[0] == 'Crit':
            damage *= 2

            try:
                if acolyte1['Name'] == 'Aulus' or acolyte2['Name'] == 'Aulus': #Aulus gives crit bonuses
                    attack += 50
            except TypeError:
                pass

        try:
            if acolyte1['Name'] == 'Paterius' or acolyte2['Name'] == 'Paterius': #Doesn't need a crit, but placed here for brevity
                damage += 15
        except TypeError:
            pass

        return is_crit[0], damage, attack

    #COMMANDS
    @commands.command(aliases=['pvp'], brief='<player>', description='Challenge another player to battle you!')
    @commands.check(Checks.is_player)
    @cooldown(1, 30, BucketType.user)
    async def battle(self, ctx, opponent : commands.MemberConverter):
        #Make sure target is a player
        if not await Checks.has_char(self.client.pg_con, opponent):
            await ctx.reply('This person does not have a character')
            ctx.command.reset_cooldown(ctx)
            return

        if opponent.id == ctx.author.id:
            await ctx.reply('Amogus.')
            ctx.command.reset_cooldown(ctx)
            return

        #Ping and challenge opponent to battle
        message = await ctx.reply(f'{opponent.mention}, {ctx.author.mention} is challenging you to a battle!')
        await message.add_reaction('\u2705') #Check
        await message.add_reaction('\u274E') #X

        def check(reaction, user):
            return user == opponent

        reaction = None
        readReactions = True
        while readReactions: 
            if str(reaction) == '\u2705': #Then exchange stuff
                await message.delete()
                break
            if str(reaction) == '\u274E':
                await message.delete()
                await ctx.reply('They declined your challenge.')
                ctx.command.reset_cooldown(ctx)
                return

            try:
                reaction, user = await self.client.wait_for('reaction_add', check=check, timeout=15.0)
                await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                readReactions = not readReactions
                await message.delete()
                await ctx.reply('They did not respond to your challenge.')
                ctx.command.reset_cooldown(ctx)
                return

        #Load each player's stats and strategy
        player1 = {}
        player1['ID'] = ctx.author.id
        player1['Attack'], player1['Crit'], player1['HP'], player1['Role'], player1['Acolyte1'], player1['Acolyte2'] = await AssetCreation.getAttack(self.client.pg_con, ctx.author.id, returnothers=True)
        player1['Strategy'] = await AssetCreation.getStrategy(self.client.pg_con, ctx.author.id)

        player2 = {}
        player2['ID'] = opponent.id
        player2['Attack'], player2['Crit'], player2['HP'], player2['Role'], player2['Acolyte1'], player2['Acolyte2'] = await AssetCreation.getAttack(self.client.pg_con, opponent.id, returnothers=True)
        player2['Strategy'] = await AssetCreation.getStrategy(self.client.pg_con, opponent.id)

        if player1['Acolyte1'] is not None:
            player1['Acolyte1'] = await AssetCreation.getAcolyteByID(self.client.pg_con, player1['Acolyte1'])

        if player1['Acolyte2'] is not None:
            player1['Acolyte2'] = await AssetCreation.getAcolyteByID(self.client.pg_con, player1['Acolyte2'])

        if player2['Acolyte1'] is not None:
            player2['Acolyte1'] = await AssetCreation.getAcolyteByID(self.client.pg_con, player2['Acolyte1'])

        if player2['Acolyte2'] is not None:
            player2['Acolyte2'] = await AssetCreation.getAcolyteByID(self.client.pg_con, player2['Acolyte2'])


        #Determine an action; Loop until hp hits 0
        battle_turns = []
        victor = None
        loser = None

        while len(battle_turns) < 50:
            player1_action = self.getAction(player1['Strategy'])
            player2_action = self.getAction(player2['Strategy'])

            #Calculate damage and HP
            player1_dealt, player1_taken = self.calcDamage(player1_action, player1['Attack'])
            player2_dealt, player2_taken = self.calcDamage(player2_action, player2['Attack'])              

            player1_crit, player1_dealt, player1['Attack'] = self.checkCrit(player1['Crit'], player1_dealt, player1['Attack'], player1['Acolyte1'], player1['Acolyte2'])
            player2_crit, player2_dealt, player2['Attack'] = self.checkCrit(player2['Crit'], player2_dealt, player2['Attack'], player2['Acolyte1'], player2['Acolyte2'])

            if player1_crit == 'Crit':
                try:
                    if player1['Acolyte1']['Name'] == 'Ayesha' or player1['Acolyte2']['Name'] == 'Ayesha':
                        player1['HP'] += 35 + int(player1['Attack'] * .3)
                except TypeError:
                    pass
            if player2_crit == 'Crit':
                try:
                    if player2['Acolyte1']['Name'] == 'Ayesha' or player2['Acolyte2']['Name'] == 'Ayesha':
                        player2['HP'] += 35 + int(player2['HP'] * .3)
                except TypeError:
                    pass

            player1['HP'] -= int(player2_dealt * player1_taken)
            player2['HP'] -= int(player1_dealt * player2_taken)

            #Output information
            if player1_crit == 'Crit' and player2_crit =='Crit':
                battle_turns.append([len(battle_turns), f'{ctx.author.mention} critically {player1_action}.\n{opponent.mention} critically {player2_action}.'])
            elif player1_crit == 'Crit' and player2_crit == 'Normal':
                battle_turns.append([len(battle_turns), f'{ctx.author.mention} critically {player1_action}.\n{opponent.mention} {player2_action}.'])
            elif player1_crit == 'Normal' and player2_crit == 'Crit':
                battle_turns.append([len(battle_turns), f'{ctx.author.mention} {player1_action}.\n{opponent.mention} critically {player2_action}.'])             
            else:
                battle_turns.append([len(battle_turns), f'{ctx.author.mention} {player1_action}.\n{opponent.mention} {player2_action}.'])

            #Check to see if anyone won
            if player1['HP'] <= 0 and player2['HP'] <= 0: #Then call it a tie
                battle_turns[-1][1] += '**\n\nThe battle ended in a draw!**'
                break

            if player1['HP'] <= 0 or player2['HP'] <= 0:
                if player1['HP'] <= 0:
                    victor = opponent.id
                    loser = ctx.author.id
                    battle_turns[-1][1] += f'**\n\n{opponent.mention} has defeated the challenger!**'
                    break

                if player2['HP'] <= 0:
                    victor = ctx.author.id
                    loser = opponent.id
                    battle_turns[-1][1] += f'**\n\n{ctx.author.mention} has proven their strength!**'
                    break

        if len(battle_turns) >= 50:
            battle_turns.append([len(battle_turns), 'Turn limit reached! The battle was inconclusive.'])

        #Reward winner and output victory
        if victor is None:
            await AssetCreation.declare_pvp_fight(self.client.pg_con, ctx.author.id, opponent.id)
        else:
            await AssetCreation.declare_pvp_winner(self.client.pg_con, victor, loser)

        embed = discord.Embed(title=f'Battle: {ctx.author.display_name} vs. {opponent.display_name}', color=0xBEDCF6)
        embed.add_field(name=f'{ctx.author.display_name}', value=f"ATK: `{player1['Attack']}` | HP: `{player1['HP']}`")
        embed.add_field(name=f'{opponent.display_name}', value=f"ATK: `{player2['Attack']}` | HP: `{player2['HP']}`")
        for turn in battle_turns[-5:]:
            embed.add_field(name=f'Turn {turn[0]}', value=f'{turn[1]}', inline=False)

        await ctx.reply(embed=embed)

def setup(client):
    client.add_cog(PvP(client)) 