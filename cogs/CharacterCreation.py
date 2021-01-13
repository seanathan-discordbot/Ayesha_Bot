import discord
import asyncio

from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

import aiosqlite
from Utilities import Checks, AssetCreation

import math

PATH = 'PATH'

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

class CharacterCreation(commands.Cog):

    def __init__(self, client):
        self.client = client

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('CC is ready.')

    #INVISIBLE
    async def createCharacter(self, ctx, name):
        user = (ctx.author.id, name)
        async with aiosqlite.connect(PATH) as conn:
            await conn.execute("""
                INSERT INTO players (user_id, user_name)
                VALUES (?, ?)""",
                user)
            await conn.commit()
        await AssetCreation.createItem(ctx.author.id, 20, 'Common', crit=0, weaponname='Wooden Spear', weapontype='Spear')

    #COMMANDS
    @commands.command(aliases=['begin','create'], brief='<name : str>', description='Start the game of Seanathan')
    @commands.check(Checks.not_player)
    async def start(self, ctx, *, name : str = None):
        if not name:
            name = ctx.author.display_name
        if len(name) > 32:
                await ctx.send("Name can only be up to 32 characters")
        else:
            prefix = await self.client.get_prefix(ctx.message)
            embed = discord.Embed(title='Start the game of Seanathan?', color=0xBEDCF6)
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
        attack, crit = await AssetCreation.getAttack(ctx.author.id)
        query = (player.id,)
        async with aiosqlite.connect(PATH) as conn:
            c = await conn.execute('SELECT * FROM players WHERE user_id = ?', query)
            profile = await c.fetchone()
            # level = AssetCreation.getLevel(profile[2])
            if profile[13] == 0:
                pvpwins = 0
            else:
                pvpwins = profile[12]/profile[13]*100
            if profile[15] == 0:
                bosswins = 0
            else:
                bosswins = profile[14]/profile[15]*100
            d = await conn.execute('SELECT * FROM Items WHERE item_id = ?', (profile[4],))
            item = await d.fetchone()
            #Create Embed
            embed = discord.Embed(title=f'{player.display_name}\'s Profile: {profile[1]}', color=0xBEDCF6)
            embed.set_thumbnail(url=f'{player.avatar_url}')
            embed.add_field(
                name='Character Info',
                value=f'Money: `{profile[8]}`\nClass: `{profile[9]}`\nOrigin: `{profile[10]}`\nLocation: `{profile[11]}`\nAssociation: `{profile[7]}`',
                inline=True)
            embed.add_field(
                name='Character Stats',
                value=f'Level: `{profile[3]}`\nAttack: `{attack}`\nCrit: `{crit}%`\nPvP Winrate: `{pvpwins:.0f}%`\nBoss Winrate: `{bosswins:.0f}%`',
                inline=True)
            if item is not None:
                embed.add_field(
                    name='Party',
                    value=f'Item: `{item[5]} ({item[6]})`\nAcolyte: `{profile[5]}`\nAcolyte: `{profile[6]}`',
                    inline=True)
            else:
                embed.add_field(
                    name='Party',
                    value=f'Item: `None`\nAcolyte: `{profile[5]}`\nAcolyte: `{profile[6]}`',
                    inline=True)
            await ctx.reply(embed=embed)

    @commands.command(aliases=['xp'], description='Check your xp and level.')
    @commands.check(Checks.is_player)
    async def level(self, ctx):
        async with aiosqlite.connect(PATH) as conn:
            c = await conn.execute('SELECT level, xp FROM players WHERE user_id = ?', (ctx.author.id,))
            level, xp = await c.fetchone()
            tonext = math.floor(10000000 * math.cos(((level+1)/64)+3.14) + 10000000 - 600) - xp

        embed = discord.Embed(color=0xBEDCF6)
        embed.add_field(name='Level', value=f'{level}')
        embed.add_field(name='EXP', value=f'{xp}')
        embed.add_field(name=f'EXP until Level {level+1}', value=f'{tonext}')
        await ctx.reply(embed=embed)

    #Add a tutorial command at the end of alpha



def setup(client):
    client.add_cog(CharacterCreation(client))