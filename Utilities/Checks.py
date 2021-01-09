import discord
import asyncio

from discord.ext import commands, menus

import aiosqlite

PATH = 'PATH'

async def not_player(ctx):
    query = (ctx.author.id,)
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT * FROM players WHERE user_id = ?', query)
        result = await c.fetchone()
        if result is None: #Then there is no char for this id
            return True

async def is_player(ctx):
    query = (ctx.author.id,)
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT * FROM players WHERE user_id = ?', query)
        result = await c.fetchone()
        if result is not None: #Then there is a char for this id
            return True
