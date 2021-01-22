import discord
import asyncio

from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

import aiosqlite
from Utilities import Checks, AssetCreation

import math

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

    def __init__(self, client):
        self.client = client

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('Profile is ready.')

    #INVISIBLE
    async def createCharacter(self, ctx, name):
        user = (ctx.author.id, name)
        async with aiosqlite.connect(AssetCreation.PATH) as conn:
            await conn.execute('INSERT INTO players (user_id, user_name) VALUES (?, ?)', user)
            await conn.execute('INSERT INTO resources (user_id) VALUES (?)', (ctx.author.id,))
            await conn.commit()
        await AssetCreation.createItem(ctx.author.id, 20, 'Common', crit=0, weaponname='Wooden Spear', weapontype='Spear')

    #COMMANDS
    @commands.command(aliases=['begin','create'], brief='<name : str>', description='Start the game of AyeshaBot.')
    @commands.check(Checks.not_player)
    async def start(self, ctx, *, name : str = None):
        if not name:
            name = ctx.author.display_name
        if len(name) > 32:
                await ctx.send("Name can only be up to 32 characters")
        else:
            prefix = await self.client.get_prefix(ctx.message)
            embed = discord.Embed(title='Start the game of AyeshaBot?', color=0xBEDCF6)
            embed.add_field(name=f'Your Name: {name}', value=f'You can customize your name by doing `{prefix}start <name>`')
            start = await YesNo(ctx, embed).prompt(ctx)
            if start:
                await ctx.send(f'Your Name: {name}')
                await self.createCharacter(ctx, name)
                await ctx.reply("Success! Use the `tutorial` command to get started!")  

    @commands.command(aliases=['p'], description='View your profile')
    async def profile(self, ctx, player : commands.MemberConverter = None):
        #Make sure targeted person is a player
        if player is None: #return author profile
            if not await Checks.has_char(ctx.author):
                await ctx.reply('You don\'t have a character. Do `start` to make one!')
                return
            else:
                player = ctx.author
        else:
            if not await Checks.has_char(player):
                await ctx.reply('This person does not have a character')
                return
        #Otherwise target is a player and we can access their profile
        attack, crit = await AssetCreation.getAttack(player.id)
        query = (player.id,)
        async with aiosqlite.connect(AssetCreation.PATH) as conn:
            c = await conn.execute("""SELECT user_name, level, equipped_item, acolyte1, acolyte2, guild, gold, class, origin, location, 
                pvpwins, pvpfights, bosswins, bossfights
                FROM players WHERE user_id = ?""", query)
            user_name, level, equipped, acolyte1, acolyte2, guild, gold, job, origin, location, pvpwins, pvpfights, bosswins, bossfights = await c.fetchone()
            #Calc pvp and boss wins. If 0, hardcode to 0 to prevent div 0
            if pvpfights == 0: 
                pvpwinrate = 0
            else:
                pvpwinrate = pvpwins/pvpfights*100
            if bossfights == 0:
                bosswinrate = 0
            else:
                bosswinrate = bosswins/bossfights*100
            d = await conn.execute('SELECT * FROM Items WHERE item_id = ?', (equipped,)) #Change the * later
            item = await d.fetchone()
            if guild is not None:
                guild = await AssetCreation.getGuildByID(guild)
            else:
                guild = {'Name' : 'None'}
            #Create the strings for acolytes
            if acolyte1 is not None:
                acolyte1 = await AssetCreation.getAcolyteByID(acolyte1)
                acolyte1 = f"{acolyte1['Name']} ({acolyte1['Rarity']}⭐)"
            if acolyte2 is not None:   
                acolyte2 = await AssetCreation.getAcolyteByID(acolyte2)
                acolyte2 = f"{acolyte2['Name']} ({acolyte2['Rarity']}⭐)"
            #Create Embed
            embed = discord.Embed(title=f'{player.display_name}\'s Profile: {user_name}', color=0xBEDCF6)
            embed.set_thumbnail(url=f'{player.avatar_url}')
            embed.add_field(
                name='Character Info',
                value=f"Money: `{gold}`\nClass: `{job}`\nOrigin: `{origin}`\nLocation: `{location}`\nAssociation: `{guild['Name']}`",
                inline=True)
            embed.add_field(
                name='Character Stats',
                value=f'Level: `{level}`\nAttack: `{attack}`\nCrit: `{crit}%`\nPvP Winrate: `{pvpwinrate:.0f}%`\nBoss Winrate: `{bosswinrate:.0f}%`',
                inline=True)
            if item is not None:
                embed.add_field(
                    name='Party',
                    value=f"Item: `{item[5]} ({item[6]})`\nAcolyte: `{acolyte1}`\nAcolyte: `{acolyte2}`",
                    inline=True)
            else:
                embed.add_field(
                    name='Party',
                    value=f"Item: `None`\nAcolyte: `{acolyte1}`\nAcolyte: `{acolyte2}`",
                    inline=True)
            await ctx.reply(embed=embed)

    @commands.command(aliases=['xp'], description='Check your xp and level.')
    @commands.check(Checks.is_player)
    async def level(self, ctx):
        async with aiosqlite.connect(AssetCreation.PATH) as conn:
            c = await conn.execute('SELECT level, xp FROM players WHERE user_id = ?', (ctx.author.id,))
            level, xp = await c.fetchone()
            tonext = math.floor(10000000 * math.cos(((level+1)/64)+3.14) + 10000000 - 600) - xp

        embed = discord.Embed(color=0xBEDCF6)
        embed.add_field(name='Level', value=f'{level}')
        embed.add_field(name='EXP', value=f'{xp}')
        embed.add_field(name=f'EXP until Level {level+1}', value=f'{tonext}')
        await ctx.reply(embed=embed)

    @commands.command(brief='<name>', description='Change your character name.')
    @commands.check(Checks.is_player)
    async def rename(self, ctx, *, name):
        if len(name) > 32:
            await ctx.reply('Name max 32 characters.')
            return
        async with aiosqlite.connect(AssetCreation.PATH) as conn:
            await conn.execute('UPDATE Players SET user_name = ? WHERE user_id = ?', (name, ctx.author.id))
            await conn.commit()
            await ctx.reply(f'Name changed to `{name}`')

    #Add a tutorial command at the end of alpha
    @commands.command(description='Learn the game')
    async def tutorial(self, ctx):
        await ctx.reply("""I'm currently trying to write a better tutorial. Ping Aramythia for help.
Otherwise use the `help` command and look at the modules existing: Profile, PvE, Travel, Associations are the big ones.
Do `create` to create a character, and `help Profile` to see how to customize it.
Do `pve <level>` to fight bosses. This is the bread and butter of the game so far.
Do `travel` to change the location in your profile. It gives limited rewards, but is currently being expanded greatly.
This is a gacha game. We are implementing acolytes and weapons.""")



def setup(client):
    client.add_cog(Profile(client))