import discord
import asyncio

from discord.ext import commands
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

import aiosqlite
from Utilities import Checks, AssetCreation, PageSourceMaker

from dpymenus import Page, PaginatedMenu

import random
import math
import time

PATH = 'PATH'

location_dict = {
    'Aramithea' : {
        'Biome' : 'City', 
        'CD' : 1800,
        'Drops' : 'You can `upgrade` your weapons here.'
        },
    'Mythic Forest' : {
        'Biome' : 'Forest', 
        'CD' : 3600,
        'Drops' : 'You can `hunt` and `forage` here for `fur`, `bone`, and `wood`.'
        }, 
    'Thenuille' : {
        'Biome' : 'Town', 
        'CD' : 1800,
        'Drops' : 'You can `upgrade` your weapons here and `fish`.'
        },
    'Fernheim' : {
        'Biome' : 'Grassland', 
        'CD' : 1800,
        'Drops' : 'You can `hunt` and `forage` here for `fur`, `bone`, and `wheat`.'
        },
    'Sunset Prairie' : {
        'Biome' : 'Grassland', 
        'CD' : 3600,
        'Drops' : 'You can `hunt` and `forage` here for `fur`, `bone`, and `oats`.'
        },
    'Riverburn' : {
        'Biome' : 'City', 
        'CD' : 3600,
        'Drops' : 'You can `upgrade` your weapons here.'
        },
    'Thanderlans' : {
        'Biome' : 'Marsh', 
        'CD' : 7200,
        'Drops' : 'You can `forage` here for `reeds`.'
        },
    'Glakelys' : {
        'Biome' : 'Grassland', 
        'CD' : 3600,
        'Drops' : 'You can `hunt` and `forage` here for `fur`, `bone`, and `oats`.'
        },
    'Russe' : {
        'Biome' : 'Taiga', 
        'CD' : 12600,
        'Drops' : 'You can `hunt` and `forage` here for `fur`, `bone`, `pine`, and `moss`.'
        },
    'Croire' : {
        'Biome' : 'Grassland', 
        'CD' : 9000,
        'Drops' : 'You can `hunt` and `forage` here for `fur`, and `wheat`.'
        },
    'Crumidia' : {
        'Biome' : 'Hills', 
        'CD' : 10800,
        'Drops' : 'You can `mine` and `forage` here for `iron`.'
        },
    'Kucre' : {
        'Biome' : 'Jungle', 
        'CD' : 14400,
        'Drops' : 'You can `forage` here for `cacao`.'
        }
}

class Travel(commands.Cog):

    def __init__(self, client):
        self.client = client

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('Travel is ready.')

    #INVISIBLE
    def convertagain(self, seconds : int):
        return time.strftime("%H:%M:%S", time.gmtime(seconds))

    def write(self):
        i=0
        embeds = []
        for location in location_dict:
            if i == 0:
                embed = Page(title='Locations')
            
            embed.add_field(name=f"{location}", 
                value=f"**Biome: **`{location_dict[location]['Biome']}`, **Travel Time: **`{self.convertagain(location_dict[location]['CD'])}`\n{location_dict[location]['Drops']}", 
                inline=False)
            
            if i == 3:
                i = 0
                embeds.append(embed)
            else:
                i += 1

            if location == 'Kucre':
                embeds.append(embed)
        return embeds

    #COMMANDS
    @commands.command(brief='<destination>', description='Travel to another area of the map, unlocking a different subset of commands.')
    @commands.check(Checks.is_player)
    async def travel(self, ctx, *, destination : str = None):
        if destination is None:
            locations = self.write()
            menu = PaginatedMenu(ctx)
            menu.add_pages(locations)
            menu.set_timeout(30)
            menu.show_command_message()
            await menu.open()
            return

        adv = await AssetCreation.getAdventure(ctx.author.id)
        if adv[0] is not None:
            await ctx.reply('You are currently traveling. Please wait until you arrive at your destination before traveling again.')
            return

        destination = destination.title()

        if await AssetCreation.getLocation(ctx.author.id) == destination:
            await ctx.reply('You are already there!')
            return

        try:
            loc = location_dict[f'{destination}']
        except KeyError:
            await ctx.reply('That is not a valid location.')
            return
        
        cd = time.time() + loc['CD'] # Adventure time varies depending on region
        cd = int(cd)

        # Start the adventure and input end time and destination into database
        async with aiosqlite.connect(PATH) as conn:
            await conn.execute('UPDATE players SET adventure = ?, destination = ? WHERE user_id = ?', (cd, destination, ctx.author.id))
            await conn.commit()
        
        # Tell player when their adventure will be done
        await ctx.reply(f"You will arrive at `{destination}` in `{self.convertagain(loc['CD'])}`.")

    @commands.command(description='See how long until you arrive at your new location or collect rewards for moving.')
    @commands.check(Checks.is_player)
    async def arrive(self, ctx):
        adv = await AssetCreation.getAdventure(ctx.author.id)
        if adv is None:
            await ctx.reply('You aren\'t travelling. Use `travel` to explore somewhere new!')
            return

        current = int(time.time())
        if current >= adv[0]: #Then enough time has passed and the adv is complete
            low_bound = math.floor((location_dict[adv[1]]['CD']**1.5)/2500)
            high_bound = math.floor((location_dict[adv[1]]['CD']**1.6)/5000)
            gold = random.randint(low_bound, high_bound)
            xp = random.randint(low_bound, high_bound)
            acolyte_xp = math.floor(xp / 10)
            getWeapon = random.randint(1,10)
            if getWeapon == 1:
                await AssetCreation.createItem(ctx.author.id, random.randint(15, 40), "Common")

            #Also give bonuses to acolytes if any
            acolyte1, acolyte2 = await AssetCreation.getAcolyteFromPlayer(ctx.author.id)

            async with aiosqlite.connect(PATH) as conn:
                await conn.execute("""UPDATE players SET 
                    xp = xp + ?, gold = gold + ?, location = ?, 
                    adventure = NULL, destination = NULL 
                    WHERE user_id = ?""", (xp, gold, adv[1], ctx.author.id))

                if acolyte1 is not None:
                    ('UPDATE acolytes SET xp = xp + ? WHERE instance_id = ?', (acolyte_xp, acolyte1))
                if acolyte2 is not None:
                    ('UPDATE acolytes SET xp = xp + ? WHERE instance_id = ?', (acolyte_xp, acolyte2,))

                await conn.commit()
                if getWeapon == 1:
                    await ctx.reply(f'You arrived at `{adv[1]}`! On the way you earned `{xp}` xp and `{gold}` gold. You also found a weapon!')
                else:
                    await ctx.reply(f'You arrived at `{adv[1]}`! On the way you earned `{xp}` xp and `{gold}` gold.')

                #Check for level ups
                await AssetCreation.checkLevel(ctx, ctx.author.id, aco1=acolyte1, aco2=acolyte2)

        else: 
            wait = adv[0] - current
            await ctx.reply(f'You will arrive at `{adv[1]}` in `{self.convertagain(wait)}`.')

    @commands.command(description='Cancel your current travel-state.')
    @commands.check(Checks.is_player)
    async def cancel(self, ctx):
        adv = await AssetCreation.getAdventure(ctx.author.id)
        if adv is None:
            await ctx.reply('You aren\'t travelling. Use `travel` to explore somewhere new!')
            return

        current = int(time.time())
        if current >= adv[0]: #Then enough time has passed and the adv is complete
            low_bound = math.floor((location_dict[adv[1]]['CD']**1.5)/2500)
            high_bound = math.floor((location_dict[adv[1]]['CD']**1.6)/5000)
            gold = random.randint(low_bound, high_bound)
            xp = random.randint(low_bound, high_bound)
            acolyte_xp = math.floor(xp / 10)
            getWeapon = random.randint(1,10)
            if getWeapon == 1:
                await AssetCreation.createItem(ctx.author.id, random.randint(15, 40), "Common")

            #Also give bonuses to acolytes if any
            acolyte1, acolyte2 = await AssetCreation.getAcolyteFromPlayer(ctx.author.id)

            async with aiosqlite.connect(PATH) as conn:
                await conn.execute("""UPDATE players SET 
                    xp = xp + ?, gold = gold + ?, location = ?, 
                    adventure = NULL, destination = NULL 
                    WHERE user_id = ?""", (xp, gold, adv[1], ctx.author.id))

                if acolyte1 is not None:
                    ('UPDATE acolytes SET xp = xp + ? WHERE instance_id = ?', (acolyte_xp, acolyte1))
                if acolyte2 is not None:
                    ('UPDATE acolytes SET xp = xp + ? WHERE instance_id = ?', (acolyte_xp, acolyte2,))

                await conn.commit()
                if getWeapon == 1:
                    await ctx.reply(f'You arrived at `{adv[1]}`! On the way you earned `{xp}` xp and `{gold}` gold. You also found a weapon!')
                else:
                    await ctx.reply(f'You arrived at `{adv[1]}`! On the way you earned `{xp}` xp and `{gold}` gold.')

                #Check for level ups
                await AssetCreation.checkLevel(ctx, ctx.author.id, aco1=acolyte1, aco2=acolyte2)

        else:
            async with aiosqlite.connect(PATH) as conn:
                await conn.execute('UPDATE players SET adventure = NULL, destination = NULL WHERE user_id = ?', (ctx.author.id,))
                await conn.commit()
                await ctx.reply('You decided not to travel.')

    @commands.command(description='Hunt for food. You may get fur and bone, which is needed to buff your acolytes.')
    @commands.check(Checks.is_player)
    @cooldown(1, 15, type=BucketType.user)
    async def hunt(self, ctx):
        #Make sure they're in hunting territory
        location = await AssetCreation.getLocation(ctx.author.id)
        biome = location_dict[location]['Biome']
        if biome != 'Grassland' and biome != 'Forest' and biome != 'Taiga': # These are the biomes you can hunt in
            await ctx.reply(f'You cannot hunt at {location}. Move to a grassland, forest, or taiga.')
            return

        #Otherwise calculate some stuff
        #Since hunt is such a common command, rewards are low, and lower in taiga
        result = random.choices(['success', 'critical success', 'failure'], [80,12,8])
        if result[0] == 'success':
            gold = random.randint(20,100)
            fur = random.randint(6,12)
            bone = int(fur / 3)

        elif result[0] == 'critical':
            gold = random.randint(100, 150)
            fur = random.randint(12,18)
            bone = int(fur/3)

        else:
            gold = 10
            fur = 0
            bone = 0

        async with aiosqlite.connect(PATH) as conn:
            await conn.execute('UPDATE players SET gold = gold + ? WHERE user_id = ?', (gold, ctx.author.id))
            await conn.execute('UPDATE resources SET fur = fur + ?, bone = bone + ? WHERE user_id = ?', (fur, bone, ctx.author.id))
            await conn.commit()

        await ctx.reply(f'Your hunting trip was a {result[0]}! You got `{gold}` gold, `{fur}` furs, and `{bone}` bones.')

    @commands.command(description='Mine for ore. You may get iron or silver, which is needed to buff your acolytes.')
    @commands.check(Checks.is_player)
    @cooldown(1, 30, type=BucketType.user)
    async def mine(self, ctx):
        #Make sure they're in mining territory
        location = await AssetCreation.getLocation(ctx.author.id)
        biome = location_dict[location]['Biome']
        if biome != 'Hills': # These are the biomes you can hunt in
            await ctx.reply(f'You cannot mine at {location}. Move to a hills biome.')
            return

        #Otherwise calc
        result = random.choices(['success', 'critical success', 'failure'], [45,35,20])
        if result[0] == 'success':
            gold = random.randint(20,100)
            iron = random.randint(20,30)
            silver = random.randint(0,2)

        elif result[0] == 'critical':
            gold = random.randint(100, 150)
            iron = random.randint(20,30)
            silver =  random.randint(10,20)

        else:
            gold = random.randint(10,30)
            iron = random.randint(10,20)
            silver = 0

        async with aiosqlite.connect(PATH) as conn:
            await conn.execute('UPDATE players SET gold = gold + ? WHERE user_id = ?', (gold, ctx.author.id))
            await conn.execute('UPDATE resources SET iron = iron + ?, silver = silver + ? WHERE user_id = ?', (iron, silver, ctx.author.id))
            await conn.commit()

        await ctx.reply(f'Your mining expedition was a {result[0]}! You got `{gold}` gold, `{iron}` iron, and `{silver}` silver.')

    @commands.command(description='Forage for materials depending on your location. These materials may buff your acolytes.')
    @commands.check(Checks.is_player)
    @cooldown(1, 60, type=BucketType.user)
    async def forage(self, ctx):
        #Get player location and materials.
        location = await AssetCreation.getLocation(ctx.author.id)
        try:
            biome = location_dict[location]['Biome']
        except TypeError:
            await ctx.reply('Move to a location before foraging!')
            return

        if biome == 'City' or biome == 'Town':
            await ctx.reply(f'You can\'t forage here at {location}! Get outside of an urban area.')
            return
        elif location == 'Fernheim' or location == 'Croire':
            mat = 'wheat'
            amount = random.randint(20,50)
        elif location == 'Sunset Prairie' or location =='Glakelys':
            mat = 'oat'
            amount = random.randint(5,20)
        elif biome == 'Forest':
            mat = 'wood'
            amount = random.randint(10,30)
        elif biome == 'Marsh':
            mat = 'reeds'
            amount = random.randint(40,80)
        elif biome == 'Taiga':
            material = random.choices(['pine', 'moss'], [66, 33])
            mat = material[0]
            if mat == 'pine':
                amount = random.randint(30,40)
            else:
                amount = random.randint(10,20)
        elif biome == 'Hills':
            mat = 'iron'
            amount = random.randint(5,10)
        elif biome == 'Jungle':
            mat = 'cacao'
            amount = random.randint(3,7)

        await AssetCreation.giveMat(mat, amount, ctx.author.id)

        await ctx.reply(f'You received `{amount} {mat}` while foraging in `{location}`.')

    @commands.command(aliases=['pack'], description='See how many materials you have.')
    @commands.check(Checks.is_player)
    async def backpack(self, ctx):
        async with aiosqlite.connect(PATH) as conn:
            c = await conn.execute('SELECT fur, bone, iron, silver, wood, wheat, oat, reeds, pine, moss, cacao FROM resources WHERE user_id = ?', (ctx.author.id,))
            backpack = await c.fetchone()
            mats = ('Fur', 'Bone', 'Iron', 'Silver', 'Wood', 'Wheat', 'Oat', 'Reeds', 'Pine', 'Moss', 'Cacao')

            embed = discord.Embed(title='Your Backpack', color=0xBEDCF6)
            for i in range(len(backpack)):
                embed.add_field(name=f'{mats[i]}', value=f'{backpack[i]}')
       
        await ctx.reply(embed=embed)

    @commands.command(description='Fish for food.')
    @commands.check(Checks.is_player)
    @cooldown(1,15,type=BucketType.user)
    async def fish(self, ctx):
        #Fishing only in Thenuille
        location = await AssetCreation.getLocation(ctx.author.id)
        if location != 'Thenuille':
            await ctx.reply('You can\'t fish here. Go to Thenuille.')
            return

        result = random.choices(['🐟','🐠','🐡','🦈','🦦','nothing'], [35, 20, 3, 1, 1, 40])
        fish = result[0]

        if fish == 'nothing':
            await ctx.reply('You waited but didn\'t catch anything.')
        elif fish == '🦦':
            await AssetCreation.giveGold(1, ctx.author.id)
            await ctx.reply(f'You caught {fish}? It gave you a gold coin before jumping back into the water.')
        else: #give them some gold
            if fish == '🐟':
                gold = random.randint(10,20)
            elif fish == '🐠':
                gold = random.randint(20,40)
            elif fish == '🐡':
                gold = random.randint(20,30)
            elif fish == '🦈':
                gold = random.randint(200,300)
            
            await AssetCreation.giveGold(gold, ctx.author.id)
            await ctx.reply(f'You caught a {fish}! You sold your prize for `{gold}` gold.')

    @commands.command(brief='<item id>', description='Upgrade the ATK stat of a weapon.')
    @commands.check(Checks.is_player)
    # @cooldown(1,1800,type=BucketType.user)
    async def upgrade(self, ctx, item_id : int):
        #Upgrade only in Cities or Towns
        location = await AssetCreation.getLocation(ctx.author.id)
        if location != 'Thenuille' and location != 'Aramithea' and location != 'Riverburn':
            await ctx.reply('You can only upgrade your items in an urban center!')
            return

        #Make sure the item exists and that they own it
        async with aiosqlite.connect(PATH) as conn:
            c = await conn.execute('SELECT item_id, attack, rarity, weapon_name FROM items WHERE item_id = ? AND owner_id = ?', (item_id, ctx.author.id))
            item = await c.fetchone()
            if item is None:
                await ctx.reply("No such item of yours exists.")
                return

            #Get the item's rarity and prevent them from upgrading it past the limit (50 for commons, +25 for each above)
            if item[2] == 'Common':
                if item[1] >= 50:
                    await ctx.reply('A common weapon can have a maximum ATK stat of 50.')
                    return

            elif item[2] == 'Uncommon':
                if item[1] >= 75:
                    await ctx.reply('An uncommon weapon can have a maximum ATK stat of 75.')
                    return

            elif item[2] == 'Rare':
                if item[1] >= 100:
                    await ctx.reply('A rare weapon can have a maximum ATK stat of 100.')
                    return

            elif item[2] == 'Epic':
                if item[1] >= 125:
                    await ctx.reply('An epic weapon can have a maximum ATK stat of 125.')
                    return

            elif item[2] == 'Legendary':
                if item[1] >= 160:
                    await ctx.reply('A legendary weapon can have a maximum ATK stat of 160.')
                    return

            #Ensure they have the ore and gold to upgrade this weapon
            #Upgrade costs: 3 * (ATK + 1) iron; 20 * (ATK + 1) gold
            iron_cost = 3 * (item[1] + 1)
            gold_cost = 20 * (item[1] + 1)

            c = await conn.execute("""SELECT gold, iron FROM players 
                INNER JOIN resources WHERE players.user_id = resources.user_id
                AND players.user_id = ?""", (ctx.author.id,))
            gold, iron = await c.fetchone()
            
            if gold < gold_cost or iron < iron_cost:
                await ctx.reply(f'Upgrading this item to `{item[1]+1}` ATK costs `{iron_cost}` iron and `{gold_cost}` gold. You don\'t have enough resources.')
                return

            #Upgrade the weapon
            await conn.execute('UPDATE items SET attack = attack + 1 WHERE item_id = ?', (item_id,))
            await conn.execute('UPDATE players SET gold = gold - ? WHERE user_id = ?', (gold_cost, ctx.author.id))
            await conn.execute('UPDATE resources SET iron = iron - ? WHERE user_id = ?', (iron_cost, ctx.author.id))
            await conn.commit()
            await ctx.reply(f'Success! You consumed `{gold_cost}` gold and `{iron_cost}` iron to upgrade your `{item[3]}` to `{item[1]+1}` ATK.')


def setup(client):
    client.add_cog(Travel(client))