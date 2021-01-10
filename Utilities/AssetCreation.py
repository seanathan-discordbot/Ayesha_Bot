import discord
import asyncio

from discord.ext import commands, menus

import aiosqlite

PATH = 'PATH'

async def createItem(weapontype, owner_id, attack, name, rarity):
    async with aiosqlite.connect(PATH) as conn:
        item = (weapontype, owner_id, attack, name, rarity)
        await conn.execute("""
            INSERT INTO items (weapontype, owner_id, attack, weapon_name, rarity)
            VALUES (?, ?, ?, ?, ?)""",
            item)
        await conn.commit()

async def createAcolyte(owner_id, acolyte_id):
    async with aiosqlite.connect(PATH) as conn:
        acolyte = (owner_id, acolyte_id)
        await conn.execute("""
            INSERT INTO items (owner_id, acolyte_id) VALUES (?, ?)""", acolyte)
        await conn.commit()