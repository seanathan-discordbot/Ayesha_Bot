import discord
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

from Utilities import Checks, AssetCreation, Links

import asyncio
import asyncpg
from datetime import date, datetime
import schedule

class Map(commands.Cog):
    def __init__(self,client):
        self.client=client

        def offices_func():
            asyncio.run_coroutine_threadsafe(select_offices(), self.client.loop)

        async def select_offices():
            async with self.client.pg_con.acquire() as conn:
                await conn.execute("""
                                    WITH gravitas_leader AS (
                                        SELECT user_id 
                                        FROM players
                                        WHERE guild IN (SELECT guild_id FROM guilds WHERE guild_type = 'College')
                                        ORDER BY gravitas DESC
                                        LIMIT 1
                                    )
                                    INSERT INTO officeholders (officeholder, office)
                                    VALUES ((SELECT user_id FROM gravitas_leader), 'Mayor');""")

                await conn.execute("""
                                    WITH guild_gold_leader AS (
                                        SELECT user_id
                                        FROM players
                                        WHERE guild IN (SELECT guild_id FROM guilds WHERE guild_type = 'Guild')
                                        ORDER BY gold DESC
                                        LIMIT 1
                                    )
                                    INSERT INTO officeholders (officeholder, office)
                                    VALUES ((SELECT user_id FROM guild_gold_leader), 'Comptroller');""")

                await self.client.pg_con.release(conn)

        async def weekly_offices():
            schedule.every().sunday.at("12:00").do(offices_func)
            while True:
                schedule.run_pending()
                print(f'{date.today()}: Selecting new officeholders...')
                await asyncio.sleep(schedule.idle_seconds())

        asyncio.ensure_future(weekly_offices())

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('Map is ready.')

    #COMMANDS
    @commands.command()
    @commands.check(Checks.is_player)
    async def offices(self, ctx):
        officeholders = await AssetCreation.get_officeholders(self.client.pg_con)
        mayor = await self.client.fetch_user(officeholders['Mayor_ID'])
        comptroller = await self.client.fetch_user(officeholders['Comptroller_ID'])

        embed = discord.Embed(title = f"The Week of {officeholders['Mayor_Term']}",
                              color = self.client.ayesha_blue)
        embed.add_field(name='Mayor',
                        value=f"{officeholders['Mayor']} ({mayor.mention})")
        embed.add_field(name='Comptroller',
                        value=f"{officeholders['Comptroller']} ({comptroller.mention})")

        await ctx.reply(embed=embed)

    @commands.command(brief = '<tax_rate : 0-9.99>',
                      description = 'The mayor can set the tax rate over Aramithea, earning a small percentage of all taxes collected over their term. The tax rate must be within the range of 0 - 9.99%.')
    @commands.check(Checks.is_mayor)
    @cooldown(1, 43200, type=BucketType.user)
    async def settax(self, ctx, tax_rate : float):
        #Check for valid input
        tax_rate = round(tax_rate, 2)

        if tax_rate > 9.99:
            return await ctx.reply('The maximum tax rate is 9.99%.')

        if tax_rate < 0:
            return await ctx.reply('The minimum tax rate is 0%.')

        #Set new tax rate
        await AssetCreation.set_tax_rate(self.client.pg_con, tax_rate, ctx.author.id)
        await ctx.reply(f'Mayor! You have set the new tax-rate to `{tax_rate}`%!')

    @commands.command(description='See the current tax rate!')
    async def tax(self, ctx):
        tax_info = await AssetCreation.get_tax_info(self.client.pg_con)
        await ctx.reply(f"The current tax rate is `{tax_info['tax_rate']}%`, set by Mayor `{tax_info['user_name']}` on `{tax_info['setdate'].date()}`\nThe mayor has collected `{tax_info['Total_Collection']}` gold so far this term.")

def setup(client):
    client.add_cog(Map(client))