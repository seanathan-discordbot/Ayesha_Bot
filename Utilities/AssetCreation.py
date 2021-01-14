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

async def createAcolyte(owner_id, acolyte_name):
    async with aiosqlite.connect(PATH) as conn:
        acolyte = (owner_id, acolyte_name)
        await conn.execute("""
            INSERT INTO items (owner_id, acolyte_name) VALUES (?, ?)""", acolyte)
        await conn.commit()

async def checkAcolyteLevel(ctx, instance_id):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT acolyte_name, level, xp FROM Acolytes WHERE instance_id = ?', (instance_id,))
        current = await c.fetchone()
        if current[1] < getLevel(current[2]):
            await conn.execute('UPDATE Acolytes SET level = level + 1 WHERE instance_id = ?', (instance_id,))
            await conn.commit()
            await ctx.send(f'{current[0]} levelled up to level {current[1] + 1}!')

async def checkLevel(ctx, user_id, aco1=None, aco2=None):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT level, xp, user_name FROM Players WHERE user_id = ?', (user_id,))
        current = await c.fetchone()
        if current[0] < getLevel(current[1]):
            #Give some rewards
            gold = (current[0] + 1) * 500
            rubidic = math.ceil((current[0] + 1) / 10)
            await conn.execute('UPDATE Players SET level = level + 1, gold = gold + ?, rubidic = rubidic + ? WHERE user_id = ?', (gold, rubidic, user_id,))
            await conn.commit()
            #Send level-up message
            embed = discord.Embed(title=f'You\'ve levelled up to level {current[0]+1}!', color=0xBEDCF6)
            embed.add_field(name=f'{current[2]}, you gained some rewards:', value=f'**Gold:** {gold}\n**Rubidics:** {rubidic}')
            await ctx.send(embed=embed)
    if aco1 is not None:
        await checkAcolyteLevel(ctx, aco1)
    if aco2 is not None:
        await checkAcolyteLevel(ctx, aco2)

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
    charattack, weaponattack, acolyteattack, attack, crit, hp = 0, 0, 0, 0, 0, 1000
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT level, equipped_item, acolyte1, acolyte2, class FROM Players WHERE user_id = ?', (user_id,))
        char = await c.fetchone()
        d = await conn.execute('SELECT attack, crit FROM Items WHERE item_id = ?', (char[1],))
        item = await d.fetchone()
        if char[2] is not None:
            acolyte1 = await getAcolyteByID(char[2])
            acolyteattack = acolyteattack + acolyte1['Attack'] + (acolyte1['Scale'] * acolyte1['Level'])
            crit = crit + acolyte1['Crit']
        if char[3] is not None:
            acolyte2 = await getAcolyteByID(char[3])
            acolyteattack = acolyteattack + acolyte2['Attack'] + (acolyte2['Scale'] * acolyte2['Level'])
            crit = crit + acolyte2['Crit']
        charattack = 20 + char[0] * 2
        if item is not None:
            weaponattack = item[0]
        if char[4] == 'Soldier':
            charattack = math.floor(charattack * 1.2) + 10
        if char[4] == 'Blacksmith':
            weaponattack = math.floor(weaponattack * 1.1) + 10
        attack = charattack + weaponattack + acolyteattack
        if item is not None:
            crit = crit + 5 + item[1]
        else:
            crit = crit + 5
        if char[4] == 'Scribe':
            crit += 10
        if char[4] == 'Leatherworker':
            hp += 200
        
        if not returnhp:
            return int(attack), crit
        else:
            return int(attack), crit, hp

def getAcolyteByName(name : str):
    return acolyte_list[name]

async def getAcolyteByID(instance : int):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT acolyte_name, level FROM Acolytes WHERE instance_id = ?', (instance,))
        name, level = await c.fetchone()
        acolyte = getAcolyteByName(name)
        acolyte.__setitem__('Name', name)
        acolyte.__setitem__('Level', level)
        return acolyte

acolyte_list = {
    'Test' : {
        'Attack' : 16,
        'Scale' : 1.5,
        'Crit' : 2,
        'Rarity' : 3,
        'Effect' : None,
        'Story' : 'Let\'s go Sean',
        'Image' : None
    },
    'Seanus' : {
        'Attack' : 4,
        'Scale' : 1,
        'Crit' : 1,
        'Rarity' : 4,
        'Effect' : None,
        'Story' : 'Sean is short for Seanathan',
        'Image' : None
    },
}