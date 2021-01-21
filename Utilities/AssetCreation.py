import discord
import asyncio

from discord.ext import commands, menus

import aiosqlite

import json
import random
import math

PATH = 'PATH'
ACOLYTE_PATH = 'PATH'

weapontypes = ['Spear', 'Sword', 'Dagger', 'Bow', 'Trebuchet', 'Gauntlets', 'Staff', 'Greatsword', 'Axe', 'Sling', 'Javelin', 'Falx', 'Mace']

dashes = []
for i in range(0,10):
    dashes.append("".join(["▬"]*i))

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
        if current[1] < getAcolyteLevel(current[2]):
            await conn.execute('UPDATE Acolytes SET level = level + 1 WHERE instance_id = ?', (instance_id,))
            await conn.commit()
            await ctx.send(f'{current[0]} levelled up to level {current[1] + 1}!')

async def checkLevel(ctx, user_id, aco1=None, aco2=None):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT level, xp, user_name FROM Players WHERE user_id = ?', (user_id,))
        current = await c.fetchone()
        if current[0] < calcLevel(current[1]):
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

def getAcolyteLevel(xp):
    level = 0

    def f(x):
        w = 3000000
        y = math.floor(w * math.cos((x/64)+3.14) + w)
        return y 
    
    while(xp >= f(level)):
        level += 1
    level -= 1

    if level > 100:
        level = 100

    return level

def calcLevel(xp):
    level = 0

    def f(x):
        w = 6000000
        y = math.floor(w * math.cos((x/64)+3.14) + w)
        return y 
    
    while(xp >= f(level)):
        level += 1
    level -= 1

    if level > 100:
        level = 100

    return level

async def getLevel(user_id : int):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT level FROM Players WHERE user_id = ?', (user_id,))
        level = await c.fetchone()
        return level[0]

async def getAttack(user_id, returnothers = False):
    charattack, weaponattack, guildattack, acolyteattack, attack, crit, hp = 0, 0, 0, 0, 0, 0, 500
    acolyte1, acolyte2 = None, None
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT level, equipped_item, acolyte1, acolyte2, class FROM Players WHERE user_id = ?', (user_id,))
        char = await c.fetchone()
        d = await conn.execute('SELECT attack, crit FROM Items WHERE item_id = ?', (char[1],))
        item = await d.fetchone()
        if char[2] is not None:
            acolyte1 = await getAcolyteByID(char[2])
            acolyteattack = acolyteattack + acolyte1['Attack'] + (acolyte1['Scale'] * acolyte1['Level'])
            crit = crit + acolyte1['Crit']
            hp = hp + acolyte1['HP']
        if char[3] is not None:
            acolyte2 = await getAcolyteByID(char[3])
            acolyteattack = acolyteattack + acolyte2['Attack'] + (acolyte2['Scale'] * acolyte2['Level'])
            crit = crit + acolyte2['Crit']
            hp = hp + acolyte2['HP']
        charattack = 20 + char[0] * 2
        if item is not None:
            weaponattack = item[0]
        if char[4] == 'Soldier':
            charattack = math.floor(charattack * 1.2) + 10
        if char[4] == 'Blacksmith':
            weaponattack = math.floor(weaponattack * 1.1) + 10
        try:
            guild = await getGuildFromPlayer(user_id)
            guild_level = await getGuildLevel(guild['ID'])
            if guild['Type'] == 'Brotherhood':
                guildattack = guild_level * (guild_level + 1) / 2
                crit = crit + guild_level
        except TypeError:
            pass
        attack = charattack + weaponattack + acolyteattack + guildattack
        if item is not None:
            crit = crit + 5 + item[1]
        else:
            crit = crit + 5
        if char[4] == 'Scribe':
            crit += 10
        if char[4] == 'Leatherworker':
            hp += 200
        
        if not returnothers:
            return int(attack), crit
        else:
            return int(attack), crit, hp, char[4], acolyte1, acolyte2 #returns Class, then acolytes

def getAcolyteByName(name : str):
    with open(ACOLYTE_PATH, 'r') as acolyte_list:
        acolytes = json.load(acolyte_list) #acolytes is a dict
        acolyte_list.close()
    return acolytes[name]

async def getAcolyteByID(instance : int):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT acolyte_name, level FROM Acolytes WHERE instance_id = ?', (instance,))
        name, level = await c.fetchone()
        acolyte = getAcolyteByName(name)
        acolyte.__setitem__('Name', name)
        acolyte.__setitem__('Level', level)
        return acolyte

async def getAcolyteFromPlayer(user_id : int):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT acolyte1, acolyte2 FROM players WHERE user_id = ?', (user_id,))
        acolyte1, acolyte2 = await c.fetchone()
        return acolyte1, acolyte2

async def getGuildFromPlayer(user_id : int):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT guild FROM players WHERE user_id = ?', (user_id,)) 
        guild_id = await c.fetchone()
        return await getGuildByID(guild_id[0])

async def getGuildByID(guild_id : int):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT * FROM guilds WHERE guild_id = ?', (guild_id,))
        info = await c.fetchone()
        guild = {
            'ID' : info[0],
            'Name' : info[1],
            'Type' : info[2],
            'XP' : info[3],
            'Leader' : info[4],
            'Desc' : info[5],
            'Icon' : info[6],
            'Join' : info[7]
        }
        return guild

async def getGuildLevel(guild_id : int, returnline = False):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT level FROM guild_levels WHERE guild_id = ?', (guild_id,))
        level = await c.fetchone()

        if returnline: #Also create a string to show progress
            c = await conn.execute('SELECT guild_xp FROM guilds WHERE guild_id = ?', (guild_id,))
            xp = await c.fetchone()
            progress = int((xp[0] % 100000) / 20000)
            progressStr = dashes[progress]+'◆'+dashes[4-progress]
            return level[0], progressStr
        else:
            return level[0]

async def getGuildMemberCount(guild_id : int):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT member_count FROM guild_membercount WHERE guild_id = ?', (guild_id,))
        count = await c.fetchone()
        return count[0]

async def getGuildCapacity(guild_id : int):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT capacity FROM guild_capacities WHERE guild_id = ?', (guild_id,))
        capacity = await c.fetchone()
        return capacity[0]

async def getAdventure(user_id : int):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT adventure, destination FROM players WHERE user_id = ?', (user_id,))
        adventure = await c.fetchone()
        return adventure

async def getLocation(user_id : int):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT location FROM players WHERE user_id = ?', (user_id,))
        location = await c.fetchone()
        return location[0]

async def giveMat(material : str, amount : int, user_id : int):
    async with aiosqlite.connect(PATH) as conn:
        query = (amount, user_id)

        if material == 'wheat':
            await conn.execute('UPDATE resources SET wheat = wheat + ? WHERE user_id = ?', query)
        if material == 'oat':
            await conn.execute('UPDATE resources SET oat = oat + ? WHERE user_id = ?', query)
        if material == 'wood':
            await conn.execute('UPDATE resources SET wood = wood + ? WHERE user_id = ?', query)
        if material == 'reeds':
            await conn.execute('UPDATE resources SET reeds = reeds + ? WHERE user_id = ?', query)
        if material == 'pine':
            await conn.execute('UPDATE resources SET pine = pine + ? WHERE user_id = ?', query)
        if material == 'moss':
            await conn.execute('UPDATE resources SET moss = moss + ? WHERE user_id = ?', query)
        if material == 'iron':
            await conn.execute('UPDATE resources SET iron = iron + ? WHERE user_id = ?', query)
        if material == 'cacao':
            await conn.execute('UPDATE resources SET cacao = cacao + ? WHERE user_id = ?', query)

        await conn.commit()

async def takeMat(material : str, amount : int, user_id : int):
    async with aiosqlite.connect(PATH) as conn:
        query = (amount, user_id)

        if material == 'wheat':
            await conn.execute('UPDATE resources SET wheat = wheat - ? WHERE user_id = ?', query)
        if material == 'oat':
            await conn.execute('UPDATE resources SET oat = oat - ? WHERE user_id = ?', query)
        if material == 'wood':
            await conn.execute('UPDATE resources SET wood = wood - ? WHERE user_id = ?', query)
        if material == 'reeds':
            await conn.execute('UPDATE resources SET reeds = reeds - ? WHERE user_id = ?', query)
        if material == 'pine':
            await conn.execute('UPDATE resources SET pine = pine - ? WHERE user_id = ?', query)
        if material == 'moss':
            await conn.execute('UPDATE resources SET moss = moss - ? WHERE user_id = ?', query)
        if material == 'iron':
            await conn.execute('UPDATE resources SET iron = iron - ? WHERE user_id = ?', query)
        if material == 'cacao':
            await conn.execute('UPDATE resources SET cacao = cacao - ? WHERE user_id = ?', query)

        await conn.commit()

async def getPlayerMat(material : str, user_id : int):
    async with aiosqlite.connect(PATH) as conn:
        if material == 'wheat':
            c = await conn.execute('SELECT wheat FROM resources WHERE user_id = ?', (user_id,))
        if material == 'oat':
            c = await conn.execute('SELECT oat FROM resources WHERE user_id = ?', (user_id,))
        if material == 'wood':
            c = await conn.execute('SELECT wood FROM resources WHERE user_id = ?', (user_id,))
        if material == 'reeds':
            c = await conn.execute('SELECT reeds FROM resources WHERE user_id = ?', (user_id,))
        if material == 'pine':
            c = await conn.execute('SELECT pine FROM resources WHERE user_id = ?', (user_id,))
        if material == 'moss':
            c = await conn.execute('SELECT moss FROM resources WHERE user_id = ?', (user_id,))
        if material == 'iron':
            c = await conn.execute('SELECT iron FROM resources WHERE user_id = ?', (user_id,))
        if material == 'cacao':
            c = await conn.execute('SELECT cacao FROM resources WHERE user_id = ?', (user_id,))
        if material == 'fur':
            c = await conn.execute('SELECT fur FROM resources WHERE user_id = ?', (user_id,))
        if material == 'bone':
            c = await conn.execute('SELECT bone FROM resources WHERE user_id = ?', (user_id,))
        if material == 'silver':
            c = await conn.execute('SELECT silver FROM resources WHERE user_id = ?', (user_id,))

        mat = await c.fetchone()
        return mat[0]

async def giveGold(amount : int, user_id : int):
    async with aiosqlite.connect(PATH) as conn:
        await conn.execute('UPDATE players SET gold = gold + ? WHERE user_id = ?', (amount, user_id))
        await conn.commit()

async def getGold(user_id : int):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT gold FROM players WHERE user_id = ?', (user_id,))
        gold = await c.fetchone()
        return gold[0]

async def giveRubidics(amount : int, user_id : int):
    async with aiosqlite.connect(PATH) as conn:
        await conn.execute('UPDATE players SET rubidic = rubidic + ? WHERE user_id = ?', (amount, user_id))
        await conn.commit()