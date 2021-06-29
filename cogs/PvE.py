import discord
import asyncio
from discord.asset import Asset

from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

from Utilities import Checks, AssetCreation, PageSourceMaker, Links

import random
import math

# List Level, Name, LowAtk, HighAtk, LowHP, HighHP, Special Abilities (if any)
bounty_levels = {
    1 : {
        'ID' : None,
        'Name' : 'Bortoise',
        'Attack' : 1,
        'HP' : 1,
        'Class' : 'Boss',
        'Acolyte1' : AssetCreation.empty_acolyte_dict(),
        'Acolyte2' : AssetCreation.empty_acolyte_dict(),
        'Effect' : None,
        'Image' : "https://i.imgur.com/C8inYxx.png"
    },
    2 : {
        'ID' : None,
        'Name' : 'Tavern Drunkard',
        'Attack' : 40,
        'HP' : 75,
        'Class' : 'Boss',
        'Acolyte1' : AssetCreation.empty_acolyte_dict(),
        'Acolyte2' : AssetCreation.empty_acolyte_dict(),
        'Effect' : None,
        'Image' : None
    },
    3 : {
        'ID' : None,
        'Name' : 'Thief',
        'Attack' : 90,
        'HP' : 75,
        'Class' : 'Boss',
        'Acolyte1' : AssetCreation.empty_acolyte_dict(),
        'Acolyte2' : AssetCreation.empty_acolyte_dict(),
        'Effect' : None,
        'Image' : None
    },
    4 : {
        'ID' : None,
        'Name' : 'Wild Boar',
        'Attack' : 135,
        'HP' : 225,
        'Class' : 'Boss',
        'Acolyte1' : AssetCreation.empty_acolyte_dict(),
        'Acolyte2' : AssetCreation.empty_acolyte_dict(),
        'Effect' : None,
        'Image' : 'https://i.imgur.com/I1V9GAQ.png'
    },
    5 : {
        'ID' : None,
        'Name' : 'Sean',
        'Attack' : 8,
        'HP' : 500,
        'Class' : 'Boss',
        'Acolyte1' : AssetCreation.empty_acolyte_dict(),
        'Acolyte2' : AssetCreation.empty_acolyte_dict(),
        'Effect' : 'Players gain 50% attack when fighting this boss.', # apply_boss_game_begin
        'Image' : None
    },
    6 : {
        'ID' : None,
        'Name' : 'Roadside Brigands',
        'Attack' : 130,
        'HP' : 950,
        'Class' : 'Boss',
        'Acolyte1' : AssetCreation.empty_acolyte_dict(),
        'Acolyte2' : AssetCreation.empty_acolyte_dict(),
        'Effect' : None,
        'Image' : None
    },
    7 : {
        'ID' : None,
        'Name' : 'Verricosus',
        'Attack' : 145,
        'HP' : 950,
        'Class' : 'Boss',
        'Acolyte1' : AssetCreation.empty_acolyte_dict(),
        'Acolyte2' : AssetCreation.empty_acolyte_dict(),
        'Effect' : None,
        'Image' : None
    },
    8 : {
        'ID' : None,
        'Name' : 'Corrupt Knight',
        'Attack' : 162,
        'HP' : 950,
        'Class' : 'Boss',
        'Acolyte1' : AssetCreation.empty_acolyte_dict(),
        'Acolyte2' : AssetCreation.empty_acolyte_dict(),
        'Effect' : None,
        'Image' : None
    },
    9 : {
        'ID' : None,
        'Name' : 'Rabid Bear',
        'Attack' : 325,
        'HP' : 450,
        'Class' : 'Boss',
        'Acolyte1' : AssetCreation.empty_acolyte_dict(),
        'Acolyte2' : AssetCreation.empty_acolyte_dict(),
        'Effect' : None,
        'Image' : 'https://i.imgur.com/aW7gAqZ.png'
    },
    10 : {
        'ID' : None,
        'Name' : 'Maritimialan Shaman',
        'Attack' : 210,
        'HP' : 875,
        'Class' : 'Boss',
        'Acolyte1' : AssetCreation.empty_acolyte_dict(),
        'Acolyte2' : AssetCreation.empty_acolyte_dict(),
        'Effect' : 'Players have 20% reduced attack when fighting this boss.', #apply_boss_game_begin
        'Image' : None
    },
    11 : {
        'ID' : None,
        'Name' : 'Apprenticeship Loan Debt Collector',
        'Attack' : 225,
        'HP' : 1175,
        'Class' : 'Boss',
        'Acolyte1' : AssetCreation.empty_acolyte_dict(),
        'Acolyte2' : AssetCreation.empty_acolyte_dict(),
        'Effect' : None,
        'Image' : None
    },
    12 : {
        'ID' : None,
        'Name' : 'Maritimialan Blood Oathsworn',
        'Attack' : 350,
        'HP' : 800,
        'Class' : 'Boss',
        'Acolyte1' : AssetCreation.empty_acolyte_dict(),
        'Acolyte2' : AssetCreation.empty_acolyte_dict(),
        'Effect' : None,
        'Image' : None
    },
    13 : {
        'ID' : None,
        'Name' : 'Moonlight Wolf Pack',
        'Attack' : 262,
        'HP' : 1575,
        'Class' : 'Boss',
        'Acolyte1' : AssetCreation.empty_acolyte_dict(),
        'Acolyte2' : AssetCreation.empty_acolyte_dict(),
        'Effect' : 'Players cannot heal when fighting this boss.', # apply_boss_turn_end
        'Image' : 'https://i.imgur.com/epRUIYs.jpg'
    },
    14 : {
        'ID' : None,
        'Name' : 'Cursed Huntress',
        'Attack' : 330,
        'HP' : 1000,
        'Class' : 'Boss',
        'Acolyte1' : AssetCreation.empty_acolyte_dict(),
        'Acolyte2' : AssetCreation.empty_acolyte_dict(),
        'Effect' : 'Players cannot block Cursed Huntress\' attacks.', # apply_boss_turn_end
        'Image' : None
    },
    15 : {
        'ID' : None,
        'Name' : 'Crumidian Warriors',
        'Attack' : 290,
        'HP' : 1400,
        'Class' : 'Boss',
        'Acolyte1' : AssetCreation.empty_acolyte_dict(),
        'Acolyte2' : AssetCreation.empty_acolyte_dict(),
        'Effect' : None,
        'Image' : None
    },
    16 : {
        'ID' : None,
        'Name' : 'Naysayers of the Larry Almighty',
        'Attack' : 575,
        'HP' : 1375,
        'Class' : 'Boss',
        'Acolyte1' : AssetCreation.empty_acolyte_dict(),
        'Acolyte2' : AssetCreation.empty_acolyte_dict(),
        'Effect' : 'Players take 75% reduced damage instead of 45% when parrying this boss\' attacks.', #apply_boss_parry
        'Image' : None
    },
    17 : {
        'ID' : None,
        'Name' : 'John',
        'Attack' : 302,
        'HP' : 1375,
        'Class' : 'Boss',
        'Acolyte1' : AssetCreation.empty_acolyte_dict(),
        'Acolyte2' : AssetCreation.empty_acolyte_dict(),
        'Effect' : None,
        'Image' : 'https://i.imgur.com/XFIlLi0.png'
    },
    18 : {
        'ID' : None,
        'Name' : 'Osprey Imperial Assassin',
        'Attack' : 310,
        'HP' : 1500,
        'Class' : 'Boss',
        'Acolyte1' : AssetCreation.empty_acolyte_dict(),
        'Acolyte2' : AssetCreation.empty_acolyte_dict(),
        'Effect' : None,
        'Image' : None
    },
    19 : {
        'ID' : None,
        'Name' : 'Arquitenio',
        'Attack' : 337,
        'HP' : 1525,
        'Class' : 'Boss',
        'Acolyte1' : AssetCreation.empty_acolyte_dict(),
        'Acolyte2' : AssetCreation.empty_acolyte_dict(),
        'Effect' : None,
        'Image' : None
    },
    20 : {
        'ID' : None,
        'Name' : 'Tomyris',
        'Attack' : 350,
        'HP' : 1750,
        'Class' : 'Boss',
        'Acolyte1' : AssetCreation.empty_acolyte_dict(),
        'Acolyte2' : AssetCreation.empty_acolyte_dict(),
        'Effect' : None,
        'Image' : None
    },
    21 : {
        'ID' : None,
        'Name' : 'Lucius Porcius Magnus Dux',
        'Attack' : 362,
        'HP' : 2000,
        'Class' : 'Boss',
        'Acolyte1' : AssetCreation.empty_acolyte_dict(),
        'Acolyte2' : AssetCreation.empty_acolyte_dict(),
        'Effect' : 'L. Porcius Magnus heals 50 HP instead of taking damage when struck by a critical strike.', #apply_boss_crit
        'Image' : None
    },
    22 : {
        'ID' : None,
        'Name' : 'Laidirix',
        'Attack' : 385,
        'HP' : 2250,
        'Class' : 'Boss',
        'Acolyte1' : AssetCreation.empty_acolyte_dict(),
        'Acolyte2' : AssetCreation.empty_acolyte_dict(),
        'Effect' : 'Laidirix reflects 5% of all damage taken.', #apply_boss_turn_end
        'Image' : None
    },
    23 : {
        'ID' : None,
        'Name' : 'Sanguirix',
        'Attack' : 440,
        'HP' : 2250,
        'Class' : 'Boss',
        'Acolyte1' : AssetCreation.empty_acolyte_dict(),
        'Acolyte2' : AssetCreation.empty_acolyte_dict(),
        'Effect' : 'Sanguirix attacks twice at the beginning of the fight', #apply_boss_turn_end
        'Image' : None
    },
    24 : {
        'ID' : None,
        'Name' : 'Supreme Ducc',
        'Attack' : 515,
        'HP' : 2950,
        'Class' : 'Boss',
        'Acolyte1' : AssetCreation.empty_acolyte_dict(),
        'Acolyte2' : AssetCreation.empty_acolyte_dict(),
        'Effect' : None,
        'Image' : 'https://i.imgur.com/hPFZte9.png'
    },
    25 : {
        'ID' : None,
        'Name' : 'Draconicus Rex',
        'Attack' : 525,
        'HP' : 4250,
        'Class' : 'Boss',
        'Acolyte1' : AssetCreation.empty_acolyte_dict(),
        'Acolyte2' : AssetCreation.empty_acolyte_dict(),
        'Effect' : 'The Draconicus Rex heals 100 HP every turn.', #apply_boss_turn_end
        'Image' : None
    },
}

#Rewards follow this equation: 800*sin[(x/20)-(3/2)]+825 < y < f(x+2). 
# Max is 30: Re-adjust this function to ensure the max > highest level 

gold_rewards = {
    1 : {'Min' : 30, 'Max' : 44},
    2 : {'Min' : 36, 'Max' : 54},
    3 : {'Min' : 44, 'Max' : 65},
    4 : {'Min' : 54, 'Max' : 79},
    5 : {'Min' : 65, 'Max' : 94},
    6 : {'Min' : 79, 'Max' : 112},
    7 : {'Min' : 94, 'Max' : 131},
    8 : {'Min' : 112, 'Max' : 151},
    9 : {'Min' : 131, 'Max' : 174},
    10 : {'Min' : 151, 'Max' : 198},
    11 : {'Min' : 174, 'Max' : 223},
    12 : {'Min' : 198, 'Max' : 251},
    13 : {'Min' : 223, 'Max' : 279},
    14 : {'Min' : 251, 'Max' : 309},
    15 : {'Min' : 279, 'Max' : 340},
    16 : {'Min' : 309, 'Max' : 373},
    17 : {'Min' : 340, 'Max' : 406},
    18 : {'Min' : 373, 'Max' : 441},
    19 : {'Min' : 406, 'Max' : 477},
    20 : {'Min' : 441, 'Max' : 513},
    21 : {'Min' : 477, 'Max' : 550},
    22 : {'Min' : 513, 'Max' : 588},
    23 : {'Min' : 550, 'Max' : 627},
    24 : {'Min' : 588, 'Max' : 666},
    25 : {'Min' : 627, 'Max' : 705}
}

class PvE(commands.Cog):
    """Basic gameplay in Ayesha"""

    def __init__(self, client):
        self.client = client

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('PvE is ready.')

    #INVISIBLE
    async def send_victory_embed(self, player : dict, boss : dict, bounty_level : int):
        if player['HP'] < 1:
            player['HP'] = 1 #To prevent weird calcs

        rewards = {
            'xp' : int(2**(bounty_level/10) * ((bounty_level+10)**2) * ((player['HP']/1250) + .2)),
            'gold' : random.randint(gold_rewards[bounty_level]['Min'], gold_rewards[bounty_level]['Max']),
            'item' : None
        }
        rewards = AssetCreation.apply_acolytes_game_end(player, rewards, 'pve')

        if random.randint(1,4) == 1:
            rewards['item'] = True

            if bounty_level <= 8:
                attack = random.randint(15, 40)
                rarity = 'Common'
                await AssetCreation.createItem(self.client.pg_con, player['ID'], attack, rarity)
            elif bounty_level <= 16:
                attack = random.randint(30, 70)
                rarity = 'Uncommon'
                await AssetCreation.createItem(self.client.pg_con, player['ID'], attack, rarity)
            elif bounty_level <= 24:
                attack = random.randint(45, 100)
                rarity = 'Rare'
                await AssetCreation.createItem(self.client.pg_con, player['ID'], attack, rarity)
            else:
                attack = random.randint(75, 120)
                rarity = 'Epic'
                await AssetCreation.createItem(self.client.pg_con, player['ID'], attack, rarity)

        if player['Acolyte1']['ID'] is not None:
            await AssetCreation.giveAcolyteXP(self.client.pg_con, int(rewards['xp'] / 10), player['Acolyte1']['ID'])
        if player['Acolyte2']['ID'] is not None:
            await AssetCreation.giveAcolyteXP(self.client.pg_con, int(rewards['xp'] / 10), player['Acolyte2']['ID'])

        await AssetCreation.giveBountyRewards(self.client.pg_con, player['ID'], rewards['gold'], rewards['xp'], victory=True)

        #Return an embed to send.
        embed = discord.Embed(title=f"You defeated {boss['Name']}!", color=self.client.ayesha_blue)
        embed.set_thumbnail(url='https://i.imgur.com/MCAMH45.jpg')
        if rewards['item']:
            embed.add_field(name=f"You had {player['HP']} hp remaining", 
                            value=f"You received `{rewards['gold']}` gold and `{rewards['xp']}` xp from the battle.\nYou also gained an item. Check your `inventory` to see it!")
        else:
            embed.add_field(name=f"You had {player['HP']} hp remaining", 
                            value=f"You received `{rewards['gold']}` gold and `{rewards['xp']}` xp from the battle.")

        return embed

    async def send_loss_embed(self, player : dict, boss : dict, bounty_level : int):
        rewards = {
            'xp' : 5 * bounty_level + 20,
            'gold' : 0,
            'item' : False
        }
        rewards = AssetCreation.apply_acolytes_game_end(player, rewards, 'pve')

        if player['Acolyte1']['ID'] is not None:
            await AssetCreation.giveAcolyteXP(self.client.pg_con, int(rewards['xp'] / 10), player['Acolyte1']['ID'])
        if player['Acolyte2']['ID'] is not None:
            await AssetCreation.giveAcolyteXP(self.client.pg_con, int(rewards['xp'] / 10), player['Acolyte2']['ID'])

        await AssetCreation.giveBountyRewards(self.client.pg_con, player['ID'], rewards['gold'], rewards['xp'], victory=False)

        #Return an embed to send.
        embed = discord.Embed(title=f"The {boss['Name']} has shown its superiority",
                              color=self.client.ayesha_blue)
        embed.add_field(name='You fled the battlefield.',
                        value=f"Boss HP: `{boss['HP']}`\nYou received `{rewards['xp']}` xp from the battle.")
        
        return embed

    def showBounties(self):
        embeds = []
        for i in range(1,26):
            embed = discord.Embed(title=f"Level {i}: {bounty_levels[i]['Name']}", color=self.client.ayesha_blue)
            embed.add_field(name='Attack Stat', 
                            value=f"{bounty_levels[i]['Attack']}")
            embed.add_field(name='HP', 
                            value=f"{bounty_levels[i]['HP']}")
            if bounty_levels[i]['Effect'] is not None:
                embed.add_field(name='Special Effect', 
                                value=f"{bounty_levels[i]['Effect']}", inline=False)

            if bounty_levels[i]['Image'] is not None:
                embed.set_image(url=bounty_levels[i]['Image'])

            embeds.append(embed)
        return embeds

    #COMMANDS
    @commands.command(aliases=['pve', 'fight', 'boss'], brief='<level>', description='Fight an enemy for rewards!')
    @commands.check(Checks.is_player)
    @cooldown(1, 10, type=BucketType.user)
    @commands.max_concurrency(1, per=BucketType.user, wait=False)
    async def bounty(self, ctx, level : int = 0):
        """`level`: the level of the PvE you want to fight. Leave blank to see a menu of bosses.

        Fight an enemy for rewards, gaining xp, gold, and possibly an item.
        """
        if level == 0:
            levels = self.showBounties()
            pages = menus.MenuPages(source=PageSourceMaker.PageMaker(levels), 
                                    clear_reactions_after=True, 
                                    delete_message_after=True)
            await pages.start(ctx)
            #Show the list of enemies
            ctx.command.reset_cooldown(ctx)
            return
        if level < 1 or level > 25:
            await ctx.reply('Please supply a valid level.')
            ctx.command.reset_cooldown(ctx)
            return

        # GET PLAYER INFO AND LOAD THEIR STATS
        player1 = await AssetCreation.get_player_battle_info(self.client.pg_con, ctx.author.id)
        boss = bounty_levels[level].copy()

        # CREATE THE EMBED
        embed = discord.Embed(title=f"{boss['Name']} attacks!",
                              color = self.client.ayesha_blue)
        embed.add_field(name='Attack', value=f"{player1['Attack']}") #field 0
        embed.add_field(name='Crit Rate', value=f"{player1['Crit']}") #field 1
        embed.add_field(name='HP', value=f"{player1['HP']}") #field 2
        embed.add_field(name=f"Enemy HP: `{boss['HP']}`",
                        value=f'🗡️ Attack , \N{SHIELD} Block, \N{CROSSED SWORDS} Parry, \u2764 Heal, \u23F1 Bide',
                        inline=False) #field 3
        embed.add_field(name='You get initiative', value='Turn `0`') #field 4
        if boss['Image'] is not None:
            embed.set_thumbnail(url=boss['Image'])

        message = await ctx.reply(embed=embed)

        # BEGIN THE BATTLE
        turn_counter = 0

        player1, boss = AssetCreation.apply_boss_game_begin(player1, boss)

        while True: #This should be broken eventually and never loop infinitely
            player1['Action'] = random.choices(['attacked', 'blocked', 'parried', 'healed', 'bided'],
                                            [player1['Strategy']['attack'],
                                             player1['Strategy']['block'],
                                             player1['Strategy']['parry'],
                                             player1['Strategy']['heal'],
                                             player1['Strategy']['bide']])[0]
            boss_action = 'attacked'

            #Calculate changes according to the player actions

            player1['Damage'] = 0
            player1['Heal'] = 0
            boss['Damage'] = 0
            boss['Heal'] = 0

            if player1['Action'] == 'attacked':
                player1['Damage'] = random.randint(int(player1['Attack'] * .9), int(player1['Attack'] * 1.1))
                player1 = AssetCreation.apply_acolytes_with_damage(player1)

                boss['Damage'] = random.randint(int(boss['Attack'] * .9), int(boss['Attack'] * 1.1))
                
                if random.randint(1,100) < player1['Crit']:
                    #Calculate damage
                    player1['Action'] = 'critically ' + player1['Action']
                    player1['Damage'] = int(player1['Damage'] * 1.5)
                    
                    #Apply acolyte effects that activate on crit
                    player1, boss = AssetCreation.apply_acolytes_on_crit(player1, boss)
                    player1, boss = AssetCreation.apply_boss_crit(player1, boss)

            elif player1['Action'] == 'blocked':
                player1['Damage'] = random.randint(int(player1['Attack'] / 20), int(player1['Attack'] / 10))
                player1 = AssetCreation.apply_acolytes_with_damage(player1)

                boss['Damage'] = random.randint(0, int(boss['Attack'] / 10))
                
                if random.randint(1,100) < player1['Crit']:
                    #Calculate damage
                    player1['Action'] = 'critically ' + player1['Action']
                    player1['Damage'] = int(player1['Damage'] * 1.5)
                    
                    #Apply acolyte effects that activate on crit
                    player1, boss = AssetCreation.apply_acolytes_on_crit(player1, boss)
                    player1, boss = AssetCreation.apply_boss_crit(player1, boss)

            elif player1['Action'] == 'parried':
                player1['Damage'] = random.randint(int(player1['Attack'] * .4), int(player1['Attack'] * .6))
                player1 = AssetCreation.apply_acolytes_with_damage(player1)

                boss['Damage'] = random.randint(int(boss['Attack'] * .35), int(boss['Attack'] * .55))
                
                if random.randint(1,100) < player1['Crit']:
                    #Calculate damage
                    player1['Action'] = 'critically ' + player1['Action']
                    player1['Damage'] = int(player1['Damage'] * 1.5)
                    
                    #Apply acolyte effects that activate on crit
                    player1, boss = AssetCreation.apply_acolytes_on_crit(player1, boss)
                    player1, boss = AssetCreation.apply_boss_crit(player1, boss)

                player1, boss = AssetCreation.apply_boss_parry(player1, boss)

            elif player1['Action'] == 'healed':
                player1['Damage'] = 0
                player1 = AssetCreation.apply_acolytes_with_damage(player1)
                player1['Heal'] = random.randint(100,200)

                boss['Damage'] = random.randint(int(boss['Attack'] * .65), int(boss['Attack'] * .9))

            else:
                player1['Damage'] = 0
                player1 = AssetCreation.apply_acolytes_with_damage(player1)
                player1['Heal'] = random.randint(25,75)
                player1['Attack'] = int(player1['Attack'] * 1.25)

                boss['Damage'] = random.randint(int(boss['Attack'] * .65), int(boss['Attack'] * .9))

            player1, boss = AssetCreation.apply_acolytes_on_turn_end(player1, boss, turn_counter)
            player1, boss = AssetCreation.apply_boss_turn_end(player1, boss, turn_counter)

            if player1['Class'] == 'Butcher':
                player1['Heal'] *= 2

            #Calculate actual combat changes
            player1['HP'] += player1['Heal'] - boss['Damage']
            boss['HP'] += boss['Heal'] - player1['Damage']

            if player1['HP'] > player1['Max_HP']:
                player1['HP'] = player1['Max_HP']

            #Check to see if HP falls below 0
            if boss['HP'] <= 0: #Give player win in event of a tie
                embed = await self.send_victory_embed(player1, boss, level)
                await message.edit(embed=embed)
                if player1['Acolyte1']['ID'] is None and player1['Acolyte2']['ID'] is None:
                    await AssetCreation.checkLevel(self.client.pg_con, ctx, ctx.author.id)
                elif player1['Acolyte1']['ID'] is not None and player1['Acolyte2']['ID'] is None:
                    await AssetCreation.checkLevel(self.client.pg_con, ctx, ctx.author.id, aco1=player1['Acolyte1']['ID'])
                elif player1['Acolyte1']['ID'] is None and player1['Acolyte2']['ID'] is not None:
                    await AssetCreation.checkLevel(self.client.pg_con, ctx, ctx.author.id, aco2=player1['Acolyte2']['ID'])
                else:
                    await AssetCreation.checkLevel(self.client.pg_con, ctx, ctx.author.id, aco1=player1['Acolyte1']['ID'], aco2=player1['Acolyte2']['ID'])
                return

            elif player1['HP'] <= 0:
                embed = await self.send_loss_embed(player1, boss, level)
                await message.edit(embed=embed)
                if player1['Acolyte1']['ID'] is None and player1['Acolyte2']['ID'] is None:
                    await AssetCreation.checkLevel(self.client.pg_con, ctx, ctx.author.id)
                elif player1['Acolyte1']['ID'] is not None and player1['Acolyte2']['ID'] is None:
                    await AssetCreation.checkLevel(self.client.pg_con, ctx, ctx.author.id, aco1=player1['Acolyte1']['ID'])
                elif player1['Acolyte1']['ID'] is None and player1['Acolyte2']['ID'] is not None:
                    await AssetCreation.checkLevel(self.client.pg_con, ctx, ctx.author.id, aco2=player1['Acolyte2']['ID'])
                else:
                    await AssetCreation.checkLevel(self.client.pg_con, ctx, ctx.author.id, aco1=player1['Acolyte1']['ID'], aco2=player1['Acolyte2']['ID'])
                return

            turn_counter += 1
            if turn_counter >= 51:
                #Return finished embed
                embed = await self.send_loss_embed(player1, boss, level)
                await message.edit(embed=embed)
                break

            #Send new embed
            embed.set_field_at(0, name='Attack', value=f"{player1['Attack']}")
            embed.set_field_at(1, name='Crit Rate', value=f"{player1['Crit']}")
            embed.set_field_at(2, name='HP', value=f"{player1['HP']}")
            embed.set_field_at(3, name=f"Enemy HP: `{boss['HP']}`", 
                               value=f'🗡️ Attack , \N{SHIELD} Block, \N{CROSSED SWORDS} Parry, \u2764 Heal, \u23F1 Bide',
                               inline=False)
            embed.set_field_at(4, name=f"Turn `{turn_counter}`",
                               value=f"You {player1['Action']}, dealing {player1['Damage']} damage and healing {player1['Heal']}.\n{boss['Name']} {boss_action} and dealt {boss['Damage']} damage, healing for {boss['Heal']}.")
            
            await message.edit(embed=embed)

            await asyncio.sleep(2)

    @commands.command(aliases=['strat', 'st'], 
                      brief='<attack> <block> <parry> <heal> <bide>', 
                      description='Set the action weighting when fighting bosses. Do this command without any arguments for more info.')
    @commands.check(Checks.is_player)
    async def strategy(self, ctx, attack : int = None, block : int = None, parry : int = None, heal : int = None, bide : int = None):
        """Set the action weighting when fighting bosses. Do this command without any arguments for more info."""
        #Explain command if nothing input
        if bide is None:
            with open(Links.tutorial, "r") as f:
                tutorial = f.readlines()

            embed1 = discord.Embed(title='Ayesha Tutorial: Strategy', 
                                   color=self.client.ayesha_blue, 
                                   description = '```strategy <attack> <block> <parry> <heal> <bide>```')
            embed1.add_field(name='You can customize how you fight bosses with the Strategy Command!', 
                             value=f"{tutorial[52]}\n{tutorial[53]}\n{tutorial[54]}\n{tutorial[55]}")

            await ctx.reply(embed=embed1)
            return

        #Let them set negatives and zeroes if they don't want to do an action at all
        if attack < 0:
            attack = 0
        if block < 0:
            block = 0
        if parry < 0:
            parry = 0
        if heal < 0:
            heal = 0
        if bide < 0:
            bide = 0

        #Make sure they don't 0 everything, then put everything in a 100 scale
        total = attack + block + parry + heal + bide
        if total <= 0:
            attack = 100
            total = 100

        attack = int(attack / total * 100)
        block = int(block / total * 100)
        parry = int(parry / total * 100)
        heal = int(heal / total * 100)
        bide = int(bide / total * 100)

        while attack + block + parry + heal + bide < 100:
            attack += 1

        #Save this in the database
        await AssetCreation.setStrategy(self.client.pg_con, ctx.author.id, attack, block, parry, heal, bide)

        #Output their new settings
        embed = discord.Embed(title='Set New Action Weights', color=self.client.ayesha_blue)
        embed.add_field(name='Here are the chances of you doing each action when fighting a boss:',
            value=f'**Attack:** {attack}%\n**Block:** {block}%\n**Parry:** {parry}%\n**Heal:** {heal}%\n**Bide:** {bide}%')
        await ctx.reply(embed=embed)

def setup(client):
    client.add_cog(PvE(client))