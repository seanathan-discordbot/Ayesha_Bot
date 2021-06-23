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
            damage = int(damage * 1.5)

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
            return user == opponent and reaction.message.id == message.id

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

            player1_crit, player1_dealt, player1['Attack'] = self.checkCrit(player1['Crit'], 
                                                                            player1_dealt, 
                                                                            player1['Attack'], 
                                                                            player1['Acolyte1'], 
                                                                            player1['Acolyte2'])
            player2_crit, player2_dealt, player2['Attack'] = self.checkCrit(player2['Crit'], 
                                                                            player2_dealt, 
                                                                            player2['Attack'], 
                                                                            player2['Acolyte1'], 
                                                                            player2['Acolyte2'])

            if player1_crit == 'Crit':
                try:
                    if player1['Acolyte1']['Name'] == 'Ayesha' or player1['Acolyte2']['Name'] == 'Ayesha':
                        player1['HP'] += int(player1['Attack'] * .2)
                except TypeError:
                    pass
            if player2_crit == 'Crit':
                try:
                    if player2['Acolyte1']['Name'] == 'Ayesha' or player2['Acolyte2']['Name'] == 'Ayesha':
                        player2['HP'] += int(player2['Attack'] * .2)
                except TypeError:
                    pass

            player1['HP'] -= int(player2_dealt * player1_taken)
            player2['HP'] -= int(player1_dealt * player2_taken)

            #Add Ajar's Effect
            try:
                if player1['Acolyte1']['Name'] == 'Ajar' or player1['Acolyte2']['Name'] == 'Ajar':
                    player1['Attack'] += 20
                    player1['HP'] -= 50
                if player2['Acolyte1']['Name'] == 'Ajar' or player2['Acolyte2']['Name'] == 'Ajar':
                    player2['Attack'] += 20
                    player2['HP'] -= 50
            except TypeError:
                pass

            if len(battle_turns) == 4: #Add Onion's Effect
                try:
                    if player1['Acolyte1']['Name'] == 'Onion' or player1['Acolyte2']['Name'] == 'Onion':
                        player1['Crit'] *= 2
                    if player2['Acolyte1']['Name'] == 'Onion' or player2['Acolyte2']['Name'] == 'Onion':
                        player2['Crit'] *= 2
                except TypeError:
                    pass    

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

        embed = discord.Embed(title=f'Battle: {ctx.author.display_name} vs. {opponent.display_name}', 
                              color=self.client.ayesha_blue)
        embed.add_field(name=f'{ctx.author.display_name}', 
                        value=f"ATK: `{player1['Attack']}` | HP: `{player1['HP']}`")
        embed.add_field(name=f'{opponent.display_name}', 
                        value=f"ATK: `{player2['Attack']}` | HP: `{player2['HP']}`")
        for turn in battle_turns[-5:]:
            embed.add_field(name=f'Turn {turn[0]}', value=f'{turn[1]}', inline=False)

        await ctx.reply(embed=embed)

    @commands.command(brief='<reward money : int>', 
                      description='Start a single-elimination PvP tournament between 2 or more players!')
    @commands.check(Checks.is_player)
    @cooldown(1, 300, type=BucketType.user)
    async def tournament(self, ctx, reward : int = 0):
        async def get_player_info(user_id : int):
            """Returns a dict containing a player's ID, name, ATK, and Crit."""
            player = {}
            player['ID'] = user_id
            player['Name'] = await AssetCreation.getPlayerName(self.client.pg_con, user_id)
            player['ATK'], player['Crit'] = await AssetCreation.getAttack(self.client.pg_con, user_id)

            return player

        async def deny_repeats(players : list, user):
            """Return True if player does not have a character or is already in tournament."""
            if not await Checks.has_char(self.client.pg_con, user):
                return True

            player_ids = [player['ID'] for player in players]
            if user.id in player_ids:
                return True

        def match_players(players : list):
            """Matches the players in the inputted list.
            Returns a list of tuples, each tuple holding the info for 2 players.
            If there are an odd amount of players, the remainder gets matched against a fake with no stats.
            """
            matches = []
            i = 0
            while i < len(players):
                try:
                    match = (
                        players[i],
                        players[i+1]
                    )
                except IndexError: #In case there are an odd amount of players
                    fake_player = {
                        'Name' : 'another contestant',
                        'ATK' : 0,
                        'Crit' : 0
                    }
                    match = (
                        players[i],
                        fake_player
                    )
                finally:
                    matches.append(match)
                    i+=2 #Skip over every other player since matches have 2 people
                    
            return matches

        def simulate_battle(player1, player2):
            """Simulate a battle between two players based solely off ATK and Crit.
            Each side has a small chance to land a "crit" (based off crit) and win.
            Otherwise it will base the victor off the proportions of the attack.
            Return the winner and loser in that order."""
            #See if one side lands a critical hit - Highest crit possible is theoretically ~70%.
            p1vict = player1['Crit']
            p2vict = p1vict + player2['Crit'] #This should theoretically be <=140
            random_crit = random.randint(0,500)
            if random_crit < p1vict:
                return player1, player2 #player1 wins; Winner is returned first
            elif random_crit < p2vict:
                return player2, player1
            
            #If no victory occurs, then base it off proportion of ATK
            victory_number = random.randint(0, player1['ATK'] + player2['ATK'])
            if victory_number < player1['ATK']:
                return player1, player2
            else:
                return player2, player1

        #Check for valid input
        if reward < 0:
            return await ctx.reply('Tournaments should be free to win!')

        player_gold = await AssetCreation.getGold(self.client.pg_con, ctx.author.id)
        if reward > player_gold:
            return await ctx.reply('You do not have enough gold to post that as a reward')

        await AssetCreation.giveGold(self.client.pg_con, reward * -1, ctx.author.id)

        #Send message allowing people to join by hitting a reaction
        #When joining, check for valid player and load their stats, strategy
        #Store all players in a list
        players = [await get_player_info(ctx.author.id)]

        join_message = await ctx.reply(f'{ctx.author.mention} is hosting a tournament! The prize is `{reward}` gold!\n Hit the \N{CROSSED SWORDS} to join!')
        await join_message.add_reaction('\N{CROSSED SWORDS}')

        reaction = None
        while True:
            if str(reaction) == '\N{CROSSED SWORDS}':
                if not await deny_repeats(players, user):
                    players.append(await get_player_info(user.id))
                    await ctx.send(f'{user.display_name} joined {ctx.author.display_name}\'s tournament.')

            try:
                reaction, user = await self.client.wait_for('reaction_add', timeout=10.0)
            except asyncio.TimeoutError:
                await join_message.delete()
                break
        
        #Enumerate and iterate over list, matching consecutive players and popping the loser.
        #Continue tournament while len(list) > 1. Inside put a for-loop
        #that goes over each player. In case off odd number of players, add byes with try statement
        await ctx.send(f'Tournament hosted by {ctx.author.mention} starting with {len(players)} participants!')

        roundnum = 1
        while len(players) > 1:
            await ctx.send(f'__**Round {roundnum}**__')
            matches = match_players(players)
            for match in matches:
                #Send the battle message
                temp_msg = await ctx.send(f"**{match[0]['Name']}** vs. **{match[1]['Name']}**")
    
                #Simulate a battle between the two participants
                await asyncio.sleep(2)
                winner, loser = simulate_battle(match[0], match[1])

                #Send result and eliminate loser from the list
                verbs = ['defeated','vanquished','knocked out','eliminated','sussy-amogused',]
                await temp_msg.edit(content=f"**{winner['Name']}** has {random.choices(verbs, [5,5,5,5,1])[0]} **{loser['Name']}**!")
                try:
                    players.remove(loser)
                except ValueError: #Occurs when the fake participant loses.
                    pass
                await asyncio.sleep(3)
            roundnum+=1

        victor = players[0]['Name']
        #Declare winner and give them reward
        await AssetCreation.giveGold(self.client.pg_con, reward, players[0]['ID'])
        await ctx.send(f'**{victor}** won the tournament hosted by {ctx.author.mention}!')

def setup(client):
    client.add_cog(PvP(client)) 