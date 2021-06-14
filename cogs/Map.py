import discord
from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

from Utilities import Checks, AssetCreation, Links, PageSourceMaker

import asyncio
import asyncpg
from datetime import date, datetime
import schedule

bh_areas = ('Mythic Forest', 'Fernheim', 'Sunset Prairie', 'Thanderlans', 'Glakelys', 'Russe', 'Croire', 'Crumidia', 'Kucre')

class Map(commands.Cog):
    def __init__(self,client):
        self.client=client

        def offices_func():
            asyncio.run_coroutine_threadsafe(select_offices(), self.client.loop)

        async def select_offices():
            async with self.client.pg_con.acquire() as conn:
                #Give payout to the mayor and comptroller
                current = await AssetCreation.get_officeholders(self.client.pg_con)
                tax_revenue = await AssetCreation.get_tax_info(self.client.pg_con)

                payout = int(tax_revenue['Total_Collection'] / 100)

                await AssetCreation.giveGold(self.client.pg_con, payout, current['Mayor_ID'])
                await AssetCreation.giveGold(self.client.pg_con, payout, current['Comptroller_ID'])

                #Select new mayor and gravitas
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

                #The comptroller bonus is NULL at the beginning of the term
                #The bonus is edited in the db when they change it. No new records are added.
                comptroller = await conn.fetchrow("""
                                                    SELECT officeholders.id, players.guild
                                                    FROM officeholders
                                                    LEFT JOIN players
                                                        ON officeholders.officeholder = players.user_id
                                                    WHERE office = 'Comptroller'
                                                    ORDER BY id DESC
                                                    LIMIT 1""")

                await conn.execute('INSERT INTO comptroller_bonuses (comptroller_id, guild_id) VALUES ($1, $2)', comptroller['id'], comptroller['guild'])

                await self.client.pg_con.release(conn)

        async def weekly_offices():
            schedule.every().friday.at("22:59").do(offices_func)
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
    @commands.command(description='See the map!')
    async def map(self, ctx):
        map_file = discord.File(Links.map_file)
        await ctx.reply(file=map_file)

    @commands.command(aliases=['te','territory'], description='See who controls the outlying areas of the `map`.')
    async def territories(self, ctx):
        control = []
        for area in bh_areas:
            guild_id = await AssetCreation.get_area_controller(self.client.pg_con, area)
            try:
                guild = await AssetCreation.getGuildByID(self.client.pg_con, guild_id)
            except TypeError: #No owner
                guild = {
                    'Name' : None
                }
            
            info = (area, guild['Name'], guild_id)

            control.append(info)

        embed = discord.Embed(title='Territories Controlled by a Brotherhood', 
                              description='Brotherhoods in control of a territory get a 50% bonus to rewards from `mine`, `forage`, and `hunt` in that territory.',
                              color=self.client.ayesha_blue)
        embed.set_footer(text="Try 'bh info <id>' to get a closer look at these brotherhoods!")

        for territory in control:
            if territory[1] is not None:
                embed.add_field(name=territory[0], value=f"{territory[1]} (ID: `{territory[2]}`)")
            else:
                embed.add_field(name=territory[0], value=f"{territory[1]}")

        await ctx.reply(embed=embed)

    @commands.command(description='Display whomever holds the offices of Mayor and Comptroller this week.')
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

    @commands.group(invoke_without_command=True, 
                    case_insensitive=True, 
                    description='See your college.')
    @commands.check(Checks.is_comptroller)
    async def invest(self, ctx):
        with open(Links.tutorial, "r") as f:
            tutorial = f.readlines()

            embed1 = discord.Embed(title='Ayesha Tutorial: Invest', 
                                   color=self.client.ayesha_blue,
                                   description = '```invest <type : combat/sales/travel>```')
            embed1.add_field(name='The Invest Command', value=f"{tutorial[58]}\n{tutorial[59]}\n{tutorial[60]}\n{tutorial[61]}\n{tutorial[62]}\n{tutorial[63]}")

            embed2 = discord.Embed(title='Ayesha Tutorial: Invest', color=self.client.ayesha_blue)
            embed2.add_field(name='Invest Enhance', value=f'{tutorial[66]}\n{tutorial[67]}\n{tutorial[68]}\n{tutorial[69]}')

            tutorial_pages = menus.MenuPages(source=PageSourceMaker.PageMaker([embed1, embed2]), 
                                            clear_reactions_after=True, 
                                            delete_message_after=True)
            await tutorial_pages.start(ctx)

    @invest.command(name='set', brief = 'type: combat/sales/travel', description='Select a bonus for your guild. Effect lasts until the end of your term and cannot be changed.')
    @commands.check(Checks.is_comptroller)
    async def _set(self, ctx, bonus : str):
        if bonus.lower() not in ('combat', 'sales', 'travel'):
            return await ctx.reply('The valid bonuses are `combat`, `sales`, and `travel`.')

        current_bonus = await AssetCreation.get_comptroller_bonus(self.client.pg_con)
        if current_bonus['is_set']: #Then its already set and cannot be changed
            return await ctx.reply('You cannot change your bonus once set.')

        await AssetCreation.set_comptroller_bonus(self.client.pg_con, bonus.lower())
        await ctx.reply(f'You gave you and your guildmates a {bonus.lower()} bonus for the rest of the week.\n`WARNING`: This cannot be changed.')

    @invest.command(brief='<money : int>', description='Enhance your bonus, 100,000 a level, up to 10 levels.')
    @commands.check(Checks.is_comptroller)
    async def enhance(self, ctx, money : int):
        #Check for valid input
        if money < 0:
            return await ctx.reply('Bruh.')

        bonus_info = await AssetCreation.get_comptroller_bonus(self.client.pg_con)
        if money > 1000000 - bonus_info['bonus_xp']:
            return await ctx.reply(f"You only need to contribute `{1000000 - bonus_info['bonus_xp']}` more gold to max out the bonus.")

        #Enhance the bonus
        await AssetCreation.giveGold(self.client.pg_con, money*-1, ctx.author.id)
        await AssetCreation.set_comptroller_bonus_xp(self.client.pg_con, money)
        current_xp = bonus_info['bonus_xp'] + money

        await ctx.reply(f'You enhanced your bonus. You have contributed a total of `{current_xp}` gold, which makes the bonus level {int(current_xp / 100000)}.')


def setup(client):
    client.add_cog(Map(client))