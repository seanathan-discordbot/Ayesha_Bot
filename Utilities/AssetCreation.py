import discord
import asyncio

from discord.ext import commands, menus

import aiosqlite

import random
import math

PATH = 'PATH'

weapontypes = ['Spear', 'Sword', 'Dagger', 'Bow', 'Trebuchet', 'Gauntlets', 'Staff', 'Greatsword', 'Axe', 'Sling', 'Javelin', 'Falx', 'Mace']



async def createItem(owner_id, attack, rarity, crit = None, weaponname = None, weapontype=None):
    if crit is None:
        if rarity == 'Common':
            crit = random.randint(0,5)
        if rarity == 'Uncommon':
            crit = random.randint(0,5)
        if rarity == 'Rare':
            crit = random.randint(0,10)
        if rarity == 'Epic':
            crit = random.randint(0,15)
        if rarity == 'Legendary':
            crit = random.randint(0,20)
    
    if weapontype is None:
        weapontype = random.choices(weapontypes)
        weapontype = weapontype[0]
    if weaponname is None:
        weaponname = 'Unnamed Weapon'
    async with aiosqlite.connect(PATH) as conn:
        await conn.execute("""
            INSERT INTO items (weapontype, owner_id, attack, crit, weapon_name, rarity)
            VALUES (?, ?, ?, ?, ?, ?)""", (weapontype, owner_id, attack, crit, weaponname, rarity))
        await conn.commit()

async def createAcolyte(owner_id, acolyte_id):
    async with aiosqlite.connect(PATH) as conn:
        acolyte = (owner_id, acolyte_id)
        await conn.execute("""
            INSERT INTO items (owner_id, acolyte_id) VALUES (?, ?)""", acolyte)
        await conn.commit()

async def checkLevel(ctx, user_id):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT level, xp, user_name FROM Players WHERE user_id = ?', (user_id,))
        current = await c.fetchone()
        if current[0] + 1 == getLevel(current[1]):
            #Give some rewards
            gold = (current[0] + 1) * 500
            rubidic = math.ceil((current[0] + 1) / 10)
            await conn.execute('UPDATE Players SET level = level + 1, gold = gold + ?, rubidic = rubidic + ? WHERE user_id = ?', (gold, rubidic, user_id,))
            await conn.commit()
            #Send level-up message
            embed = discord.Embed(title=f'You\'ve levelled up to level {current[0]+1}!', color=0xBEDCF6)
            embed.add_field(name=f'{current[2]}, you gained some rewards:', value=f'**Gold:** {gold}\n**Rubidics:** {rubidic}')
            await ctx.send(embed=embed)

def getLevel(xp):
    level = 0

    def f(x):
        w = 10000000
        y = math.floor(w * math.cos((x/64)+3.14) + w - 600)
        return y 
    
    while(xp >= f(level)):
        level += 1
    level -= 1

    return level

async def getAttack(user_id, returnhp = False):
    charattack, weaponattack, attack, crit, hp = 0, 0, 0, 0, 1000
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT level, equipped_item, acolyte1, acolyte2, class FROM Players WHERE user_id = ?', (user_id,))
        char = await c.fetchone()
        d = await conn.execute('SELECT attack, crit FROM Items WHERE item_id = ?', (char[1],))
        item = await d.fetchone()
        # Implement acolytes later
        charattack = char[0] * 2
        weaponattack = item[0]
        if char[4] == 'Soldier':
            charattack = math.floor(charattack * 1.15)
        if char[4] == 'Blacksmith':
            weaponattack = math.floor(weaponattack * 1.1)
        attack = charattack + weaponattack
        crit = 5 + item[1]
        if char[4] == 'Scribe':
            crit += 10
        if char[4] == 'Leatherworker':
            hp += 200
        
        if not returnhp:
            return attack, crit
        else:
            return attack, crit, hp