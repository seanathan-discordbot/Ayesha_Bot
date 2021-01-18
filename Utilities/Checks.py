import discord
import asyncio

from discord.ext import commands, menus

from Utilities import AssetCreation

import aiosqlite

PATH = 'PATH'

async def not_player(ctx):
    query = (ctx.author.id,)
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT user_id FROM players WHERE user_id = ?', query)
        result = await c.fetchone()
        if result is None: #Then there is no char for this id
            return True

async def is_player(ctx):
    query = (ctx.author.id,)
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT user_id FROM players WHERE user_id = ?', query)
        result = await c.fetchone()
        if result is not None: #Then there is a char for this id
            return True

async def has_char(user : discord.user): #NOT A CHECK --> in-function version of is_player
    query = (user.id,)
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT user_id FROM players WHERE user_id = ?', query)
        result = await c.fetchone()
        if result is not None: #Then there is a char for this id
            return True
        else:
            return False

async def not_in_guild(ctx):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT guild FROM players WHERE user_id = ?', (ctx.author.id,))
        guild = await c.fetchone()
        if guild[0] is None:
            return True

async def target_not_in_guild(user : discord.user): #NOT A CHECK --> in-function version of not_in_guilf
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT guild FROM players WHERE user_id = ?', (user.id,))
        guild = await c.fetchone()
        if guild[0] is None:
            return True

async def in_brotherhood(ctx):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT guild FROM players WHERE user_id = ?', (ctx.author.id,))
        guild = await c.fetchone()
        if guild[0] is None:
            return
        else:
            c = await conn.execute('SELECT guild_type FROM guilds WHERE guild_id = ?', (guild[0],))
            guild_type = await c.fetchone()
            if guild_type[0] == 'Brotherhood':
                return True

async def in_guild(ctx):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT guild FROM players WHERE user_id = ?', (ctx.author.id,))
        guild = await c.fetchone()
        if guild is None:
            return
        else:
            c = await conn.execute('SELECT guild_type FROM guilds WHERE guild_id = ?', (guild[0]))
            guild_type = await c.fetchone()
            if guild_type == 'Guild':
                return True     

async def guild_can_be_created(ctx, name): #NOT A CHECK
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT guild_id FROM guilds WHERE guild_name = ?', (name,))
        is_taken = await c.fetchone()
        if is_taken is not None:
            await ctx.reply('This name is already taken.')
            return
        c = await conn.execute('SELECT gold FROM players WHERE user_id = ?', (ctx.author.id,))
        gold = await c.fetchone()
        if gold[0] < 15000:
            await ctx.reply('You don\'t have enough money form a brotherhood.')
            return
        return True #Otherwise we're good to go

async def is_guild_leader(ctx):
    player_guild = await AssetCreation.getGuildFromPlayer(ctx.author.id)
    if ctx.author.id == player_guild['Leader']:
        return True

async def is_not_guild_leader(ctx):
    player_guild = await AssetCreation.getGuildFromPlayer(ctx.author.id)
    if ctx.author.id != player_guild['Leader']:
        return True

async def guild_has_vacancy(ctx): 
    guild = await AssetCreation.getGuildFromPlayer(ctx.author.id)
    members = await AssetCreation.getGuildMemberCount(guild['ID'])
    capacity = await AssetCreation.getGuildCapacity(guild['ID'])
    if members < capacity:
        return True

async def target_guild_has_vacancy(guild_id : int): #NOT A CHECK. ALT VERSION OF guild_has_vacancy
    guild = await AssetCreation.getGuildByID(guild_id)
    members = await AssetCreation.getGuildMemberCount(guild['ID'])
    capacity = await AssetCreation.getGuildCapacity(guild['ID'])
    if members < capacity:
        return True