import discord
import asyncio

from discord.ext import commands, menus

from Utilities import AssetCreation

import asyncpg

async def not_player(ctx):
    async with ctx.bot.pg_con.acquire() as conn:
        result = await conn.fetchrow('SELECT user_id FROM players WHERE user_id = $1', ctx.author.id)
        await ctx.bot.pg_con.release(conn)
    
    if result is None: #Then there is no char for this id
        return True

async def is_player(ctx):
    async with ctx.bot.pg_con.acquire() as conn:
        result = await conn.fetchrow('SELECT user_id FROM players WHERE user_id = $1', ctx.author.id)
        await ctx.bot.pg_con.release(conn)
        
    if result is not None: #Then there is a char for this id
        return True

async def has_char(pool, user : discord.user): #NOT A CHECK --> in-function version of is_player
    async with pool.acquire() as conn:
        result = await conn.fetchrow('SELECT user_id FROM players WHERE user_id = $1', user.id)
        await pool.release(conn)
    
    if result is not None: #Then there is a char for this id
        return True

async def not_in_guild(ctx):
    async with ctx.bot.pg_con.acquire() as conn:
        guild = await conn.fetchval('SELECT guild FROM players WHERE user_id = $1', ctx.author.id)
        await ctx.bot.pg_con.release(conn)
    
    if guild is None:
        return True

async def target_not_in_guild(pool, user : discord.user): #NOT A CHECK --> in-function version of not_in_guilf
    async with pool.acquire() as conn:
        guild = await conn.fetchval('SELECT guild FROM players WHERE user_id = $1', user.id)
        await pool.release(conn)
    
    if guild is None:
        return True

async def in_brotherhood(ctx):
    async with ctx.bot.pg_con.acquire() as conn:
        guild = await conn.fetchrow('SELECT guild FROM players WHERE user_id = $1', ctx.author.id)
    
        if guild[0] is None:
            return
        else:
            guild_type = await conn.fetchval('SELECT guild_type FROM guilds WHERE guild_id = $1', guild[0])
            if guild_type == 'Brotherhood':
                return True

async def in_guild(ctx):
    async with ctx.bot.pg_con.acquire() as conn:
        guild = await conn.fetchrow('SELECT guild FROM players WHERE user_id = $1', ctx.author.id)

        if guild is None:
            return
        else:
            guild_type = await conn.fetchrow('SELECT guild_type FROM guilds WHERE guild_id = $1', guild[0])
            if guild_type[0] == 'Guild':
                return True     

async def guild_can_be_created(ctx, name): #NOT A CHECK
    async with ctx.bot.pg_con.acquire() as conn:
        is_taken = await conn.fetchrow('SELECT guild_id FROM guilds WHERE guild_name = $1', name)
        if is_taken is not None:
            await ctx.reply('This name is already taken.')
            await ctx.bot.pg_con.release(conn)
            return
        gold = await conn.fetchrow('SELECT gold FROM players WHERE user_id = $1', ctx.author.id)
        if gold[0] < 15000:
            await ctx.reply('You don\'t have enough money form a brotherhood.')
            await ctx.bot.pg_con.release(conn)
            return
        await ctx.bot.pg_con.release(conn)
        return True #Otherwise we're good to go

async def is_guild_leader(ctx):
    async with ctx.bot.pg_con.acquire() as conn:
        playerrank = await conn.fetchval('SELECT guild_rank FROM players WHERE user_id = $1', ctx.author.id)

        if playerrank == 'Leader':
            return True

async def is_not_guild_leader(ctx):
    player_guild = await AssetCreation.getGuildFromPlayer(ctx.bot.pg_con, ctx.author.id)
    if ctx.author.id != player_guild['Leader']:
        return True

async def is_guild_officer(ctx):
    async with ctx.bot.pg_con.acquire() as conn:
        rank = await conn.fetchrow('SELECT guild_rank FROM players WHERE user_id = $1', ctx.author.id)
        await ctx.bot.pg_con.release(conn)
    
    if rank[0] == 'Officer' or rank[0]:
        return True
    elif is_guild_leader(ctx):
        return True

async def guild_has_vacancy(ctx): 
    guild = await AssetCreation.getGuildFromPlayer(ctx.bot.pg_con, ctx.author.id)
    members = await AssetCreation.getGuildMemberCount(ctx.bot.pg_con, guild['ID'])
    capacity = await AssetCreation.getGuildCapacity(ctx.bot.pg_con, guild['ID'])
    if members < capacity:
        return True

async def target_guild_has_vacancy(pool, guild_id : int): #NOT A CHECK. ALT VERSION OF guild_has_vacancy
    guild = await AssetCreation.getGuildByID(pool, guild_id)
    members = await AssetCreation.getGuildMemberCount(pool, guild['ID'])
    capacity = await AssetCreation.getGuildCapacity(pool, guild['ID'])
    if members < capacity:
        return True