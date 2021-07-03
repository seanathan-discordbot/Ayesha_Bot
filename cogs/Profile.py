import discord
import asyncio

from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

from Utilities import Checks, AssetCreation, Links, PageSourceMaker
from Utilities.PageSourceMaker import PageMaker

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
                await conn.execute("UPDATE players SET gravitas = gravitas + 4 WHERE occupation = 'Farmer';")
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
        # attack, crit = await AssetCreation.getAttack(self.client.pg_con, player.id)
        combat_info = await AssetCreation.get_attack_crit_hp(self.client.pg_con, player.id)
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
            value=f"Level: `{character['Level']}`\nGravitas: `{character['gravitas']}`\nAttack: `{combat_info['Attack']}`\nCrit: `{combat_info['Crit']}%`\nHP: `{combat_info['HP']}`\nPvP Winrate: `{pvpwinrate:.0f}%`\nBoss Winrate: `{bosswinrate:.0f}%`",
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
        """Rebirth your character, resetting their level and upgrading their ATK and HP."""
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

    @commands.group(description='Learn the game.', case_insensitive=True, invoke_without_command=True)
    async def tutorial(self, ctx):
        """Learn the game."""
        p = ctx.prefix
        with open(Links.tutorial, "r") as f:
            tutorial = f.readlines()

        embed1 = discord.Embed(color=self.client.ayesha_blue)
        embed1.set_author(name='Ayesha Tutorial: Introduction', icon_url=self.client.user.avatar_url)
        embed1.set_thumbnail(url=ctx.author.avatar_url)

        embed1.add_field(name='Welcome to Ayesha, a new Gacha RPG for Discord!',
                         value=(f"**∘ |** **Create a character** by doing `{p}create <your name>`.\n"
                                f"**∘ |** **Customize** your playstyle with `{p}class` and `{p}origin`.\n"
                                f"**∘ |** View your **profile** with the `{p}profile` command!\n"
                                f"**∘ |** View your **weapons** with the `{p}inventory` command.\n"
                                f"**∘ |** View your **acolytes** with `{p}tavern`.\n"
                                f"**∘ |** Do `{p}pve <1-25>` to fight **bosses** and earn **rewards**!\n"
                                f"**∘ |** Get passive **resources** from `{p}travel` and `{p}expedition.\n`"
                                f"**∘ |** Make friends in `{p}brotherhood`s, `{p}college`s, or `{p}guild`s.\n\n"
                                f"Hit the ▶️ for a quick walkthrough!\n"
                                f"Still stuck? Use the `{p}help` command!"))

        embed2 = discord.Embed(color=self.client.ayesha_blue)
        embed2.set_author(name='Ayesha Tutorial: Introduction', icon_url=self.client.user.avatar_url)
        embed2.set_thumbnail(url=ctx.author.avatar_url)

        embed2.add_field(name="Ayesha's Stat System",
                         value=(f"**You will be seeing a bunch of terms thrown all over the game. "
                                f"Here's a quick overview:**\n"
                                f"**∘ | Gold:** the base currency for Ayesha, used for most anything in the game.\n"
                                f"**∘ | Rubidics:** rubidics are the **gacha** currency for Ayesha. "
                                f"That means it is entirely separate from gameplay, and used only for `{p}summon`ing.\n"
                                f"**∘ | Level:** your character's level, which can be increased by a few important commands.\n"
                                f"**∘ | Attack:** your character's attack. It can be increased based"
                                f"off your weapon, acolytes, class, origin, and association.\n"
                                f"**∘ | Crit:** like Attack, but denoting your critical strike chance.\n"
                                f"**∘ | HP:** your hit points, used in `{p}pvp` and `{p}pve`.\n"
                                f"**∘ | Gravitas:** Your **reputation** or **influence** in the bot, "
                                f"an alternative stat to raise for those not interested by combat.\n\n"
                                f"Hit the ▶️ for your first steps!\n"
                                f"Still stuck? Join the `{p}support` server for help!"))

        embed3 = discord.Embed(color=self.client.ayesha_blue)
        embed3.set_author(name='Ayesha Tutorial: Introduction', icon_url=self.client.user.avatar_url)
        embed3.set_thumbnail(url=ctx.author.avatar_url)    

        embed3.add_field(name='Quick-Start Guide',
                         value=(f"**∘ |** Fighting bosses is the fastest way to level up. Try doing `{p}pve 1`.\n"
                                f"**∘ |** You will notice that you had set Attack, Crit, and HP stats. "
                                f"There are multiple factors affecting these. The fastest way to increase "
                                f"your attack is with a better weapon. Do `{p}inventory` and equip "
                                f"your **Wooden Spear** by doing `{p}equip <ID>`. The ID is the number "
                                f"listed next to the weapon's name in your inventory."))

        embed3.add_field(name='Introduction to Class and Origin',
                         value=(f"**∘ |** Now do `{p}class` and `{p}origin`. There are 10 classes "
                                f"and 9 origins, each with their own niche. Read their effects "
                                f"carefully, then do `{p}class <Name>` and `{p}origin <Name>` "
                                f"to take on whichever are your favorites! You can change them "
                                f"again later."),
                         inline=False)

        embed4 = discord.Embed(color=self.client.ayesha_blue)
        embed4.set_author(name='Ayesha Tutorial: Introduction', icon_url=self.client.user.avatar_url)
        embed4.set_thumbnail(url=ctx.author.avatar_url) 

        embed4.add_field(name='The Gacha System!',
                         value=(f"**∘ |** To get stronger weapons and acolytes, use the `{p}roll` "
                                f"command. You can roll up to 10 times at once with `{p}roll 10`.\n"
                                f"**∘ |** Each summon from the gacha costs **1 rubidic**, Ayesha's "
                                f"gacha currency. You start off with 10 rolls, but can gain more:\n"
                                f"**  -** By levelling up (do more `{p}pve`!)\n"
                                f"**  -** Doing `{p}daily` every 12 hours, for **2** rubidics.\n"
                                f"**  -** And voting for the bot on the bot list! This will net you "
                                f"**1** rubidic, but we are listed on two sites (do `{p}vote`). "
                                f"Voting has the same cooldown as `{p}daily`, so you can do it at the "
                                f"the same time everyday, twice a day, for **8** rubidics/day!"))

        embed4.add_field(name='Your Friendly Neighborhood Acolyte',
                         value=(f"**∘ |** Acolytes are the most effective way to increase your ATK, "
                                f"Crit, and HP, and some give other powerful effects!\n"
                                f"**∘ |** Acolytes are obtained through gacha. If you've already "
                                f"pulled some, you can see your list with `{p}tavern`.\n"
                                f"**∘ |** Like your inventory, acolytes have an ID number, and they "
                                f"are equipped with the `{p}hire` command. You can have up to 2 "
                                f"acolytes equipped at any time, hence the slot being '1 or 2.'"),
                         inline=False)

        embed5 = discord.Embed(title='Thanks for playing!',
                               description=(f"More tutorials for other aspects of the bot:\n"
                                            f"**  -** `{p}tutorial acolytes`\n"
                                            f"**  -** `{p}tutorial items`\n"
                                            f"**  -** `{p}tutorial pve`\n"
                                            f"**  -** `{p}tutorial travel`\n\n"
                                            f"Need help with something? Check out the `{p}help` command!\n\n"
                                            f"Suggestions? Bugs? Want to meet more players? Join the "
                                            f"[support server](https://discord.com/api/oauth2/authorize?client_id=767234703161294858&permissions=70347841&scope=bot).\n\n"
                                            f"Support us by voting on [top.gg](https://top.gg/bot/767234703161294858)!"),
                               color=self.client.ayesha_blue)
        embed5.set_author(name='Ayesha Tutorial: Introduction', icon_url=self.client.user.avatar_url)
        embed5.set_thumbnail(url=ctx.author.avatar_url) 


        pages = PageMaker.number_pages([embed1, embed2, embed3, embed4, embed5])
        tutorial_pages = menus.MenuPages(source=PageSourceMaker.PageMaker(pages), 
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