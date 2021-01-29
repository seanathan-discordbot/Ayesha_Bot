import discord
import asyncio

from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

from Utilities import Checks, AssetCreation, PageSourceMaker

import random
import math

# List Level, Name, LowAtk, HighAtk, LowHP, HighHP, Special Abilities (if any)
bounty_levels = {
    1 : {
        'Name' : 'Tavern Drunkard',
        'LowATK' : 10,
        'HighATK' : 30,
        'LowHP' : 50,
        'HighHP' : 100,
        'Effect' : None,
        'Image' : None
    },
    2 : {
        'Name' : 'Thief',
        'LowATK' : 50,
        'HighATK' : 100,
        'LowHP' : 50,
        'HighHP' : 100,
        'Effect' : None,
        'Image' : None
    },
    3 : {
        'Name' : 'Roadside Brigands',
        'LowATK' : 60,
        'HighATK' : 90,
        'LowHP' : 700,
        'HighHP' : 900,
        'Effect' : None,
        'Image' : None
    },
    4 : {
        'Name' : 'Eques Maledicens',
        'LowATK' : 100,
        'HighATK' : 120,
        'LowHP' : 750,
        'HighHP' : 1000,
        'Effect' : None,
        'Image' : None
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
        'Name' : 'Rabid Bear',
        'LowATK' : 300,
        'HighATK' : 350,
        'LowHP' : 400,
        'HighHP' : 500,
        'Effect' : None,
        'Image' : None
    },
    7 : {
        'Name' : 'Maritimialan Shaman', #SPECIAL: ATTACK REDUCED BY 20%
        'LowATK' : 125,
        'HighATK' : 150,
        'LowHP' : 500,
        'HighHP' : 750,
        'Effect' : 'Players have 20% reduced attack when fighting this boss.',
        'Image' : None
    },
    8 : {
        'Name' : 'Apprenticeship Loan Debt Collector',
        'LowATK' : 150,
        'HighATK' : 160,
        'LowHP' : 800,
        'HighHP' : 1000,
        'Effect' : None,
        'Image' : None
    },
    9 : {
        'Name' : 'Moonlight Wolf Pack', #SPECIAL: NO HEALING
        'LowATK' : 150,
        'HighATK' : 180,
        'LowHP' : 1100,
        'HighHP' : 1500,
        'Effect' : 'Players cannot heal when fighting this boss.',
        'Image' : None
    },
    10 : {
        'Name' : 'Crumidian Warriors', 
        'LowATK' : 180,
        'HighATK' : 200,
        'LowHP' : 1100,
        'HighHP' : 1500,
        'Effect' : None,
        'Image' : None
    },
    11 : {
        'Name' : 'Naysayers of the Larry Almighty', #SPECIAL: -80% DAMAGE TAKEN IF PARRYING
        'LowATK' : 500,
        'HighATK' : 800,
        'LowHP' : 1200,
        'HighHP' : 1300,
        'Effect' : 'Players take 80% reduced damage instead of 50% when parrying this boss\' attacks.',
        'Image' : None
    },
    12 : {
        'Name' : 'Osprey Imperial Assassin', 
        'LowATK' : 200,
        'HighATK' : 225,
        'LowHP' : 1150,
        'HighHP' : 1250,
        'Effect' : None,
        'Image' : None
    },
    13 : {
        'Name' : 'Lucius Porcius Magnus Dux', #SPECIAL: ENEMY HEALS 50 HP INSTEAD OF TAKING DAMAGE IF CRIT
        'LowATK' : 200,
        'HighATK' : 250,
        'LowHP' : 1100,
        'HighHP' : 1300,
        'Effect' : 'L. Porcius Magnus heals 50 HP instead of taking damage when struck by a critical strike.',
        'Image' : None
    },
    14 : {
        'Name' : 'Laidirix', #SPECIAL: REFLECTS 5% OF DAMAGE TAKEN
        'LowATK' : 200,
        'HighATK' : 250,
        'LowHP' : 1500,
        'HighHP' : 2000,
        'Effect' : 'Laidirix reflects 5% of all damage taken.',
        'Image' : None
    },
    15 : {
        'Name' : 'Draconicus Rex', #SPECIAL: HEALS 100 HP EVERY TURN
        'LowATK' : 225,
        'HighATK' : 250,
        'LowHP' : 2500,
        'HighHP' : 2500,
        'Effect' : 'The Draconicus Rex heals 100 HP every turn.',
        'Image' : None
    },
}

#Rewards follow this equation: 400*sin[(x/10)-(3/2)]+425 < y < f(x+2). 
# Max is 15: Re-adjust this function to ensure the max > highest level 

gold_rewards = {
    1 : {'Min' : 30, 'Max' : 52},
    2 : {'Min' : 39, 'Max' : 68},
    3 : {'Min' : 52, 'Max' : 88},
    4 : {'Min' : 68, 'Max' : 111},
    5 : {'Min' : 88, 'Max' : 138},
    6 : {'Min' : 111, 'Max' : 167},
    7 : {'Min' : 138, 'Max' : 199},
    8 : {'Min' : 167, 'Max' : 233},
    9 : {'Min' : 199, 'Max' : 269},
    10 : {'Min' : 233, 'Max' : 306},
    11 : {'Min' : 269, 'Max' : 345},
    12 : {'Min' : 306, 'Max' : 385},
    13 : {'Min' : 345, 'Max' : 425},
    14 : {'Min' : 385, 'Max' : 464},
    15 : {'Min' : 425, 'Max' : 504}
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
            await message.clear_reactions()
            await message.edit(embed=vict)
            await AssetCreation.checkLevel(self.client.pg_con, ctx, ctx.author.id, aco1=acolyte1, aco2=acolyte2)
            return True
        elif hp <= 0: #loss
            loss, acolyte1, acolyte2 = await self.doDefeat(ctx.author.id, level, enemyhp, acolyte1, acolyte2)
            await message.clear_reactions()
            await message.edit(embed=loss)
            await AssetCreation.checkLevel(self.client.pg_con, ctx, ctx.author.id, aco1=acolyte1, aco2=acolyte2)
            return True
        else:
            return None

    async def doVictory(self, player, level, hp, acolyte1, acolyte2):
        getweapon = False
        #Calculate chance of receiving a weapon: 25%
        if random.randint(1,4) == 1:
            if level <= 5:
                attack = random.randint(15, 40)
                rarity = 'Common'
                await AssetCreation.createItem(self.client.pg_con, player, attack, rarity)
            elif level <= 10:
                attack = random.randint(30, 70)
                rarity = 'Uncommon'
                await AssetCreation.createItem(self.client.pg_con, player, attack, rarity)
            else:
                attack = random.randint(45, 100)
                rarity = 'Rare'
                await AssetCreation.createItem(self.client.pg_con, player, attack, rarity)
            getweapon = not getweapon
        #Calculate gold, xp, acolyte xp rewards
        gold = random.randint(gold_rewards[level]['Min'], gold_rewards[level]['Max'])
        xp = math.floor(2**(level/7) * ((level+10)**2) * ((hp/1000) + .5))
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
            if level == 13: #Lvl 13 special prevents crits
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
        for i in range(1,16):
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
    @commands.max_concurrency(1, per=BucketType.user, wait=False)
    async def bounty(self, ctx, level : int = 0):
        if level == 0:
            levels = self.showBounties()
            pages = menus.MenuPages(source=PageSourceMaker.PageMaker(levels), clear_reactions_after=True, delete_message_after=True)
            await pages.start(ctx)
            #Show the list of enemies
            ctx.command.reset_cooldown(ctx)
            return
        if level < 1 or level > 15:
            await ctx.reply('Please supply a valid level.')
            ctx.command.reset_cooldown(ctx)
            return
        #Get the player's info and load stats
        attack, crit, hp, playerjob, acolyte1, acolyte2 = await AssetCreation.getAttack(self.client.pg_con, ctx.author.id, returnothers=True)
        if acolyte1 is not None:
            acolyte1 = await AssetCreation.getAcolyteByID(self.client.pg_con, acolyte1)
        if acolyte2 is not None:
            acolyte2 = await AssetCreation.getAcolyteByID(self.client.pg_con, acolyte2)
        
        if level == 5:
            attack = math.floor(attack * 1.5)
        if level == 7:
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
                if level == 14:
                    hp = hp - (bossaction['Damage'] + math.floor(damage / 20))
                else:
                    hp = hp - bossaction['Damage']
                if level == 15:
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
                if level == 14:
                    your_damage = math.floor((bossaction['Damage'] / 20) + (damage / 20))
                else:
                    your_damage = math.floor(bossaction['Damage'] / 20)
                hp = hp - your_damage
                if level == 15:
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
                if level == 14:
                    your_damage = math.floor(bossaction['Damage']/2 + damage/20)
                your_damage = math.floor(bossaction['Damage']/2)
                if level == 11:
                    your_damage = math.floor(your_damage / 5)
                hp = hp - your_damage
                if level == 15:
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
                if level == 9:
                    heal = 0
                hp = hp + heal
                if level == 15:
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
                if level == 15:
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

    # @bounty.error
    # async def on_bounty_error(self, ctx, error):
    #     #If you guys know how to make this work contact me thanks
    #     if isinstance(error, commands.MaxConcurrencyReached):
    #         pass
    #     elif isinstance(error, commands.CommandOnCooldown):
    #         pass
    #     else: #When the error is Missing Perms but that wont work for some reason
    #         await ctx.reply('The bot is missing permissions here! Make sure the bot can send, edit, and manage messages in this channel.')

    @commands.command(aliases=['strat', 'st'], brief='<attack> <block> <parry> <heal> <bide>', description='Set the action weighting when fighting bosses. Do this command without any arguments for more info.')
    @commands.check(Checks.is_player)
    async def strategy(self, ctx, attack : int = None, block : int = None, parry : int = None, heal : int = None, bide : int = None):
        #Explain command if nothing input
        if bide is None:
            with open(r"F:\OneDrive\Ayesha\Assets\Tutorial.txt", "r") as f:
                tutorial = f.readlines()

            embed1 = discord.Embed(title='Ayesha Tutorial: Strategy', color=0xBEDCF6, description = '```strategy <attack> <block> <parry> <heal> <bide>```')
            embed1.add_field(name='You can customize how you fight bosses with the Strategy Command!', value=f"{tutorial[51]}\n{tutorial[52]}\n{tutorial[53]}\n{tutorial[54]}")

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