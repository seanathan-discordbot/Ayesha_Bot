import discord
import asyncio

from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

import aiosqlite
from Utilities import Checks, AssetCreation, PageSourceMaker

import random
import math
import time

PATH = 'PATH'

location_dict = {
    'Aramithea' : {'Biome' : 'City', 'CD' : 1800},
    'Mythic Forest' : {'Biome' : 'Forest', 'CD' : 3600}, 
    'Thenuille' : {'Biome' : 'Town', 'CD' : 1800},
    'Fernheim' : {'Biome' : 'Grassland', 'CD' : 1800},
    'Sunset Prairie' : {'Biome' : 'Grassland', 'CD' : 3600},
    'Riverburn' : {'Biome' : 'City', 'CD' : 3600},
    'Thanderlans' : {'Biome' : 'Marsh', 'CD' : 7200},
    'Glakelys' : {'Biome' : 'Grassland', 'CD' : 3600},
    'Russe' : {'Biome' : 'Taiga', 'CD' : 12600},
    'Croire' : { 'Biome' : 'Grassland', 'CD' : 9000},
    'Crumidia' : {'Biome' : 'Hills', 'CD' : 10800},
    'Kucre' : {'Biome' : 'Jungle', 'CD' : 14400}
}

class Travel(commands.Cog):

    def __init__(self, client):
        self.client = client

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('Travel is ready.')

    @commands.command(brief='<destination>', description='Travel to another area of the map, unlocking a different subset of commands.')
    @commands.check(Checks.is_player)
    async def travel(self, ctx, *, destination):
        adv = await AssetCreation.getAdventure(ctx.author.id)
        if adv[0] is not None:
            await ctx.reply('You are currently traveling. Please wait until you arrive at your destination before traveling again.')
            return

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

    @commands.command()
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

    def convertagain(self, seconds : int):
        return time.strftime("%H:%M:%S", time.gmtime(seconds))
       
def setup(client):
    client.add_cog(Travel(client))