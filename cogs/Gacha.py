import discord

import json

from Utilities import Checks, AssetCreation, Links
from discord.ext import commands

import asyncpg

import random

#Randomize at bot startup
l=list(range(1,101))
random.shuffle(l)
two_star=l[0:60]
three_star=l[60:95]
four_star=l[95:98]
one_star=[l[98]]
five_star=[l[99]]

class Gacha(commands.Cog):
    def __init__(self,client):
        self.client=client

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('Gacha is ready.')

    #INVISIBLE
    async def doDupe(self, user_id, name):
        is_duplicate = await AssetCreation.checkDuplicate(self.client.pg_con, user_id, name)

        if is_duplicate is not None: #then its a dupe - add 1 to duplicate
            await AssetCreation.addAcolyteDuplicate(self.client.pg_con, is_duplicate['instance_id'])
        else: #Create a new one and add it to tavern
            await AssetCreation.createAcolyte(self.client.pg_con, user_id, name)

    #COMMANDS
    @commands.command(aliases=['summon','gacha'], 
                      brief='<rolls (1-10)>', 
                      description='Spend 1 rubidic to get a random acolyte or weapon!')
    @commands.check(Checks.is_player)
    async def roll(self, ctx, rolls : int = 1):
        #Make sure they have rubidics
        if rolls > 10:
            return await ctx.reply('You can only roll up to 10 times at once!')

        info = await AssetCreation.getRubidics(self.client.pg_con, ctx.author.id)
        if info['rubidic'] < rolls:
            return await ctx.reply(f"You don\'t have enough rubidics to summon. Do `{ctx.prefix}daily` or level up to get some!")

        #Load the list of acolytes
        with open(Links.acolyte_list) as f:
            acolyte_list=json.load(f) #This stores all the acolytes' info
            star_data=dict() #This sorts all the acolytes by their rarity
            for key in acolyte_list:
                if acolyte_list[key]["Rarity"] not in star_data:
                    star_data[acolyte_list[key]['Rarity']]=[key]
                else:
                    star_data[acolyte_list[key]['Rarity']].append(key)

        #Check to see if player has reached pity
        pity = info['pitycounter']
        output = ''

        for _ in range(rolls):

            if pity >= 79:
                reward = ['acolyte']
                name=random.choice(star_data[5])
                await self.doDupe(ctx.author.id, name)
                pity = 0

            else: 
                winner=random.randint(1,100)

                #Determine if reward will be a weapon
                reward = random.choices(['weapon', 'acolyte'], [75, 25])

                #Select a random weapon or acolyte
                if winner in five_star: #If its a five star reset the pity
                    if reward[0] == 'weapon':
                        item_info = await AssetCreation.createItem(self.client.pg_con, 
                                                                   ctx.author.id, 
                                                                   random.randint(100, 150), 
                                                                   'Legendary', 
                                                                   returnstats=True)
                    else:
                        name=random.choice(star_data[5])
                        await self.doDupe(ctx.author.id, name)
                    pity = 0
                else: #Add one to the pitycounter
                    if winner in two_star:
                        if reward[0] == 'weapon':
                            item_info = await AssetCreation.createItem(self.client.pg_con, 
                                                                       ctx.author.id, 
                                                                       random.randint(30,60), 
                                                                       'Uncommon', 
                                                                       returnstats=True)
                        else:
                            name=random.choice(star_data[2])
                            await self.doDupe(ctx.author.id, name)

                    elif winner in three_star:
                        if reward[0] == 'weapon':
                            item_info = await AssetCreation.createItem(self.client.pg_con, 
                                                                       ctx.author.id, 
                                                                       random.randint(45,90), 
                                                                       'Rare', 
                                                                       returnstats=True)
                        else:
                            name=random.choice(star_data[3])
                            await self.doDupe(ctx.author.id, name)

                    elif winner in four_star:
                        if reward[0] == 'weapon':
                            item_info = await AssetCreation.createItem(self.client.pg_con, 
                                                                       ctx.author.id, 
                                                                       random.randint(75,120), 
                                                                       'Epic', 
                                                                       returnstats=True)
                        else:
                            name=random.choice(star_data[4])
                            await self.doDupe(ctx.author.id, name)

                    elif winner in one_star:
                        if reward[0] == 'weapon': #Minimum 2 star weapons from gacha
                            item_info = await AssetCreation.createItem(self.client.pg_con, 
                                                                       ctx.author.id, 
                                                                       random.randint(30,60), 
                                                                       'Uncommon', 
                                                                       returnstats=True)
                        else:
                            name=random.choice(star_data[1])
                            await self.doDupe(ctx.author.id, name)

                    pity += 1

            if reward[0] == 'acolyte':
                output += f"{acolyte_list[name]['Rarity']}⭐ Acolyte: {acolyte_list[name]['Name']}\n"
            elif reward[0] == 'weapon':
                output += f"({item_info['Rarity']}) {item_info['Name']}, with {item_info['Attack']} ATK and {item_info['Crit']} CRIT.\n"

        output += f"\nYou have {info['rubidic']-rolls} rubidics. You will receive a 5⭐ acolyte in {80-pity} summons."

        #With acolyte(s) chosen, update rubidics and pity counter
        await AssetCreation.setPityCounter(self.client.pg_con, ctx.author.id, pity)
        rubidics = info['rubidic'] - rolls
        await AssetCreation.setRubidics(self.client.pg_con, ctx.author.id, rubidics)

        #Send embed
        if rolls == 1:
            if reward[0] == 'acolyte':
                embed = discord.Embed(title=f"{name} ({acolyte_list[name]['Rarity']}⭐) has entered the tavern!", 
                                      color=self.client.ayesha_blue)
                if acolyte_list[name]['Image'] is not None:
                    embed.set_thumbnail(url=f"{acolyte_list[name]['Image']}")
                embed.add_field(name='Attack', 
                                value=f"{acolyte_list[name]['Attack']} + {acolyte_list[name]['Scale']}/lvl")
                embed.add_field(name='Crit', 
                                value=f"{acolyte_list[name]['Crit']}")
                embed.add_field(name='HP', value=f"{acolyte_list[name]['HP']}")
                if acolyte_list[name]['Effect'] is None:
                    embed.add_field(name='Effect', 
                                    value=f" No effect.\n{name} uses {acolyte_list[name]['Mat']} to level up.")
                else:
                    embed.add_field(name='Effect', 
                                    value=f"{acolyte_list[name]['Effect']}\n{name} uses `{acolyte_list[name]['Mat']}` to level up.", inline=False)
                embed.set_footer(text=f"You have {rubidics} rubidics. You will receive a 5-star in {80-pity} summons.")
            else:
                embed = discord.Embed(title=f"You received {item_info['Name']} ({item_info['Rarity']})!", color=self.client.ayesha_blue)
                embed.add_field(name='Type', value=f"{item_info['Type']}")
                embed.add_field(name='Attack', value=f"{item_info['Attack']}")
                embed.add_field(name='Crit', value=f"{item_info['Crit']}")
                embed.set_footer(text=f"You have {rubidics} rubidics. You will receive a 5-star in {80-pity} summons.")

            await ctx.reply(embed=embed)
        else:
            await ctx.reply(f"```{output}```")

    @commands.command(aliases=['goldsummon', 'gr', 'gs'], 
                      brief='<rolls (1-10)>', 
                      description='Spend 100,000 gold to get a random acolyte or weapon! This gives inferior drops to the the `roll` command.')
    @commands.check(Checks.is_player)
    async def goldroll(self, ctx, rolls : int = 1):
        #Make sure they have enough gold
        if rolls > 10:
            return await ctx.reply('You can only roll up to 10 times at once!')
        
        if await AssetCreation.getGold(self.client.pg_con, ctx.author.id) < rolls * 100000:
            return await ctx.reply('You don\'t have enough gold to roll this many times.')

        #Load the list of acolytes
        with open(Links.acolyte_list) as f:
            acolyte_list=json.load(f) #This stores all the acolytes' info
            star_data=dict() #This sorts all the acolytes by their rarity
            for key in acolyte_list:
                if acolyte_list[key]["Rarity"] not in star_data:
                    star_data[acolyte_list[key]['Rarity']]=[key]
                else:
                    star_data[acolyte_list[key]['Rarity']].append(key)

        output = ''

        for _ in range(rolls):
            winner=random.randint(1,250)

            #Determine if reward will be a weapon
            reward = random.choices(['weapon', 'acolyte'], [85, 15])

            #Select a random weapon or acolyte
            if winner in two_star or winner >= 200:
                if reward[0] == 'weapon':
                    item_info = await AssetCreation.createItem(self.client.pg_con, 
                                                               ctx.author.id, 
                                                               random.randint(30,60), 
                                                               'Uncommon', 
                                                               returnstats=True)
                else:
                    name=random.choice(star_data[2])
                    await self.doDupe(ctx.author.id, name)

            elif winner in three_star or winner >= 110:
                if reward[0] == 'weapon':
                    item_info = await AssetCreation.createItem(self.client.pg_con, 
                                                               ctx.author.id, 
                                                               random.randint(45,90), 
                                                               'Rare', 
                                                               returnstats=True)
                else:
                    name=random.choice(star_data[3])
                    await self.doDupe(ctx.author.id, name)

            elif winner in four_star or winner > 100:
                if reward[0] == 'weapon':
                    item_info = await AssetCreation.createItem(self.client.pg_con, 
                                                               ctx.author.id, 
                                                               random.randint(75,110), 
                                                               'Epic', 
                                                               returnstats=True)
                else:
                    name=random.choice(star_data[4])
                    await self.doDupe(ctx.author.id, name)

            elif winner in five_star:
                if reward[0] == 'weapon':
                    item_info = await AssetCreation.createItem(self.client.pg_con, 
                                                               ctx.author.id, 
                                                               random.randint(90,140), 
                                                               'Legendary', 
                                                               returnstats=True)

            elif winner in one_star:
                if reward[0] == 'weapon': #Minimum 2 star weapons from gacha
                    item_info = await AssetCreation.createItem(self.client.pg_con, 
                                                               ctx.author.id, 
                                                               random.randint(30,60), 
                                                               'Uncommon', 
                                                               returnstats=True)
                else:
                    name=random.choice(star_data[1])
                    await self.doDupe(ctx.author.id, name)

            if reward[0] == 'acolyte':
                output += f"{acolyte_list[name]['Rarity']}⭐ Acolyte: {acolyte_list[name]['Name']}\n"
            elif reward[0] == 'weapon':
                output += f"({item_info['Rarity']}) {item_info['Name']}, with {item_info['Attack']} ATK and {item_info['Crit']} CRIT.\n"

        #With acolyte(s) chosen, update gold
        await AssetCreation.giveGold(self.client.pg_con, -100000 * rolls, ctx.author.id)

        #Send embed
        if rolls == 1:
            if reward[0] == 'acolyte':
                embed = discord.Embed(title=f"{name} ({acolyte_list[name]['Rarity']}⭐) has entered the tavern!", 
                                      color=self.client.ayesha_blue)
                if acolyte_list[name]['Image'] is not None:
                    embed.set_thumbnail(url=f"{acolyte_list[name]['Image']}")
                embed.add_field(name='Attack', 
                                value=f"{acolyte_list[name]['Attack']} + {acolyte_list[name]['Scale']}/lvl")
                embed.add_field(name='Crit', value=f"{acolyte_list[name]['Crit']}")
                embed.add_field(name='HP', value=f"{acolyte_list[name]['HP']}")
                if acolyte_list[name]['Effect'] is None:
                    embed.add_field(name='Effect', 
                                    value=f" No effect.\n{name} uses {acolyte_list[name]['Mat']} to level up.")
                else:
                    embed.add_field(name='Effect', 
                                    value=f"{acolyte_list[name]['Effect']}\n{name} uses `{acolyte_list[name]['Mat']}` to level up.", inline=False)
                # embed.set_footer(text=f"You have {rubidics} rubidics. You will receive a 5-star in {80-pity} summons.")
            else:
                embed = discord.Embed(title=f"You received {item_info['Name']} ({item_info['Rarity']})!", 
                                      color=self.client.ayesha_blue)
                embed.add_field(name='Type', value=f"{item_info['Type']}")
                embed.add_field(name='Attack', value=f"{item_info['Attack']}")
                embed.add_field(name='Crit', value=f"{item_info['Crit']}")
                # embed.set_footer(text=f"You have {rubidics} rubidics. You will receive a 5-star in {80-pity} summons.")

            await ctx.reply(embed=embed)
        else:
            await ctx.reply(f"```{output}```")

        #Send output

    @commands.command(aliases=['rolls', 'summons'], 
                      description='See how many rubidics you have and how many more summons are needed until receiving guaranteed 5*')
    @commands.check(Checks.is_player)
    async def rubidics(self, ctx):
        info = await AssetCreation.getRubidics(self.client.pg_con, ctx.author.id)
        await ctx.reply(f"You have **{info['rubidic']}** rubidics.\nYou will get a 5⭐ weapon or acolyte in **{80-info['pitycounter']}** summons.")

    @commands.group(description='Exchange extra gold for some stuff!', invoke_without_command=True, case_insensitive=True)
    @commands.check(Checks.is_player)
    async def shop(self, ctx):
        shop = discord.Embed(title='Gold Shop', 
                             description='Exchange your gold for some items!', 
                             color=self.client.ayesha_blue)
        shop.add_field(name='Weapon and Acolyte Materials', 
                       value='Do `shop material <material> <amount>` to buy this!\nEach material costs 200 gold.', 
                       inline=False)
        shop.add_field(name='Epic Weapon', 
                       value='Do `shop epic` to buy this!\nReceive a random epic item for 500,000 gold.', 
                       inline=False)
        shop.add_field(name='Rare Weapon', 
                       value='Do `shop rare` to buy this!\nReceive a random rare item for 50,000 gold.', 
                       inline=False)
        shop.add_field(name='Rubidic', 
                       value='Do `shop rubidic` to buy this!\nReceive 1 rubidic for 10,000,000 gold.')
        await ctx.reply(embed=shop)


    @shop.command(brief='<material> <amount>', description='Purchase a resource. Each resource costs 200 gold.')
    @commands.check(Checks.is_player)
    async def material(self, ctx, material : str, amount : int):
        #Make sure the material and amount is a valid amount
        material = material.lower()
        mats = ('fur', 'bone', 'iron', 'silver', 'wood', 'wheat', 'oat', 'reeds', 'pine', 'moss', 'cacao')
        if material not in mats:
            await ctx.reply('That is not a valid material. The purchaseable materials are those listed in the `backpack` command.')
            return

        if amount < 1:
            await ctx.reply('You cannot purchase less than 1 of a material!')
            return
        
        #Make sure player has enough gold for this transaction
        player_gold = await AssetCreation.getGold(self.client.pg_con, ctx.author.id)
        cost = amount * 200
        if player_gold < cost:
            await ctx.reply(f'Buying `{amount}` of this resources costs `{cost}` gold. You don\'t have enough gold (you have `{player_gold}`).')
            return

        #Fulfill the transaction
        await AssetCreation.giveMat(self.client.pg_con, material, amount, ctx.author.id)
        await AssetCreation.giveGold(self.client.pg_con, 0-cost, ctx.author.id)

        await ctx.reply(f'Successfully bought {amount} {material} for {cost} gold.')

    @shop.command(description='Get a new epic weapon! Costs 500,000 gold.')
    @commands.check(Checks.is_player)
    async def epic(self, ctx):
        #Make sure player has enough gold for this transaction
        player_gold = await AssetCreation.getGold(self.client.pg_con, ctx.author.id)
        if player_gold < 500000:
            await ctx.reply(f'Buying an epic weapon costs `500,000` gold. You don\'t have enough gold (you have `{player_gold}`).')
            return

        item_info = await AssetCreation.createItem(self.client.pg_con, 
                                                   ctx.author.id, 
                                                   random.randint(75,120), 
                                                   'Epic', 
                                                   returnstats=True)
        await AssetCreation.giveGold(self.client.pg_con, -500000, ctx.author.id)

        embed = discord.Embed(title=f"You received {item_info['Name']} ({item_info['Rarity']})!", 
                              color=self.client.ayesha_blue)            
        embed.add_field(name='Type', value=f"{item_info['Type']}")
        embed.add_field(name='Attack', value=f"{item_info['Attack']}")
        embed.add_field(name='Crit', value=f"{item_info['Crit']}")
        embed.set_footer(text=f"You now have {player_gold - 500000} gold.")

        await ctx.reply(embed=embed)

    @shop.command(description='Get a new rare weapon! Costs 50,000 gold.')
    @commands.check(Checks.is_player)
    async def rare(self, ctx):
        #Make sure player has enough gold for this transaction
        player_gold = await AssetCreation.getGold(self.client.pg_con, ctx.author.id)
        if player_gold < 50000:
            await ctx.reply(f'Buying a rare weapon costs `50,000` gold. You don\'t have enough gold (you have `{player_gold}`).')
            return

        item_info = await AssetCreation.createItem(self.client.pg_con, 
                                                   ctx.author.id, 
                                                   random.randint(45,90), 
                                                   'Rare', 
                                                   returnstats=True)
        await AssetCreation.giveGold(self.client.pg_con, -50000, ctx.author.id)

        embed = discord.Embed(title=f"You received {item_info['Name']} ({item_info['Rarity']})!", 
                              color=self.client.ayesha_blue)            
        embed.add_field(name='Type', value=f"{item_info['Type']}")
        embed.add_field(name='Attack', value=f"{item_info['Attack']}")
        embed.add_field(name='Crit', value=f"{item_info['Crit']}")
        embed.set_footer(text=f"You now have {player_gold - 50000} gold.")

        await ctx.reply(embed=embed)

    @shop.command(description='Get a rubidic. 1 rubidic for 10,000,000 gold.')
    @commands.check(Checks.is_player)
    async def rubidic(self, ctx, amount : int):
        #Make sure player has enough gold for this transaction
        if amount < 1:
            await ctx.reply('Lol')
            return

        player_gold = await AssetCreation.getGold(self.client.pg_con, ctx.author.id)
        cost = amount * 10000000
        if player_gold < cost:
            await ctx.reply(f'Buying a rubidic costs `10,000,000` gold. You don\'t have enough gold (you have `{player_gold}`).')
            return

        #Otherwise process the transaction
        await AssetCreation.giveRubidics(self.client.pg_con, amount, ctx.author.id)
        await AssetCreation.giveGold(self.client.pg_con, 0-cost, ctx.author.id)

        if amount == 1:
            await ctx.reply(f'Successfully bought `1` rubidic for `{cost}` gold.')
        else:
            await ctx.reply(f'Successfully bought `{amount}` rubidics for `{cost}` gold.')

    @shop.command(brief='<material> <amount>', description='Sell your materials for 20 gold each.')
    @commands.check(Checks.is_player)
    async def sell(self, ctx, material : str, amount : int):
        #Make sure they have the mats
        material = material.lower()
        mats = ('fur', 'bone', 'iron', 'silver', 'wood', 'wheat', 'oat', 'reeds', 'pine', 'moss', 'cacao')
        if material not in mats:
            return await ctx.reply('That is not a valid material. The purchaseable materials are those listed in the `backpack` command.')

        if amount < 1:
            return await ctx.reply('You cannot sell less than 1 of a material!')
         
        mat_amount = await AssetCreation.getPlayerMat(self.client.pg_con, material, ctx.author.id)

        if amount > mat_amount:
            return await ctx.reply(f'You only have up to {mat_amount} {material} to sell.')

        #Delete mats and give gold
        await AssetCreation.giveGold(self.client.pg_con, amount * 20, ctx.author.id)
        await AssetCreation.giveMat(self.client.pg_con, material, -1*amount, ctx.author.id)

        await ctx.reply(f'You sold {amount} {material} for {amount * 20} gold.')

def setup(client):
    client.add_cog(Gacha(client))