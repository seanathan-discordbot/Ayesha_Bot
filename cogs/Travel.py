import discord
import asyncio

from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

from Utilities import Links, Checks, AssetCreation, PageSourceMaker

import random
import math
import time

import aiohttp

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
        'Drops' : 'You can `mine` and `forage` here for `iron` and `silver`.'
        },
    'Kucre' : {
        'Biome' : 'Jungle', 
        'CD' : 14400,
        'Drops' : 'You can `forage` here for `cacao`.'
        }
}

class Travel(commands.Cog):
    """Explore the land of Rabidus"""

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
                embed = discord.Embed(title='Locations')
            
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

    async def completeExpedition(self, ctx, start_time : int):
        elapsed_time = int(time.time() - start_time)
        if elapsed_time > 604800:
            elapsed_time = 604800

        hours = elapsed_time / 3600

        #Calculate xp, gold, and materials based off elapsed time (in hours)
        if elapsed_time < 3600: #Less than 1 hour, ~100 gold/hr, no gravitas
            gold = math.floor(hours * 100)
            mats = random.randint(10,20)
            gravitas = 0
            gravitas_decay = .01
        elif elapsed_time < 10800: #1-3 hrs, ~175 gold/hr, 30 mats/hr, no gravitas
            gold = math.floor(hours * 175)
            mats = math.floor(hours * 30)
            gravitas = 0
            gravitas_decay = .05
        elif elapsed_time < 43200: #3-12 hrs, ~200 gold/hr, 45 mats/hr, 1/3 gravitas/hr
            gold = math.floor(hours * 265)
            mats = math.floor(hours * 45)
            gravitas = math.floor(hours / 3)
            gravitas_decay = .1
        elif elapsed_time < 259200: #12hrs - 3 days, ~300 gold/hr, 70 mats/hr, 1/2 gravitas/hr
            gold = math.floor(hours * 375)
            mats = math.floor(hours * 70)
            gravitas = math.floor(hours / 2)
            gravitas_decay = .15
        else: #Up to 7 days, ~500 gold/hr, 100 mats/hr, 1 gravitas/hr
            gold = math.floor(hours * 500)
            mats = math.floor(hours * 100)
            gravitas = math.floor(hours)
            gravitas_decay = .2
        
        xp = math.floor(gold / 4 + 50)
        acolyte_xp = math.floor(xp / 10)

        #Give those materials
        await AssetCreation.giveGold(self.client.pg_con, gold, ctx.author.id)
        await AssetCreation.givePlayerXP(self.client.pg_con, xp, ctx.author.id)

        acolyte1, acolyte2 = await AssetCreation.getAcolyteFromPlayer(self.client.pg_con, ctx.author.id)
        if acolyte1 is not None:
            await AssetCreation.giveAcolyteXP(self.client.pg_con, acolyte_xp, acolyte1)
        if acolyte2 is not None:
            await AssetCreation.giveAcolyteXP(self.client.pg_con, acolyte_xp, acolyte2)

        city_expedition = False
        location = await AssetCreation.getLocation(self.client.pg_con, ctx.author.id)
        if location == 'Mythic Forest':
            resource = 'wood'
            await AssetCreation.giveMat(self.client.pg_con, 'wood', mats, ctx.author.id)
        elif location == 'Fernheim' or location == 'Croire':
            resource = 'wheat'
            await AssetCreation.giveMat(self.client.pg_con, 'wheat', mats, ctx.author.id)
        elif location == 'Sunset Prairie' or location == 'Glakelys':
            resource = 'oats'
            await AssetCreation.giveMat(self.client.pg_con, 'oat', mats, ctx.author.id)
        elif location == 'Thanderlans':
            resource = 'reeds'
            await AssetCreation.giveMat(self.client.pg_con, 'reeds', mats, ctx.author.id)
        elif location == 'Russe':
            resource = random.choice(['pine', 'moss'])
            await AssetCreation.giveMat(self.client.pg_con, resource, mats, ctx.author.id)
        elif location == 'Crumidia':
            resource = 'silver'
            await AssetCreation.giveMat(self.client.pg_con, 'silver', mats, ctx.author.id)
        elif location == 'Kucre':
            resource = 'cacao'
            await AssetCreation.giveMat(self.client.pg_con, 'cacao', mats, ctx.author.id)
        else: #then theyre in the city - only time gravitas is gained as a result of expeditions
            resource = random.choice(['fur', 'bone'])
            mats = math.floor(mats / 2)
            await AssetCreation.giveMat(self.client.pg_con, resource, mats, ctx.author.id)
            await AssetCreation.give_gravitas(self.client.pg_con, ctx.author.id, gravitas)
            city_expedition = True

        # Decay gravitas for those who did wild expeditions
        if not city_expedition:
            player_gravitas = await AssetCreation.get_gravitas(self.client.pg_con, ctx.author.id)
            decay_amount = int(player_gravitas * gravitas_decay)
            await AssetCreation.give_gravitas(self.client.pg_con, ctx.author.id, decay_amount * -1)

        await AssetCreation.setAdventure(self.client.pg_con, None, None, ctx.author.id)

        #Send results of player
        if elapsed_time >= 43200 and city_expedition:
            await ctx.reply(f'You returned from your urban expedition and received `{gold}` gold, `{xp}` xp, and `{mats}` {resource}.\nYou also gained `{gravitas}` gravitas while campaigning.')
        else:
            await ctx.reply(f'You returned from your expedition and received `{gold}` gold, `{xp}` xp, and `{mats}` {resource}.\nUnfortunately, you lost `{gravitas_decay}` gravitas while in the wild.')

        await AssetCreation.checkLevel(self.client.pg_con, ctx, ctx.author.id, aco1=acolyte1, aco2=acolyte2)

        return

    #COMMANDS
    @commands.command(brief='<destination>', description='Travel to another area of the map, unlocking a different subset of commands.')
    @commands.check(Checks.is_player)
    async def travel(self, ctx, *, destination : str = None):
        """`destination`: where on the map you are travelling to. Leave blank to see a menu of valid areas.

        Travel to another area of the map, unlocking a different subset of commands.
        """
        if destination is None:
            locations = self.write()
            travel_pages = menus.MenuPages(source=PageSourceMaker.PageMaker(locations), 
                                           clear_reactions_after=True, 
                                           delete_message_after=True)
            await travel_pages.start(ctx)
            return

        adv = await AssetCreation.getAdventure(self.client.pg_con, ctx.author.id)
        if adv['adventure'] is not None:
            await ctx.reply('You are currently traveling. Please wait until you arrive at your destination before traveling again.')
            return

        destination = destination.title()

        if await AssetCreation.getLocation(self.client.pg_con, ctx.author.id) == destination:
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
        await AssetCreation.setAdventure(self.client.pg_con, cd, destination, ctx.author.id)
        
        # Tell player when their adventure will be done
        await ctx.reply(f"You will arrive at `{destination}` in `{self.convertagain(loc['CD'])}`.")

    @commands.command(aliases=['expo'], description='Go on an expedition for a time, returning with materials!')
    @commands.check(Checks.is_player)
    @cooldown(1, 900, type=BucketType.user)
    async def expedition(self, ctx):
        """Go on an expedition for an extended period of time, returning with materials.
        You will receive gold, xp, and materials related to the territory you are in. Urban expeditions will also net you gravitas.
        The longer the expedition, the more you will be rewarded. Rewards only scale up to 1 week, so use `arrive` by then.
        """
        #Make sure they're not on an adventure or traveling
        adventure = await AssetCreation.getAdventure(self.client.pg_con, ctx.author.id)
        if adventure['adventure'] is not None:
            ctx.command.reset_cooldown(ctx)
            return await ctx.reply('You are currently traveling. Please wait until you arrive at your destination before traveling again.')

        #Tell database they're going on an expedition
        await AssetCreation.setAdventure(self.client.pg_con, int(time.time()), "EXPEDITION", ctx.author.id)

        #Send message
        await ctx.reply('You have went on an expedition! You can return at any time with the `arrive` command.\nYou will gain increased rewards the longer you are on expedition, but only for 1 week.')

    @commands.command(description='See how long until you arrive at your new location or collect rewards for moving.')
    @commands.check(Checks.is_player)
    async def arrive(self, ctx):
        """Arrive at your destination. This command is used to both complete `travel` and `expedition`."""
        adv = await AssetCreation.getAdventure(self.client.pg_con, ctx.author.id)
        if adv['adventure'] is None:
            await ctx.reply('You aren\'t travelling. Use `travel` to explore somewhere new!')
            return

        #If they're on an expedition, handle it differently
        if adv['destination'] == 'EXPEDITION':
            await self.completeExpedition(ctx, adv['adventure'])
            return 

        current = int(time.time())
        if current >= adv['adventure']: #Then enough time has passed and the adv is complete
            low_bound = math.floor((location_dict[adv['destination']]['CD']**1.5)/2500)
            high_bound = math.floor((location_dict[adv['destination']]['CD']**1.6)/5000)
            gold = random.randint(low_bound, high_bound)
            xp = random.randint(low_bound, high_bound)
            acolyte_xp = math.floor(xp / 10)
            getWeapon = random.randint(1,10)
            if getWeapon == 1:
                await AssetCreation.createItem(self.client.pg_con, ctx.author.id, random.randint(15, 40), "Common")

            #Class bonus
            role = await AssetCreation.getClass(self.client.pg_con, ctx.author.id)
            if role == 'Traveler':
                gold *= 3

            await AssetCreation.giveAdventureRewards(self.client.pg_con, xp, gold, adv['destination'], ctx.author.id)

            #Also give bonuses to acolytes if any
            acolyte1, acolyte2 = await AssetCreation.getAcolyteFromPlayer(self.client.pg_con, ctx.author.id)

            if acolyte1 is not None:
                await AssetCreation.giveAcolyteXP(self.client.pg_con, acolyte_xp, acolyte1)
            if acolyte2 is not None:
                await AssetCreation.giveAcolyteXP(self.client.pg_con, acolyte_xp, acolyte2)

            if getWeapon == 1:
                await ctx.reply(f"You arrived at `{adv['destination']}`! On the way you earned `{xp}` xp and `{gold}` gold. You also found a weapon!")
            else:
                await ctx.reply(f"You arrived at `{adv['destination']}`! On the way you earned `{xp}` xp and `{gold}` gold.")

            #Check for level ups
            await AssetCreation.checkLevel(self.client.pg_con, ctx, ctx.author.id, aco1=acolyte1, aco2=acolyte2)

        else: 
            wait = adv['adventure'] - current
            await ctx.reply(f"You will arrive at `{adv['destination']}` in `{self.convertagain(wait)}`.")

    @commands.command(description='Cancel your current travel-state.')
    @commands.check(Checks.is_player)
    async def cancel(self, ctx):
        """Cancel your current adventure if travelling."""
        adv = await AssetCreation.getAdventure(self.client.pg_con, ctx.author.id)
        if adv is None:
            await ctx.reply('You aren\'t travelling. Use `travel` to explore somewhere new!')
            return

        #If they're on an expedition, handle it differently
        if adv['destination'] == 'EXPEDITION':
            await self.completeExpedition(ctx, adv['adventure'])
            return 

        current = int(time.time())
        if current >= adv['adventure']: #Then enough time has passed and the adv is complete
            low_bound = math.floor((location_dict[adv['destination']]['CD']**1.5)/2500)
            high_bound = math.floor((location_dict[adv['destination']]['CD']**1.6)/5000)
            gold = random.randint(low_bound, high_bound)
            xp = random.randint(low_bound, high_bound)
            acolyte_xp = math.floor(xp / 10)
            getWeapon = random.randint(1,10)
            if getWeapon == 1:
                await AssetCreation.createItem(self.client.pg_con, ctx.author.id, random.randint(15, 40), "Common")

            #Class bonus
            role = await AssetCreation.getClass(self.client.pg_con, ctx.author.id)
            if role == 'Traveler':
                gold *= 3

            await AssetCreation.giveAdventureRewards(self.client.pg_con, xp, gold, adv['destination'], ctx.author.id)

            #Also give bonuses to acolytes if any
            acolyte1, acolyte2 = await AssetCreation.getAcolyteFromPlayer(self.client.pg_con, ctx.author.id)

            if acolyte1 is not None:
                await AssetCreation.giveAcolyteXP(self.client.pg_con, acolyte_xp, acolyte1)
            if acolyte2 is not None:
                await AssetCreation.giveAcolyteXP(self.client.pg_con, acolyte_xp, acolyte2)

            if getWeapon == 1:
                await ctx.reply(f"You arrived at `{adv['destination']}`! On the way you earned `{xp}` xp and `{gold}` gold. You also found a weapon!")
            else:
                await ctx.reply(f"You arrived at `{adv['destination']}`! On the way you earned `{xp}` xp and `{gold}` gold.")

            #Check for level ups
            await AssetCreation.checkLevel(self.client.pg_con, ctx, ctx.author.id, aco1=acolyte1, aco2=acolyte2)

        else:
            await AssetCreation.setAdventure(self.client.pg_con, None, None, ctx.author.id)
            await ctx.reply('You decided not to travel.')

    @commands.command(description='Hunt for food. You may get fur and bone, which is needed to buff your acolytes.')
    @commands.check(Checks.is_player)
    @cooldown(1, 10, type=BucketType.user)
    async def hunt(self, ctx):
        """Hunt for food, gaining fur and bone, materials that buff certain acolytes.
        The amount of materials you gain is affected by your weapontype.
        Bow: 100% bonus
        Sling: 50% bonus
        Javelin: 25% bonus
        Gauntlets: 50% nerf
        """
        #Make sure they're in hunting territory
        location = await AssetCreation.getLocation(self.client.pg_con, ctx.author.id)
        biome = location_dict[location]['Biome']
        if biome != 'Grassland' and biome != 'Forest' and biome != 'Taiga': # These are the biomes you can hunt in
            await ctx.reply(f'You cannot hunt at {location}. Move to a grassland, forest, or taiga.')
            return

        #Otherwise calculate some stuff
        #Since hunt is such a common command, rewards are low, and lower in taiga
        result = random.choices(['success', 'critical success', 'failure'], [80,12,8])
        if result[0] == 'success':
            gold = random.randint(20,100)
            fur = random.randint(10,18)
            bone = int(fur / 1.2)

        elif result[0] == 'critical success':
            gold = random.randint(100, 150)
            fur = random.randint(18,24)
            bone = int(fur/1.2)

        else:
            gold = random.randint(5,15)
            fur = random.randint(5,10)
            bone = int(fur/1.2)

        #Modify the result given player's role, weapontype, and brotherhood
        role = await AssetCreation.getClass(self.client.pg_con, ctx.author.id)
        if role == 'Hunter':
            gold *= 2
            fur *= 2
            bone *= 2

        if await AssetCreation.check_for_map_control_bonus(self.client.pg_con, ctx.author.id):
            gold = int(gold * 1.5)
            fur = int(fur * 1.5)
            bone = int(bone * 1.5)

        item_id = await AssetCreation.getEquippedItem(self.client.pg_con, ctx.author.id)
        item_info = await AssetCreation.getItem(self.client.pg_con, item_id)
        if item_info['Type'] == 'Bow':
            gold *= 2
            fur *= 2
            bone *= 2
        elif item_info['Type'] == 'Gauntlets':
            gold = int(gold / 2)
            fur = int(fur / 2)
            bone = int(bone / 2)
        elif item_info['Type'] ==  'Sling':
            gold = int(gold * 1.5)
            fur = int(fur * 1.5)
            bone = int(bone * 1.5)
        elif item_info['Type'] ==  'Javelin':
            gold = int(gold * 1.25)
            fur = int(fur * 1.25)
            bone = int(bone * 1.25)

        await AssetCreation.giveGold(self.client.pg_con, gold, ctx.author.id)
        await AssetCreation.giveMat(self.client.pg_con, 'fur', fur, ctx.author.id)
        await AssetCreation.giveMat(self.client.pg_con, 'bone', bone, ctx.author.id)

        await ctx.reply(f'Your hunting trip was a {result[0]}! You got `{gold}` gold, `{fur}` furs, and `{bone}` bones.')

    @commands.command(description='Mine for ore. You may get iron or silver, which is needed to buff your acolytes.')
    @commands.check(Checks.is_player)
    @cooldown(1, 10, type=BucketType.user)
    async def mine(self, ctx):
        """Mine for ore, gaining iron and silver, materials that buff certain acolytes.
        The amount of materials you gain is affected by your weapontype:
        Trebuchet: 100% bonus
        Greatsword, Axe, Mace: 25% bonus
        Dagger: 50% nerf
        Bow, Sling: 66% nerf
        """
        #Make sure they're in mining territory
        location = await AssetCreation.getLocation(self.client.pg_con, ctx.author.id)
        biome = location_dict[location]['Biome']
        if biome != 'Hills': # These are the biomes you can hunt in
            await ctx.reply(f'You cannot mine at {location}. Move to a hills biome.')
            return

        #Otherwise calc
        result = random.choices(['success', 'critical success', 'failure'], [45,35,20])
        if result[0] == 'success':
            gold = random.randint(20,100)
            iron = random.randint(40,80)
            silver = random.randint(18,25)

        elif result[0] == 'critical success':
            gold = random.randint(100, 150)
            iron = random.randint(80,100)
            silver = random.randint(30,45)

        else:
            gold = random.randint(10,30)
            iron = random.randint(25,35)
            silver = random.randint(2,8)

        #Modify rewards given player's class and weapontype
        role = await AssetCreation.getClass(self.client.pg_con, ctx.author.id)
        if role == 'Blacksmith':
            gold *= 2
            iron *= 2
            silver *= 2

        if await AssetCreation.check_for_map_control_bonus(self.client.pg_con, ctx.author.id):
            gold = int(gold * 1.5)
            iron = int(iron * 1.5)
            silver = int(silver * 1.5)

        item_id = await AssetCreation.getEquippedItem(self.client.pg_con, ctx.author.id)
        item_info = await AssetCreation.getItem(self.client.pg_con, item_id)
        if item_info['Type'] == 'Dagger':
            gold = int(gold / 2)
            iron = int(iron / 2)
            silver = int(silver / 2)
        elif item_info['Type'] == 'Bow' or item_info['Type'] == 'Sling':
            gold = int(gold / 3)
            iron = int(iron / 3)
            silver = int(silver / 3)
        elif item_info['Type'] == 'Trebuchet':
            gold = int(gold * 2)
            iron = int(iron * 2)
            silver = int(silver * 2)
        elif item_info['Type'] == 'Greatsword' or item_info['Type'] == 'Axe' or item_info['Type'] == 'Mace':
            gold = int(gold * 1.25)
            iron = int(iron * 1.25)
            silver = int(silver * 1.25)

        await AssetCreation.giveGold(self.client.pg_con, gold, ctx.author.id)
        await AssetCreation.giveMat(self.client.pg_con, 'iron', iron, ctx.author.id)
        await AssetCreation.giveMat(self.client.pg_con, 'silver', silver, ctx.author.id)

        await ctx.reply(f'Your mining expedition was a {result[0]}! You got `{gold}` gold, `{iron}` iron, and `{silver}` silver.')

    @commands.command(description='Forage for materials depending on your location. These materials may buff your acolytes.')
    @commands.check(Checks.is_player)
    @cooldown(1, 10, type=BucketType.user)
    async def forage(self, ctx):
        """Forage for food, gaining different materials depending on your location.
        Having a dagger equipped will net you 10% more rewards.
        """
        #Get player location and materials.
        location = await AssetCreation.getLocation(self.client.pg_con, ctx.author.id)
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
            amount = random.randint(7,12)

        #Modify result given player's role and weapon type
        role = await AssetCreation.getClass(self.client.pg_con, ctx.author.id)
        if role == 'Traveler':
            amount *= 2

        if await AssetCreation.check_for_map_control_bonus(self.client.pg_con, ctx.author.id):
            amount = int(amount * 1.5)

        item_id = await AssetCreation.getEquippedItem(self.client.pg_con, ctx.author.id)
        item_info = await AssetCreation.getItem(self.client.pg_con, item_id)
        if item_info['Type'] == 'Dagger':
            amount = int(amount * 1.1)

        await AssetCreation.giveMat(self.client.pg_con, mat, amount, ctx.author.id)

        await ctx.reply(f'You received `{amount} {mat}` while foraging in `{location}`.')

    @commands.command(aliases=['pack'], description='See how many materials you have.')
    @commands.check(Checks.is_player)
    async def backpack(self, ctx):
        """See the resources you currently possess."""
        mats = ('Fur', 'Bone', 'Iron', 'Silver', 'Wood', 'Wheat', 'Oat', 'Reeds', 'Pine', 'Moss', 'Cacao')
        backpack = []

        for resource in mats:
            backpack.append(await AssetCreation.getPlayerMat(self.client.pg_con, resource.lower(), ctx.author.id))

        embed = discord.Embed(title='Your Backpack', color=self.client.ayesha_blue)
        for i in range(len(backpack)):
            embed.add_field(name=f'{mats[i]}', value=f'{backpack[i]}')
       
        await ctx.reply(embed=embed)

    @commands.command(description='Fish for food.')
    @commands.check(Checks.is_player)
    @cooldown(1,10,type=BucketType.user)
    async def fish(self, ctx):
        """Fish for food."""
        #Fishing only in Thenuille
        location = await AssetCreation.getLocation(self.client.pg_con, ctx.author.id)
        if location != 'Thenuille':
            await ctx.reply('You can\'t fish here. Go to Thenuille.')
            return

        result = random.choices(['🐟','🐠','🐡','🦈','🦦','nothing'], [35, 20, 3, 1, 1, 40])
        fish = result[0]

        if fish == 'nothing':
            await ctx.reply('You waited but didn\'t catch anything.')
        elif fish == '🦦':
            await AssetCreation.giveGold(self.client.pg_con, 1, ctx.author.id)
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
            
            await AssetCreation.giveGold(self.client.pg_con, gold, ctx.author.id)
            await ctx.reply(f'You caught a {fish}! You sold your prize for `{gold}` gold.')

    @commands.command(brief='<item id>', description='Upgrade the ATK stat of a weapon.')
    @commands.check(Checks.is_player)
    @cooldown(1,90,type=BucketType.user)
    async def upgrade(self, ctx, item_id : int = None):
        """`item_id`: the ID of the item you are upgrading

        Upgrade the ATK stat of a weapon. The cost of upgrading is `3*(ATK+1)` iron and `20*(ATK+1)` gold. This cost is halved if you are a blacksmith.
        Weapons of a rarity can also only be upgraded to a certain value:\n**Common:** 50\n**Uncommon:** 75\n**Rare:** 100\n**Epic:** 125\n**Legendary:** 160
        """
        if item_id is None:
            embed = discord.Embed(title='Upgrade', color=self.client.ayesha_blue)
            embed.add_field(name='Upgrade an item\'s attack stat by 1.', value='The cost of upgrading scales with the attack of the item. You will have to pay `3*(ATK+1)` iron and `20*(ATK+1)` gold to upgrade an item\'s ATK stat.\nEach rarity also has a maximum ATK:\n**Common:** 50\n**Uncommon:** 75\n**Rare:** 100\n**Epic:** 125\n**Legendary:** 160\n`Upgrade` has a 90 second cooldown.')
            ctx.command.reset_cooldown(ctx)
            return await ctx.reply(embed=embed)

        #Upgrade only in Cities or Towns
        location = await AssetCreation.getLocation(self.client.pg_con, ctx.author.id)
        if location != 'Thenuille' and location != 'Aramithea' and location != 'Riverburn':
            ctx.command.reset_cooldown(ctx)
            return await ctx.reply('You can only upgrade your items in an urban center!')

        #Make sure the item exists and that they own it
        item_is_valid = await AssetCreation.verifyItemOwnership(self.client.pg_con, item_id, ctx.author.id)
        if not item_is_valid:
            ctx.command.reset_cooldown(ctx)
            return await ctx.reply("No such item of yours exists.")

        item = await AssetCreation.getItem(self.client.pg_con, item_id)

        #Get the item's rarity and prevent them from upgrading it past the limit (50 for commons, +25 for each above)
        if item['Rarity'] == 'Common':
            if item['Attack'] >= 50:
                await ctx.reply('A common weapon can have a maximum ATK stat of 50.')
                ctx.command.reset_cooldown(ctx)
                return

        elif item['Rarity'] == 'Uncommon':
            if item['Attack'] >= 75:
                await ctx.reply('An uncommon weapon can have a maximum ATK stat of 75.')
                ctx.command.reset_cooldown(ctx)
                return

        elif item['Rarity'] == 'Rare':
            if item['Attack'] >= 100:
                await ctx.reply('A rare weapon can have a maximum ATK stat of 100.')
                ctx.command.reset_cooldown(ctx)
                return

        elif item['Rarity'] == 'Epic':
            if item['Attack'] >= 125:
                await ctx.reply('An epic weapon can have a maximum ATK stat of 125.')
                ctx.command.reset_cooldown(ctx)
                return

        elif item['Rarity'] == 'Legendary':
            if item['Attack'] >= 160:
                await ctx.reply('A legendary weapon can have a maximum ATK stat of 160.')
                ctx.command.reset_cooldown(ctx)
                return

        #Ensure they have the ore and gold to upgrade this weapon
        #Upgrade costs: 3 * (ATK + 1) iron; 20 * (ATK + 1) gold; halved if blacksmith
        role = await AssetCreation.getClass(self.client.pg_con, ctx.author.id)
        if role == 'Blacksmith':
            iron_cost = int(1.5 * (item['Attack'] + 1))
            gold_cost = 10 * (item['Attack'] + 1)
        else:
            iron_cost = 3 * (item['Attack'] + 1)
            gold_cost = 20 * (item['Attack'] + 1)

        gold = await AssetCreation.getGold(self.client.pg_con, ctx.author.id)
        iron = await AssetCreation.getPlayerMat(self.client.pg_con, 'iron', ctx.author.id)
            
        if gold < gold_cost or iron < iron_cost:
            await ctx.reply(f"Upgrading this item to `{item['Attack']+1}` ATK costs `{iron_cost}` iron and `{gold_cost}` gold. You don\'t have enough resources.")
            ctx.command.reset_cooldown(ctx)
            return

        #Upgrade the weapon
        await AssetCreation.increaseItemAttack(self.client.pg_con, item_id, 1)
        await AssetCreation.giveGold(self.client.pg_con, 0 - gold_cost, ctx.author.id)
        await AssetCreation.giveMat(self.client.pg_con, 'iron', 0 - iron_cost, ctx.author.id)
        await ctx.reply(f"Success! You consumed `{gold_cost}` gold and `{iron_cost}` iron to upgrade your `{item['Name']}` to `{item['Attack']+1}` ATK.")

    @commands.command(description='Work a shift at a nearby shoppe to gain some cash.')
    @commands.check(Checks.is_player)
    @cooldown(1, 7200, type=BucketType.user)
    async def work(self, ctx):
        """Get a short gig in town, making some money."""
        #Upgrade only in Cities or Towns
        location = await AssetCreation.getLocation(self.client.pg_con, ctx.author.id)
        if location != 'Thenuille' and location != 'Aramithea' and location != 'Riverburn':
            await ctx.reply('You can only work in an urban center!')
            ctx.command.reset_cooldown(ctx)
            return

        #Choose random workplace and gold amount
        workplaces = ('blacksmith', 'cartographer\'s study', 'library', 'manor', 'doctor\'s office', 'carpenter\'s studio', 'farm', 'general goods store', 'bar')
        workplace = random.choice(workplaces)

        gold_made = random.randint(1,10)
        if gold_made == 10:
            gold = random.randint(10000, 20000)
        else:
            gold = random.randint(2000,10000)

        await AssetCreation.giveGold(self.client.pg_con, gold, ctx.author.id)

        #Send output
        await ctx.reply(f'You worked at the local {workplace} and made `{gold}` gold.')

def setup(client):
    client.add_cog(Travel(client))