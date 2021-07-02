import discord
import asyncio

from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

from Utilities import Checks, AssetCreation, PageSourceMaker, Links

import random
import math

class PvP(commands.Cog):
    """Challenge your friends to battle!"""

    def __init__(self, client):
        self.client = client

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('PvP is ready.')

    #INVISIBLE

    def calc_damage(self, player, opponent):
        """Randomly choose a player's action for that turn, calculating their damage, damage taken multiplier, and crit success.
        Input and return both players[dict]. Will only calculate action for FIRST player passed.
        """
        if player['Action'] == 'attacked':
            player['Damage'] = random.randint(int(player['Attack']*.9), int(player['Attack']*1.1))
            player = AssetCreation.apply_acolytes_with_damage(player)

            player['Taken'] = 1

            if random.randint(1,100) < player['Crit']:
                player, opponent = self.check_for_crit(player, opponent)

        elif player['Action'] == 'blocked':
            player['Damage'] = random.randint(int(player['Attack'] / 20), int(player['Attack'] / 10))
            player = AssetCreation.apply_acolytes_with_damage(player)

            player['Taken'] = random.randint(0,10) / 100

            if random.randint(1,100) < player['Crit']:
                player, opponent = self.check_for_crit(player, opponent)

        elif player['Action'] == 'parried':
            player['Damage'] = random.randint(int(player['Attack']*.4), int(player['Attack']*.6))
            player = AssetCreation.apply_acolytes_with_damage(player)

            player['Taken'] = random.randint(35, 55) / 100

            if random.randint(1,100) < player['Crit']:
                player, opponent = self.check_for_crit(player, opponent)

        elif player['Action'] == 'healed':
            player['Damage'] = 0
            player = AssetCreation.apply_acolytes_with_damage(player)
            player['Heal'] = random.randint(100,200)

            player['Taken'] = random.randint(65, 90) / 100

        else:
            player['Damage'] = 0
            player = AssetCreation.apply_acolytes_with_damage(player)
            player['Heal'] = random.randint(25,75)
            player['Attack'] = int(player['Attack'] * 1.25)

            player['Taken'] = random.randint(65, 90) / 100

        return player, opponent

    def check_for_crit(self, player, opponent):
        """Calculates crit damage and applies acolyte effects.
        Input and return both players[dict]. Will only calculate action for FIRST player passed.
        """
        player['Action'] = 'critically ' + player['Action']
        player['Damage'] = int(player['Damage'] * 1.5)

        player, opponent = AssetCreation.apply_acolytes_on_crit(player, opponent)

        return player, opponent


    #COMMANDS
    @commands.command(aliases=['pvp'], brief='<player>', description='Challenge another player to battle you!')
    @commands.check(Checks.is_player)
    @cooldown(1, 30, BucketType.user)
    async def battle(self, ctx, opponent : commands.MemberConverter):
        """`opponent`: the person you want to fight

        Challenge another player to battle you.
        """
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
        player1 = await AssetCreation.get_player_battle_info(self.client.pg_con, ctx.author.id)
        player2 = await AssetCreation.get_player_battle_info(self.client.pg_con, opponent.id)

        #Determine an action; Loop until hp hits 0
        battle_turns = []
        victor = None
        loser = None

        while len(battle_turns) < 50:
            player1['Damage'] = 0
            player1['Taken'] = 1
            player1['Heal'] = 0
            player2['Damage'] = 0
            player2['Taken'] = 1
            player2['Heal'] = 0


            player1['Action'] = random.choices(['attacked', 'blocked', 'parried', 'healed', 'bided'],
                                            [player1['Strategy']['attack'],
                                            player1['Strategy']['block'],
                                            player1['Strategy']['parry'],
                                            player1['Strategy']['heal'],
                                            player1['Strategy']['bide']])[0]
            player2['Action'] = random.choices(['attacked', 'blocked', 'parried', 'healed', 'bided'],
                                            [player2['Strategy']['attack'],
                                            player2['Strategy']['block'],
                                            player2['Strategy']['parry'],
                                            player2['Strategy']['heal'],
                                            player2['Strategy']['bide']])[0]

            #Determine action, calculate the damage done
            player1, player2 = self.calc_damage(player1, player2)
            player2, player1 = self.calc_damage(player2, player1)

            if player1['Class'] == 'Butcher':
                player1['Heal'] *= 2  
            if player2['Class'] == 'Butcher':
                player2['Heal'] *= 2  

            p1taken = int(player2['Damage'] * player1['Taken'])
            p2taken = int(player1['Damage'] * player2['Taken'])
            player1['HP'] = int(player1['HP'] + player1['Heal'] - p1taken)
            player2['HP'] = int(player2['HP'] + player2['Heal'] - p2taken)

            if player1['HP'] > player1['Max_HP']:
                player1['HP'] = player1['Max_HP']
            if player2['HP'] > player2['Max_HP']:
                player2['HP'] = player2['Max_HP']

            player1, player2 = AssetCreation.apply_acolytes_on_turn_end(player1, player2, len(battle_turns))

            #Output information

            fmt = f"{ctx.author.mention} {player1['Action']} (Damage: `{p2taken}` | Heal: `{player1['Heal']}`).\n"
            fmt += f"{opponent.mention} {player2['Action']} (Damage: `{p1taken}` | Heal: `{player2['Heal']}`)."

            battle_turns.append([len(battle_turns), fmt])

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
        for turn in battle_turns[-5:]: #Only print last 5 turns to satisfy character restraints
            embed.add_field(name=f'Turn {turn[0]}', value=f'{turn[1]}', inline=False)

        await ctx.reply(embed=embed)

    @commands.command(brief='<reward money : int>', 
                      description='Start a single-elimination PvP tournament between 2 or more players!')
    @commands.check(Checks.is_player)
    @cooldown(1, 300, type=BucketType.user)
    async def tournament(self, ctx, reward : int = 0):
        """`reward`: the amount of gold you want to give to the winner of this tournament.

        Start a single-elimination PvP tournament between 2 or more players!
        """
        async def get_player_info(user_id : int):
            """Returns a dict containing a player's ID, name, Attack, and Crit."""
            player = await AssetCreation.get_attack_crit_hp(self.client.pg_con, user_id)
            player['ID'] = user_id
            player['Name'] = await AssetCreation.getPlayerName(self.client.pg_con, user_id)
            # player['ATK'], player['Crit'] = await AssetCreation.getAttack(self.client.pg_con, user_id)

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
                        'Attack' : 0,
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
            victory_number = random.randint(0, player1['Attack'] + player2['Attack'])
            if victory_number < player1['Attack']:
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
                reaction, user = await self.client.wait_for('reaction_add', timeout=25.0)
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