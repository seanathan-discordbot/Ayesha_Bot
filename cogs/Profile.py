import discord
import asyncio

from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

from Utilities import Checks, AssetCreation, Links, PageSourceMaker

import asyncpg
import math
import schedule
from datetime import date

class YesNo(menus.Menu):
    def __init__(self, ctx, embed):
        super().__init__(timeout=15.0, delete_message_after=True)
        self.embed = embed
        self.result = None
        
    async def send_initial_message(self, ctx, channel):
        return await channel.send(embed=self.embed)
    
    async def prompt(self, ctx):
        await self.start(ctx, wait=True)
        return self.result
    
    @menus.button('\u2705') # Check mark
    async def on_yes(self, payload):
        self.result = True
        self.stop()
        
    @menus.button('\u274E') # X
    async def on_no(self, payload):
        self.result = False
        self.stop() 

class Profile(commands.Cog):
    """Create a character and view your stats!"""

    def __init__(self, client):
        self.client = client

        def gravitas_func():
            asyncio.run_coroutine_threadsafe(update_gravitas(), self.client.loop)

        async def update_gravitas():
            async with self.client.pg_con.acquire() as conn:
                # Decay current gravitas first. 10% for all, and 10% more for people not in the cities
                await conn.execute("UPDATE players SET gravitas = gravitas - (gravitas / 10);") 
                await conn.execute("""
                                    UPDATE players SET 
                                        gravitas = gravitas - (gravitas / 10) WHERE loc != 'Aramithea'
                                            AND loc != 'Riverburn'
                                            AND loc != 'Thenuille';""")
                # Class bonuses: 3 Farmer, 1 Soldier or Scribe
                await conn.execute("UPDATE players SET gravitas = gravitas + 3 WHERE occupation = 'Farmer';")
                await conn.execute("""
                                    UPDATE players SET
                                        gravitas = gravitas + 1 WHERE occupation = 'Soldier' 
                                            OR occupation = 'Scribe';""")
                # Origin bonuses: 5 for Aramithea, 3 for cities, 1 for various other areas
                await conn.execute("UPDATE players SET gravitas = gravitas + 5 WHERE origin = 'Aramithea';")
                await conn.execute("""
                                    UPDATE players SET 
                                        gravitas = gravitas + 3 WHERE origin = 'Riverburn'
                                            OR origin = 'Thenuille';""")
                await conn.execute("""
                                    UPDATE players SET
                                        gravitas = gravitas + 1 WHERE origin = 'Mythic Forest'
                                            OR origin = 'Lunaris'
                                            OR origin = 'Crumidia';""")
                # 2 for Ajar + Duchess users
                await conn.execute("""
                                    WITH ajar_users AS(
                                        WITH acolyte_1 AS (
                                            SELECT players.user_id, players.user_name, acolytes.acolyte_name
                                            FROM players
                                            INNER JOIN acolytes ON players.acolyte1 = acolytes.instance_id
                                            WHERE acolytes.acolyte_name = 'Ajar'
                                        ),
                                        acolyte_2 AS (
                                            SELECT players.user_id, players.user_name, acolytes.acolyte_name
                                            FROM players
                                            INNER JOIN acolytes ON players.acolyte2 = acolytes.instance_id
                                            WHERE acolytes.acolyte_name = 'Ajar'
                                        )
                                        SELECT * FROM acolyte_1
                                        UNION
                                        SELECT * FROM acolyte_2
                                    )
                                    UPDATE players
                                    SET gravitas = gravitas + 2
                                    WHERE user_id IN (SELECT user_id FROM ajar_users)""")
                await conn.execute("""
                                    WITH duchess_users AS(
                                        WITH acolyte_1 AS (
                                            SELECT players.user_id, players.user_name, acolytes.acolyte_name
                                            FROM players
                                            INNER JOIN acolytes ON players.acolyte1 = acolytes.instance_id
                                            WHERE acolytes.acolyte_name = 'Duchess'
                                        ),
                                        acolyte_2 AS (
                                            SELECT players.user_id, players.user_name, acolytes.acolyte_name
                                            FROM players
                                            INNER JOIN acolytes ON players.acolyte2 = acolytes.instance_id
                                            WHERE acolytes.acolyte_name = 'Duchess'
                                        )
                                        SELECT * FROM acolyte_1
                                        UNION
                                        SELECT * FROM acolyte_2
                                    )
                                    UPDATE players
                                    SET gravitas = gravitas + 2
                                    WHERE user_id IN (SELECT user_id FROM duchess_users)""")

                # 7 for college members
                await conn.execute("""
                                    WITH colleges AS (
                                        SELECT DISTINCT players.guild
                                        FROM players
                                        INNER JOIN guilds
                                            ON players.guild = guilds.guild_id
                                        WHERE guilds.guild_type = 'College'
                                    )
                                    UPDATE players
                                    SET gravitas = gravitas + 7
                                    WHERE guild IN (SELECT guild FROM colleges);""")

                await self.client.pg_con.release(conn)

        async def daily_gravitas():
            gravscheduler = schedule.Scheduler()
            gravscheduler.every().day.at("12:00").do(gravitas_func)
            while True:
                gravscheduler.run_pending()
                print(f'{date.today()}: Updating gravitas...')
                await asyncio.sleep(gravscheduler.idle_seconds)

        asyncio.ensure_future(daily_gravitas())

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('Profile is ready.')

    #COMMANDS
    @commands.command(aliases=['begin','create','play'], 
                      brief='<name : str>', 
                      description='Start the game of AyeshaBot.')
    @commands.check(Checks.not_player)
    async def start(self, ctx, *, name : str = None):
        """`name`: the name of your character

        Begin the game of Ayesha by creating a character!
        """
        if not name:
            name = ctx.author.display_name
        if len(name) > 32:
                await ctx.send("Name can only be up to 32 characters")
        else:
            prefix = await self.client.get_prefix(ctx.message)
            embed = discord.Embed(title='Start the game of AyeshaBot?', color=self.client.ayesha_blue)
            embed.add_field(name=f'Your Name: {name}', 
                            value=f'You can customize your name by doing `{prefix}start <name>`')
            start = await YesNo(ctx, embed).prompt(ctx)
            if start:
                await ctx.send(f'Your Name: {name}')
                await AssetCreation.createCharacter(self.client.pg_con, ctx.author.id, name)
                await ctx.reply("Success! Use the `tutorial` command to get started!")  

    @commands.command(aliases=['p'], description='View your profile')
    async def profile(self, ctx, player : commands.MemberConverter = None):
        """`player`: the player whose profile you want to see. Defaults to your own if none is given

        View your or any other player's profile!
        """
        # Make sure targeted person is a player
        if player is None: #return author profile
            if not await Checks.has_char(self.client.pg_con, ctx.author):
                await ctx.reply('You don\'t have a character. Do `start` to make one!')
                return
            else:
                player = ctx.author
        else:
            if not await Checks.has_char(self.client.pg_con, player):
                await ctx.reply('This person does not have a character')
                return
        # Otherwise target is a player and we can access their profile
        attack, crit = await AssetCreation.getAttack(self.client.pg_con, player.id)
        character = await AssetCreation.getPlayerByID(self.client.pg_con, player.id)

        #Calc pvp and boss wins. If 0, hardcode to 0 to prevent div 0
        if character['pvpfights'] == 0: 
            pvpwinrate = 0
        else:
            pvpwinrate = character['pvpwins']/character['pvpfights']*100
        if character['bossfights'] == 0:
            bosswinrate = 0
        else:
            bosswinrate = character['bosswins']/character['bossfights']*100

        try:
            item = await AssetCreation.getEquippedItem(self.client.pg_con, player.id)
            item = await AssetCreation.getItem(self.client.pg_con, item)
        except TypeError:
            item = None

        if character['Guild'] is not None:
            guild = await AssetCreation.getGuildByID(self.client.pg_con, character['Guild'])
        else:
            guild = {'Name' : 'None'}

        #Create the strings for acolytes
        if character['Acolyte1'] is not None:
            acolyte1 = await AssetCreation.getAcolyteByID(self.client.pg_con, character['Acolyte1'])
            acolyte1 = f"{acolyte1['Name']} ({acolyte1['Rarity']}⭐)"
        else:
            acolyte1 = None

        if character['Acolyte2'] is not None:   
            acolyte2 = await AssetCreation.getAcolyteByID(self.client.pg_con, character['Acolyte2'])
            acolyte2 = f"{acolyte2['Name']} ({acolyte2['Rarity']}⭐)"
        else:
            acolyte2 = None

        #Create Embed
        embed = discord.Embed(title=f"{player.display_name}\'s Profile: {character['Name']} ({character['prestige']} \u2604)", 
                              color=self.client.ayesha_blue)
        embed.set_thumbnail(url=f'{player.avatar_url}')
        embed.add_field(
            name='Character Info',
            value=f"Gold: `{character['Gold']}`\nClass: `{character['Class']}`\nOrigin: `{character['Origin']}`\nLocation: `{character['Location']}`\nAssociation: `{guild['Name']}`",
            inline=True)
        embed.add_field(
            name='Character Stats',
            value=f"Level: `{character['Level']}`\nGravitas: `{character['gravitas']}`\nAttack: `{attack}`\nCrit: `{crit}%`\nPvP Winrate: `{pvpwinrate:.0f}%`\nBoss Winrate: `{bosswinrate:.0f}%`",
            inline=True)
        if item is not None:
            embed.add_field(
                name='Party',
                value=f"Item: `{item['Name']} ({item['Rarity']})`\nAcolyte: `{acolyte1}`\nAcolyte: `{acolyte2}`",
                inline=True)
        else:
            embed.add_field(
                name='Party',
                value=f"Item: `None`\nAcolyte: `{acolyte1}`\nAcolyte: `{acolyte2}`",
                inline=True)
        
        await ctx.reply(embed=embed)

    @commands.command(aliases=['e', 'econ', 'economy', 'wallet'], description='See how much gold you have.')
    @commands.check(Checks.is_player)
    async def gold(self, ctx):
        """See how much gold you have."""
        gold = await AssetCreation.getGold(self.client.pg_con, ctx.author.id)
        await ctx.reply(f'You have `{gold}` gold.')

    @commands.command(aliases=['xp'], description='Check your xp and level.')
    @commands.check(Checks.is_player)
    async def level(self, ctx):
        """See your current level, xp, and distance from levelling up."""
        level, xp = await AssetCreation.getPlayerXP(self.client.pg_con, ctx.author.id)
        prestige = await AssetCreation.getPrestige(self.client.pg_con, ctx.author.id)
        w = 600 + (25 * prestige)
        tonext = int(w * ((level+1)**2)) - xp

        embed = discord.Embed(color=self.client.ayesha_blue)
        embed.add_field(name='Level', value=f'{level}')
        embed.add_field(name='EXP', value=f'{xp}')
        if level != 100:
            embed.add_field(name=f'EXP until Level {level+1}', value=f'{tonext}')
        else:
            embed.add_field(name=f'EXP until Level {level+1}', value='∞')
        await ctx.reply(embed=embed)

    @commands.command(brief='<name>', description='Change your character name.')
    @commands.check(Checks.is_player)
    async def rename(self, ctx, *, name):
        """`name`: your new name (max 32 characters)
        
        Change your character name.
        """
        if len(name) > 32:
            await ctx.reply('Name max 32 characters.')
            return
        await AssetCreation.setPlayerName(self.client.pg_con, ctx.author.id, name)
        await ctx.reply(f'Name changed to `{name}`.')

    @commands.command(description='Rebirth your character, resetting their level and giving them 30 attack and 50 HP.')
    @commands.check(Checks.is_player)
    async def prestige(self, ctx):
        """Rebirth your character, resetting their level and giving them 30 attack and 50 HP."""
        #Make sure player is lvl 100
        level = await AssetCreation.getLevel(self.client.pg_con, ctx.author.id)
        if level < 100:
            await ctx.reply('You can only prestige at level 100.')
            return

        #Reset level, gold, resources
        await AssetCreation.resetPlayerLevel(self.client.pg_con, ctx.author.id)
        await AssetCreation.setGold(self.client.pg_con, ctx.author.id, 0)
        await AssetCreation.resetResources(self.client.pg_con, ctx.author.id)

        #Give 10 rubidics and add 1 to prestige
        await AssetCreation.giveRubidics(self.client.pg_con, 10, ctx.author.id)
        prestige = await AssetCreation.prestigeCharacter(self.client.pg_con, ctx.author.id)

        #Send response
        await ctx.reply(f"Successfully reset your character! You are now prestige {prestige}!")

    #Add a tutorial command at the end of alpha
    @commands.group(description='Learn the game.', case_insensitive=True, invoke_without_command=True)
    async def tutorial(self, ctx):
        """Learn the game."""
        with open(Links.tutorial, "r") as f:
            tutorial = f.readlines()

        embed1 = discord.Embed(title='Ayesha Tutorial', color=self.client.ayesha_blue)
        embed1.add_field(name='Welcome to Ayesha Alpha!', 
                         value=f"{tutorial[1]}\n{tutorial[2]}\n{tutorial[3]}")

        embed2 = discord.Embed(title='Ayesha Tutorial', color=self.client.ayesha_blue)
        embed2.add_field(name='Intro to PvE', 
                         value=f'{tutorial[6]}\n{tutorial[7]}\n{tutorial[8]}\n{tutorial[9]}')

        embed3 = discord.Embed(title='Ayesha Tutorial', color=self.client.ayesha_blue)
        embed3.add_field(name='Intro to Gacha', 
                         value=f'{tutorial[12]}\n{tutorial[13]}')

        tutorial_pages = menus.MenuPages(source=PageSourceMaker.PageMaker([embed1, embed2, embed3]), 
                                         clear_reactions_after=True, 
                                         delete_message_after=True)
        await tutorial_pages.start(ctx)

    @tutorial.command(aliases=['acolyte'], description='Learn more about Acolytes!')
    async def Acolytes(self, ctx):
        """Learn the game."""
        with open(Links.tutorial, "r") as f:
            tutorial = f.readlines()

        embed1 = discord.Embed(title='Ayesha Tutorial: Acolytes', color=self.client.ayesha_blue)
        embed1.add_field(name='Welcome to Ayesha Alpha!', value=f"{tutorial[16]}\n{tutorial[17]}\n{tutorial[18]}")

        embed2 = discord.Embed(title='Ayesha Tutorial: Acolytes', color=self.client.ayesha_blue)
        embed2.add_field(name='The Tavern and Effects', value=f'{tutorial[21]}\n{tutorial[22]}\n{tutorial[23]}')

        embed3 = discord.Embed(title='Ayesha Tutorial: Acolytes', color=self.client.ayesha_blue)
        embed3.add_field(name='Strengthening your Acolytes', 
                         value=f'{tutorial[26]}\n{tutorial[27]}\n{tutorial[28]}\n{tutorial[29]}')

        tutorial_pages = menus.MenuPages(source=PageSourceMaker.PageMaker([embed1, embed2, embed3]), 
                                         clear_reactions_after=True, 
                                         delete_message_after=True)
        await tutorial_pages.start(ctx)

    @tutorial.command(aliases=['item', 'weapon', 'weapons'], description='Learn more about Items!')
    async def Items(self, ctx):
        """Learn the game."""
        with open(Links.tutorial, "r") as f:
            tutorial = f.readlines()

        embed1 = discord.Embed(title='Ayesha Tutorial: Items', color=self.client.ayesha_blue)
        embed1.add_field(name='Everything on Items', 
                         value=f"{tutorial[32]}\n{tutorial[33]}\n{tutorial[34]}\n{tutorial[35]}")

        await ctx.reply(embed=embed1)

    @tutorial.command(description='Learn more about PvE!')
    async def pve(self, ctx):
        """Learn the game."""
        with open(Links.tutorial, "r") as f:
            tutorial = f.readlines()

        embed1 = discord.Embed(title='Ayesha Tutorial: PvE', color=self.client.ayesha_blue)
        embed1.add_field(name='Everything on PvE', 
                         value=f"{tutorial[38]}\n{tutorial[39]}\n{tutorial[40]}\n{tutorial[41]}\n{tutorial[42]}\n{tutorial[43]}")

        await ctx.reply(embed=embed1)

    @tutorial.command(description='Learn more about Travel!')
    async def Travel(self, ctx):
        """Learn the game."""
        with open(Links.tutorial, "r") as f:
            tutorial = f.readlines()

        embed1 = discord.Embed(title='Ayesha Tutorial: Travel', color=self.client.ayesha_blue)
        embed1.add_field(name='Everything on Travel', 
                         value=f"{tutorial[46]}\n{tutorial[47]}\n{tutorial[48]}\n{tutorial[49]}")

        await ctx.reply(embed=embed1)

def setup(client):
    client.add_cog(Profile(client))