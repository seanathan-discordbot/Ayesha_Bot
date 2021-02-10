import discord
import asyncio

from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

from Utilities import Checks, AssetCreation, PageSourceMaker, Links

import random
import math

# List Level, Name, LowAtk, HighAtk, LowHP, HighHP, Special Abilities (if any)
bounty_levels = {
    1 : {
        'Name' : 'Bortoise',
        'LowATK' : 0,
        'HighATK' : 0,
        'LowHP' : 1,
        'HighHP' : 1,
        'Effect' : None,
        'Image' : "https://i.imgur.com/C8inYxx.png"
    },
    2 : {
        'Name' : 'Tavern Drunkard',
        'LowATK' : 30,
        'HighATK' : 50,
        'LowHP' : 50,
        'HighHP' : 100,
        'Effect' : None,
        'Image' : None
    },
    3 : {
        'Name' : 'Thief',
        'LowATK' : 80,
        'HighATK' : 100,
        'LowHP' : 50,
        'HighHP' : 100,
        'Effect' : None,
        'Image' : None
    },
    4 : {
        'Name' : 'Wild Boar',
        'LowATK' : 120,
        'HighATK' : 150,
        'LowHP' : 200,
        'HighHP' : 250,
        'Effect' : None,
        'Image' : 'https://i.imgur.com/I1V9GAQ.png'
    },
    5 : { 
        'Name' : 'Sean', #SPECIAL: 50% INCREASED ATTACK
        'LowATK' : 5,
        'HighATK' : 10,
        'LowHP' : 500,
        'HighHP' : 500,
        'Effect' : 'Players gain 50% attack when fighting this boss.',
        'Image' : None
    },
    6 : {
        'Name' : 'Roadside Brigands',
        'LowATK' : 110,
        'HighATK' : 150,
        'LowHP' : 800,
        'HighHP' : 900,
        'Effect' : None,
        'Image' : None
    },
    7 : {
        'Name' : 'Verricosus',
        'LowATK' : 130,
        'HighATK' : 160,
        'LowHP' : 900,
        'HighHP' : 1000,
        'Effect' : None,
        'Image' : None
    },
    8 : {
        'Name' : 'Eques Maledicens',
        'LowATK' : 150,
        'HighATK' : 175,
        'LowHP' : 900,
        'HighHP' : 1000,
        'Effect' : None,
        'Image' : None
    },
    9 : {
        'Name' : 'Rabid Bear',
        'LowATK' : 300,
        'HighATK' : 350,
        'LowHP' : 400,
        'HighHP' : 500,
        'Effect' : None,
        'Image' : 'https://i.imgur.com/aW7gAqZ.png'
    },
    10 : {
        'Name' : 'Maritimialan Shaman', #SPECIAL: ATTACK REDUCED BY 20%
        'LowATK' : 190,
        'HighATK' : 225,
        'LowHP' : 750,
        'HighHP' : 1000,
        'Effect' : 'Players have 20% reduced attack when fighting this boss.',
        'Image' : None
    },
    11 : {
        'Name' : 'Apprenticeship Loan Debt Collector',
        'LowATK' : 200,
        'HighATK' : 250,
        'LowHP' : 1100,
        'HighHP' : 1250,
        'Effect' : None,
        'Image' : None
    },
    12 : {
        'Name' : 'Maritimialan Blood Warrior',
        'LowATK' : 300,
        'HighATK' : 400,
        'LowHP' : 700,
        'HighHP' : 900,
        'Effect' : None,
        'Image' : None
    },
    13 : {
        'Name' : 'Moonlight Wolf Pack', #SPECIAL: NO HEALING
        'LowATK' : 250,
        'HighATK' : 275,
        'LowHP' : 1500,
        'HighHP' : 1650,
        'Effect' : 'Players cannot heal when fighting this boss.',
        'Image' : 'https://i.imgur.com/epRUIYs.jpg'
    },
    14 : {
        'Name' : 'Cursed Huntress', #SPECIAL: CANNOT BE BLOCKED
        'LowATK' : 320,
        'HighATK' : 340,
        'LowHP' : 900,
        'HighHP' : 1100,
        'Effect' : 'Players cannot block Cursed Huntress\' attacks.',
        'Image' : None
    },
    15 : {
        'Name' : 'Crumidian Warriors', 
        'LowATK' : 280,
        'HighATK' : 300,
        'LowHP' : 1300,
        'HighHP' : 1500,
        'Effect' : None,
        'Image' : None
    },
    16 : {
        'Name' : 'Naysayers of the Larry Almighty', #SPECIAL: -80% DAMAGE TAKEN IF PARRYING
        'LowATK' : 450,
        'HighATK' : 700,
        'LowHP' : 1300,
        'HighHP' : 1350,
        'Effect' : 'Players take 80% reduced damage instead of 50% when parrying this boss\' attacks.',
        'Image' : None
    },
    17 : {
        'Name' : 'John', 
        'LowATK' : 295,
        'HighATK' : 310,
        'LowHP' : 1200,
        'HighHP' : 1400,
        'Effect' : None,
        'Image' : 'https://i.imgur.com/XFIlLi0.png'
    },
    18 : {
        'Name' : 'Osprey Imperial Assassin', 
        'LowATK' : 305,
        'HighATK' : 325,
        'LowHP' : 1300,
        'HighHP' : 1450,
        'Effect' : None,
        'Image' : None
    },
    19 : {
        'Name' : 'Arquitenio', #SPECIAL: ATTACKS EVERY TURN
        'LowATK' : 325,
        'HighATK' : 350,
        'LowHP' : 1400,
        'HighHP' : 1450,
        'Effect' : 'Aruitenio never misses. He attacks every turn.',
        'Image' : None
    },
    20 : {
        'Name' : 'Tomyris', 
        'LowATK' : 340,
        'HighATK' : 360,
        'LowHP' : 1500,
        'HighHP' : 1500,
        'Effect' : None,
        'Image' : None
    },
    21 : {
        'Name' : 'Lucius Porcius Magnus Dux', #SPECIAL: ENEMY HEALS 50 HP INSTEAD OF TAKING DAMAGE IF CRIT
        'LowATK' : 360,
        'HighATK' : 375,
        'LowHP' : 1400,
        'HighHP' : 1600,
        'Effect' : 'L. Porcius Magnus heals 50 HP instead of taking damage when struck by a critical strike.',
        'Image' : None
    },
    22 : {
        'Name' : 'Laidirix', #SPECIAL: REFLECTS 5% OF DAMAGE TAKEN
        'LowATK' : 375,
        'HighATK' : 395,
        'LowHP' : 1500,
        'HighHP' : 2000,
        'Effect' : 'Laidirix reflects 5% of all damage taken.',
        'Image' : None
    },
    23 : {
        'Name' : 'Sanguirix', #SPECIAL: DOUBLE ATTACK AT TURN 0
        'LowATK' : 400,
        'HighATK' : 420,
        'LowHP' : 1750,
        'HighHP' : 2000,
        'Effect' : 'Sanguirix attacks twice at the beginning of the fight if you damage him.',
        'Image' : None
    },
    24 : {
        'Name' : 'Supreme Duck', 
        'LowATK' : 480,
        'HighATK' : 550,
        'LowHP' : 2300,
        'HighHP' : 2500,
        'Effect' : None,
        'Image' : 'https://i.imgur.com/hPFZte9.png'
    },
    25 : {
        'Name' : 'Draconicus Rex', #SPECIAL: HEALS 100 HP EVERY TURN
        'LowATK' : 500,
        'HighATK' : 520,
        'LowHP' : 3000,
        'HighHP' : 3000,
        'Effect' : 'The Draconicus Rex heals 100 HP every turn.',
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

    def __init__(self, client):
        self.client = client
        # self.players = {}

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('PvE is ready.')

    def getBossAction(self, level):
        action = {'Action' : None, 'Damage' : None, 'DamageTaken' : 1}
        actiondet = random.randint(1,10)
        
        if level == 19: #Arquitenio effect - always attack
            actiondet = 1

        if actiondet < 7:
            action['Action'] = 'attacked' 
            action['Damage'] = random.randint(bounty_levels[level]['LowATK'], bounty_levels[level]['HighATK'])
        elif actiondet < 9:
            action['Action'] = 'parried'
            action['Damage'] = math.floor(random.randint(bounty_levels[level]['LowATK'], bounty_levels[level]['HighATK']) / 2)
            action['DamageTaken'] = .5
        else:
            action['Action'] = 'blocked'
            action['Damage'] = math.floor(random.randint(bounty_levels[level]['LowATK'], bounty_levels[level]['HighATK']) / 100)
            action['DamageTaken'] = .05
        return action

    async def checkEndGame(self, ctx, message, level, hp, enemyhp, acolyte1, acolyte2):
        if enemyhp <= 0: #give them a win in the event of a tie
            vict, acolyte1, acolyte2 = await self.doVictory(ctx.author.id, level, hp, acolyte1, acolyte2)
            await message.edit(embed=vict)
            await AssetCreation.checkLevel(self.client.pg_con, ctx, ctx.author.id, aco1=acolyte1, aco2=acolyte2)
            return True
        elif hp <= 0: #loss
            loss, acolyte1, acolyte2 = await self.doDefeat(ctx.author.id, level, enemyhp, acolyte1, acolyte2)
            await message.edit(embed=loss)
            await AssetCreation.checkLevel(self.client.pg_con, ctx, ctx.author.id, aco1=acolyte1, aco2=acolyte2)
            return True
        else:
            return None

    async def doVictory(self, player, level, hp, acolyte1, acolyte2):
        getweapon = False
        #Calculate chance of receiving a weapon: 25%
        if random.randint(1,4) == 1:
            if level <= 8:
                attack = random.randint(15, 40)
                rarity = 'Common'
                await AssetCreation.createItem(self.client.pg_con, player, attack, rarity)
            elif level <= 16:
                attack = random.randint(30, 70)
                rarity = 'Uncommon'
                await AssetCreation.createItem(self.client.pg_con, player, attack, rarity)
            elif level <= 24:
                attack = random.randint(45, 100)
                rarity = 'Rare'
                await AssetCreation.createItem(self.client.pg_con, player, attack, rarity)
            else:
                attack = random.randint(75, 120)
                rarity = 'Epic'
                await AssetCreation.createItem(self.client.pg_con, player, attack, rarity)
            
            getweapon = not getweapon
        #Calculate gold, xp, acolyte xp rewards
        if hp < 1:
            hp = 1
        gold = random.randint(gold_rewards[level]['Min'], gold_rewards[level]['Max'])
        xp = math.floor(2**(level/10) * ((level+10)**2) * ((hp/1250) + .2))
        try:
            if acolyte1['Name'] == 'Sean' or acolyte2['Name'] == 'Sean':
                xp = math.floor(xp * 1.1)
        except TypeError:
            pass
        acolyte_xp = math.ceil(xp / 10)
        #Give rewards
        acolyte1, acolyte2 = await AssetCreation.getAcolyteFromPlayer(self.client.pg_con, player)
        if acolyte1 is not None:
            await AssetCreation.giveAcolyteXP(self.client.pg_con, acolyte_xp, acolyte1)
        if acolyte2 is not None:
            await AssetCreation.giveAcolyteXP(self.client.pg_con, acolyte_xp, acolyte2)
        await AssetCreation.giveBountyRewards(self.client.pg_con, player, gold, xp, victory=True)

        #Return an embed to send
        embed = discord.Embed(title=f"You defeated {bounty_levels[level]['Name']}!", color=0xBEDCF6)
        embed.set_thumbnail(url='https://i.imgur.com/MCAMH45.jpg')
        if getweapon:
            embed.add_field(name=f'You had {hp} hp remaining', value=f'You received {gold} gold and {xp} xp from the battle.\nYou also gained an item. Check your `inventory` to see it!')
        else:
            embed.add_field(name=f'You had {hp} hp remaining', value=f'You received {gold} gold and {xp} xp from the battle.')

        if acolyte1 is not None and acolyte2 is not None:
            return embed, acolyte1, acolyte2
        elif acolyte1 is not None and acolyte2 is None:
            return embed, acolyte1, None
        elif acolyte1 is None and acolyte2 is not None:
            return embed, acolyte1, acolyte2
        else:
            return embed, None, None

    async def doDefeat(self, player, level, enemyhp, acolyte1, acolyte2):
        #Calculate xp, acolyte xp rewards: xp greatly reduced
        xp = 5 * level + 20
        try:
            if acolyte1['Name'] == 'Sean' or acolyte2['Name'] == 'Sean':
                xp = math.floor(xp * 1.1)
        except TypeError:
            pass
        acolyte_xp = math.ceil(xp / 10)
        gold = 0

        acolyte1, acolyte2 = await AssetCreation.getAcolyteFromPlayer(self.client.pg_con, player)
        if acolyte1 is not None:
            await AssetCreation.giveAcolyteXP(self.client.pg_con, acolyte_xp, acolyte1)
        if acolyte2 is not None:
            await AssetCreation.giveAcolyteXP(self.client.pg_con, acolyte_xp, acolyte2)
        await AssetCreation.giveBountyRewards(self.client.pg_con, player, gold, xp, victory=False)

        #Return an embed to send
        embed = discord.Embed(title=f"The {bounty_levels[level]['Name']} has shown its superiority", color=0xBEDCF6)
        embed.add_field(name='You fled the battlefield', value=f'Boss HP: `{enemyhp}`\nYou received {xp} xp from the battle.')
        # Also returns the acolytes to check their level
        if acolyte1 is not None and acolyte2 is not None:
            return embed, acolyte1, acolyte2
        elif acolyte1 is not None and acolyte2 is None:
            return embed, acolyte1, None
        elif acolyte1 is None and acolyte2 is not None:
            return embed, acolyte1, acolyte2
        else:
            return embed, None, None

    def checkCrit(self, level, crit, damage, enemyhp, attack, acolyte1, acolyte2):
        is_crit = random.choices(['Normal', 'Crit'], [100-crit, crit])
        if is_crit[0] == 'Crit':
            if level == 21: #Magnus special prevents crits
                damage = 0
                enemyhp += 50
            else:
                damage = damage * 2

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

        return crit, is_crit[0], damage, enemyhp, attack

    def showBounties(self):
        embeds = []
        for i in range(1,26):
            embed = discord.Embed(title=f"Level {i}: {bounty_levels[i]['Name']}", color=0xBEDCF6)
            embed.add_field(name='Attack Range', value=f"{bounty_levels[i]['LowATK']} - {bounty_levels[i]['HighATK']}")
            embed.add_field(name='HP Range', value=f"{bounty_levels[i]['LowHP']} - {bounty_levels[i]['HighHP']}")
            if bounty_levels[i]['Effect'] is not None:
                embed.add_field(name='Special Effect', value=f"{bounty_levels[i]['Effect']}", inline=False)
            embeds.append(embed)
        return embeds

    #COMMANDS
    @commands.command(aliases=['pve', 'fight', 'boss'], brief='<level>', description='Fight an enemy for rewards!')
    @commands.check(Checks.is_player)
    @cooldown(1, 10, type=BucketType.user)
    @commands.max_concurrency(1, per=BucketType.user, wait=False)
    async def bounty(self, ctx, level : int = 0):
        if level == 0:
            levels = self.showBounties()
            pages = menus.MenuPages(source=PageSourceMaker.PageMaker(levels), clear_reactions_after=True, delete_message_after=True)
            await pages.start(ctx)
            #Show the list of enemies
            ctx.command.reset_cooldown(ctx)
            return
        if level < 1 or level > 25:
            await ctx.reply('Please supply a valid level.')
            ctx.command.reset_cooldown(ctx)
            return
        #Get the player's info and load stats
        attack, crit, hp, playerjob, acolyte1, acolyte2 = await AssetCreation.getAttack(self.client.pg_con, ctx.author.id, returnothers=True)
        if acolyte1 is not None:
            acolyte1 = await AssetCreation.getAcolyteByID(self.client.pg_con, acolyte1)
        if acolyte2 is not None:
            acolyte2 = await AssetCreation.getAcolyteByID(self.client.pg_con, acolyte2)
        
        if level == 5: #Sean
            attack = math.floor(attack * 1.5)
        if level == 10: #Maritimialian Shaman
            attack = math.floor(attack * (4/5))
        enemyhp = random.randint(bounty_levels[level]['LowHP'], bounty_levels[level]['HighHP'])

        strategy = await AssetCreation.getStrategy(self.client.pg_con, ctx.author.id)

        # Create the embed
        embed = discord.Embed(title=f"{bounty_levels[level]['Name']} attacks!", color=0xBEDCF6)
        embed.add_field(name='Attack', value=f'{attack}') #field 0
        embed.add_field(name='Crit Rate', value=f'{crit}%') #field 1
        embed.add_field(name='HP', value=f'{hp}') #field 2
        embed.add_field(name=f'Enemy HP: `{enemyhp}`', value=f'🗡️ Attack , \N{SHIELD} Block, \N{CROSSED SWORDS} Parry, \u2764 Heal, \u23F1 Bide', inline=False) #field 3
        embed.add_field(name='You get initiative', value='Turn `0`') #field 4
        if bounty_levels[level]['Image'] is not None:
            embed.set_thumbnail(url=bounty_levels[level]['Image'])
        message = await ctx.reply(embed=embed)

        readReactions = True
        turnCounter = 0

        while readReactions:
            reaction = random.randint(1,100)

            if reaction <= strategy['attack']:
                #Do Calcs
                bossaction = self.getBossAction(level)
                damage = math.floor(random.randint(attack, attack+10) * bossaction['DamageTaken'])

                #Critical Strike handling - implement bonuses for having certain acolytes
                crit, is_crit, damage, enemyhp, attack = self.checkCrit(level, crit, damage, enemyhp, attack, acolyte1, acolyte2)

                enemyhp = enemyhp - damage
                if level == 22: #Laidirix reflects damage
                    hp = hp - (bossaction['Damage'] + math.floor(damage / 20))
                else:
                    if level == 23 and turnCounter == 0: #Sanguirix
                        bossaction['Damage'] *= 2
                    hp = hp - bossaction['Damage']
                if level == 25:
                    enemyhp += 100
                turnCounter += 1

                #Check to see if hp falls below 0
                doEnd = await self.checkEndGame(ctx, message, level, hp, enemyhp, acolyte1, acolyte2)
                if doEnd:
                    break

                #Send new embed if game continues
                embed.set_field_at(0, name='Attack', value=f'{attack}')
                embed.set_field_at(2, name='HP', value=f'{hp}')
                embed.set_field_at(3, name=f'Enemy HP: `{enemyhp}`', value=f'🗡️ Attack , \N{SHIELD} Block, \N{CROSSED SWORDS} Parry, \u2764 Heal, \u23F1 Bide', inline=False)
                if is_crit == 'Normal':
                    embed.set_field_at(4, name=f'Turn `{turnCounter}`', value=f"You hit for {damage} damage. {bounty_levels[level]['Name']} {bossaction['Action']} and dealt {bossaction['Damage']} damage.", inline=False)
                else:
                    embed.set_field_at(4, name=f'Turn `{turnCounter}`', value=f"You critically striked for {damage} damage. {bounty_levels[level]['Name']} {bossaction['Action']} and dealt {bossaction['Damage']} damage.", inline=False)
                await message.edit(embed=embed)

            elif reaction <= strategy['attack'] + strategy['block']:
                #Do Calcs
                bossaction = self.getBossAction(level)
                damage = math.floor((random.randint(attack, attack+10)/10) * bossaction['DamageTaken'])

                #Critical Strike handling - implement bonuses for having certain acolytes
                crit, is_crit, damage, enemyhp, attack = self.checkCrit(level, crit, damage, enemyhp, attack, acolyte1, acolyte2)

                enemyhp = enemyhp - damage
                if level == 22: #Laidirix
                    your_damage = math.floor((bossaction['Damage'] / 20) + (damage / 20))
                else:
                    if level == 23 and turnCounter == 0: #Sanguirix
                        bossaction['Damage'] *= 2
                    if level == 14:
                        your_damage = bossaction['Damage']
                    else:
                        your_damage = math.floor(bossaction['Damage'] / 20)
                hp = hp - your_damage
                if level == 25:
                    enemyhp += 100
                turnCounter += 1

                #Check to see if hp falls below 0
                doEnd = await self.checkEndGame(ctx, message, level, hp, enemyhp, acolyte1, acolyte2)
                if doEnd:
                    break

                #Send new embed
                embed.set_field_at(0, name='Attack', value=f'{attack}')
                embed.set_field_at(2, name='HP', value=f'{hp}')
                embed.set_field_at(3, name=f'Enemy HP: `{enemyhp}`', value=f'🗡️ Attack , \N{SHIELD} Block, \N{CROSSED SWORDS} Parry, \u2764 Heal, \u23F1 Bide', inline=False)
                if is_crit == 'Normal':
                    embed.set_field_at(4, name=f'Turn `{turnCounter}`', value=f"You blocked and dealt {damage} damage. {bounty_levels[level]['Name']} {bossaction['Action']} and dealt {your_damage} damage.", inline=False)
                else:
                    embed.set_field_at(4, name=f'Turn `{turnCounter}`', value=f"You critically striked for {damage} damage. {bounty_levels[level]['Name']} {bossaction['Action']} and dealt {your_damage} damage.", inline=False)
                await message.edit(embed=embed)

            elif reaction <= strategy['attack'] + strategy['block'] + strategy['parry']:
                #Do Calcs
                bossaction = self.getBossAction(level)
                damage = math.floor((random.randint(attack, attack+10) * bossaction['DamageTaken'])/2)

                #Critical Strike handling - implement bonuses for having certain acolytes
                crit, is_crit, damage, enemyhp, attack = self.checkCrit(level, crit, damage, enemyhp, attack, acolyte1, acolyte2)

                enemyhp = enemyhp - damage

                #Calculate player damage
                your_damage = bossaction['Damage']
                if level == 22: #Laidirix
                    your_damage = math.floor(bossaction['Damage']/2 + damage/20)
                if level == 23 and turnCounter == 0: #Sanguirix
                    pass
                else:
                    your_damage = math.floor(bossaction['Damage']/2)
                if level == 16:
                    your_damage = math.floor(your_damage / 5)
                hp = hp - your_damage

                if level == 25:
                    enemyhp += 100
                turnCounter += 1

                #Check to see if hp falls below 0
                doEnd = await self.checkEndGame(ctx, message, level, hp, enemyhp, acolyte1, acolyte2)
                if doEnd:
                    break

                #Send new embed
                embed.set_field_at(0, name='Attack', value=f'{attack}')
                embed.set_field_at(2, name='HP', value=f'{hp}')
                embed.set_field_at(3, name=f'Enemy HP: `{enemyhp}`', value=f'🗡️ Attack , \N{SHIELD} Block, \N{CROSSED SWORDS} Parry, \u2764 Heal, \u23F1 Bide', inline=False)
                if is_crit == 'Normal':
                    embed.set_field_at(4, name=f'Turn `{turnCounter}`', value=f"You parried for {damage} damage. {bounty_levels[level]['Name']} {bossaction['Action']} and dealt {your_damage} damage.", inline=False)
                else:
                    embed.set_field_at(4, name=f'Turn `{turnCounter}`', value=f"You critically striked for {damage} damage. {bounty_levels[level]['Name']} {bossaction['Action']} and dealt {your_damage} damage.", inline=False)
                await message.edit(embed=embed)

            elif reaction <= strategy['attack'] + strategy['block'] + strategy['parry'] + strategy['heal']:
                bossaction = self.getBossAction(level)
                hp = hp - bossaction['Damage']
                heal = math.floor((1500 - hp) / 8)
                if playerjob == 'Butcher':
                    heal = heal * 2
                if level == 13: #Moonlight Wolf Pack
                    heal = 0
                hp = hp + heal
                if level == 25:
                    enemyhp += 100
                turnCounter += 1

                #Check to see if hp falls below 0
                doEnd = await self.checkEndGame(ctx, message, level, hp, enemyhp, acolyte1, acolyte2)
                if doEnd:
                    break

                #Send new embed
                embed.set_field_at(0, name='Attack', value=f'{attack}')
                embed.set_field_at(2, name='HP', value=f'{hp}')
                embed.set_field_at(3, name=f'Enemy HP: `{enemyhp}`', value=f'🗡️ Attack , \N{SHIELD} Block, \N{CROSSED SWORDS} Parry, \u2764 Heal, \u23F1 Bide', inline=False)
                embed.set_field_at(4, name=f'Turn `{turnCounter}`', value=f"You healed {heal} hp. {bounty_levels[level]['Name']} {bossaction['Action']} and dealt {bossaction['Damage']} damage.", inline=False)
                await message.edit(embed=embed)

            else:
                #Do Calcs
                bossaction = self.getBossAction(level)
                your_damage = math.floor(bossaction['Damage'] * (3/4))
                hp = hp - your_damage
                attack = math.floor(attack * (1.1))
                if level == 25:
                    enemyhp += 100
                turnCounter += 1

                #Check to see if hp falls below 0
                doEnd = await self.checkEndGame(ctx, message, level, hp, enemyhp, acolyte1, acolyte2)
                if doEnd:
                    break

                #Send new embed
                embed.set_field_at(0, name='Attack', value=f'{attack}')
                embed.set_field_at(2, name='HP', value=f'{hp}')
                embed.set_field_at(3, name=f'Enemy HP: `{enemyhp}`', value=f'🗡️ Attack , \N{SHIELD} Block, \N{CROSSED SWORDS} Parry, \u2764 Heal, \u23F1 Bide', inline=False)
                embed.set_field_at(4, name=f'Turn `{turnCounter}`', value=f"You bided your time and boosted your attack. {bounty_levels[level]['Name']} {bossaction['Action']} and dealt {your_damage} damage.", inline=False)
                await message.edit(embed=embed)

            if turnCounter == 51: #50 turn limit
                loss = await self.doDefeat(ctx.author.id, level, enemyhp, acolyte1, acolyte2)
                await message.edit(embed=loss[0])
                break                

            await asyncio.sleep(2.0)

    @commands.command(aliases=['strat', 'st'], brief='<attack> <block> <parry> <heal> <bide>', description='Set the action weighting when fighting bosses. Do this command without any arguments for more info.')
    @commands.check(Checks.is_player)
    async def strategy(self, ctx, attack : int = None, block : int = None, parry : int = None, heal : int = None, bide : int = None):
        #Explain command if nothing input
        if bide is None:
            with open(Links.tutorial, "r") as f:
                tutorial = f.readlines()

            embed1 = discord.Embed(title='Ayesha Tutorial: Strategy', color=0xBEDCF6, description = '```strategy <attack> <block> <parry> <heal> <bide>```')
            embed1.add_field(name='You can customize how you fight bosses with the Strategy Command!', value=f"{tutorial[52]}\n{tutorial[53]}\n{tutorial[54]}\n{tutorial[55]}")

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
        embed = discord.Embed(title='Set New Action Weights', color=0xBEDCF6)
        embed.add_field(name='Here are the chances of you doing each action when fighting a boss:',
            value=f'**Attack:** {attack}%\n**Block:** {block}%\n**Parry:** {parry}%\n**Heal:** {heal}%\n**Bide:** {bide}%')
        await ctx.reply(embed=embed)

def setup(client):
    client.add_cog(PvE(client))