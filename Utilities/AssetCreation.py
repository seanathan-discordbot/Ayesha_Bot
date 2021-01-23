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

async def createCharacter(ctx, name):
    user = (ctx.author.id, name)
    async with aiosqlite.connect(PATH) as conn:
        await conn.execute('INSERT INTO players (user_id, user_name) VALUES (?, ?)', user)
        await conn.execute('INSERT INTO resources (user_id) VALUES (?)', (ctx.author.id,))
        await conn.commit()
    await createItem(ctx.author.id, 20, 'Common', crit=0, weaponname='Wooden Spear', weapontype='Spear')

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

async def getAllItemsFromPlayer(user_id : int):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT item_id, weapontype, attack, crit, weapon_name, rarity, is_equipped FROM items WHERE owner_id = ? AND is_equipped = 1', (user_id,))
        inv = await c.fetchall()
        c = await conn.execute('SELECT item_id, weapontype, attack, crit, weapon_name, rarity, is_equipped FROM items WHERE owner_id = ? AND is_equipped = 0', (user_id,))
        for item in (await c.fetchall()):
            inv.append(item)
    return inv

async def verifyItemOwnership(item_id : int, user_id : int):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT weapon_name FROM items WHERE item_id = ? AND owner_id = ?', (item_id, user_id))
        item = await c.fetchone()
        if item is None:
            return False
        else:
            return True

async def getEquippedItem(user_id : int):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT item_id FROM items WHERE owner_id = ? AND is_equipped = 1', (user_id,))
        item = await c.fetchone()
        return item[0]

async def unequipItem(user_id : int, item_id : int = None):
    async with aiosqlite.connect(PATH) as conn:
        if item_id is None:
            item_id = await getEquippedItem(user_id)

        await conn.execute('UPDATE items SET is_equipped = 0 WHERE item_id = ?', (item_id,))
        await conn.execute('UPDATE players SET equipped_item = NULL WHERE user_id = ?', (user_id,))
        await conn.commit()

async def equipItem(item_id : int, user_id : int):
    async with aiosqlite.connect(PATH) as conn:
        await conn.execute('UPDATE items SET is_equipped = 1 WHERE item_id = ?', (item_id,))
        await conn.execute('UPDATE players SET equipped_item = ? WHERE user_id = ?', (item_id, user_id))
        await conn.commit()

async def getItem(item_id : int):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT weapontype, owner_id, attack, crit, weapon_name, rarity, is_equipped FROM items WHERE item_id = ?', (item_id,))
        info = await c.fetchone()
    
    item = {
        'ID' : item_id,
        'Type' : info[0],
        'Owner' : info[1],
        'Attack' : info[2],
        'Crit' : info[3],
        'Name' : info[4],
        'Rarity' : info[5],
        'Equip' : info[6]
    }

    return item

async def deleteItem(item_id : int):
    async with aiosqlite.connect(PATH) as conn:
        await conn.execute('DELETE FROM Items WHERE item_id = ?', (item_id,))
        await conn.commit()

async def setItemOwner(item_id : int, user_id : int):
    async with aiosqlite.connect(PATH) as conn:
        await conn.execute('UPDATE Items SET owner_id = ? WHERE item_id = ?', (user_id, item_id))
        await conn.commit()

async def setItemName(item_id : int, name : str):
    async with aiosqlite.connect(PATH) as conn:
        await conn.execute('UPDATE items SET weapon_name = ? WHERE item_id = ?', (name, item_id))
        await conn.commit()

async def increaseItemAttack(item_id : int, increase : int):
    async with aiosqlite.connect(PATH) as conn:
        await conn.execute('UPDATE items SET attack = attack + ? WHERE item_id = ?', (increase, item_id))
        await conn.commit()

async def createAcolyte(owner_id, acolyte_name):
    async with aiosqlite.connect(PATH) as conn:
        acolyte = (owner_id, acolyte_name)
        await conn.execute("""
            INSERT INTO acolytes (owner_id, acolyte_name) VALUES (?, ?)""", acolyte)
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
        c = await conn.execute('SELECT acolyte_name, level, is_equipped, duplicate FROM Acolytes WHERE instance_id = ?', (instance,))
        name, level, equip_status, dupes = await c.fetchone()
        acolyte = getAcolyteByName(name)

        acolyte['Level'] = level
        acolyte['ID'] = instance
        acolyte['Equip'] = equip_status
        acolyte['Dupes'] = dupes

        return acolyte

async def getAcolyteFromPlayer(user_id : int): #Returns the IDs of the equipped acolytes
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT acolyte1, acolyte2 FROM players WHERE user_id = ?', (user_id,))
        acolyte1, acolyte2 = await c.fetchone()
        return acolyte1, acolyte2

async def getAllAcolytesFromPlayer(user_id : int): #Returns tuple of every acolyte a player owns
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute("""SELECT instance_id, acolyte_name, level, is_equipped, duplicate FROM acolytes
                WHERE owner_id = ? AND (is_equipped = 1 OR is_equipped = 2)""", (user_id,))
        inv = await c.fetchall()
        c = await conn.execute("""SELECT instance_id, acolyte_name, level, is_equipped, duplicate FROM acolytes
                WHERE owner_id = ? AND is_equipped = 0""", (user_id,))
        for item in (await c.fetchall()): 
            inv.append(item)

    return inv

async def verifyAcolyteOwnership(instance_id : int, user_id : int):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT instance_id FROM Acolytes WHERE instance_id = ? AND owner_id = ?', (instance_id, user_id))
        acolyte = await c.fetchone()
        if acolyte is None:
            return False
        else:
            return True #Then something came up and teh acolyte actually is in this player's tavern

async def unequipAcolyte(instance_id : int, slot : int = None, user_id : int = None):
    async with aiosqlite.connect(PATH) as conn:
        await conn.execute('UPDATE Acolytes SET is_equipped = 0 WHERE instance_id = ?', (instance_id,))

        if slot == 1:
            await conn.execute('UPDATE players SET acolyte1 = NULL where user_id = ?', (user_id,))
        if slot == 2:
            await conn.execute('UPDATE players SET acolyte2 = NULL where user_id = ?', (user_id,))

        await conn.commit()

async def equipAcolyte(instance_id : int, slot : int, user_id : int):
    async with aiosqlite.connect(PATH) as conn:
        await conn.execute('UPDATE Acolytes SET is_equipped = ? WHERE instance_id = ?', (slot, instance_id))
        if slot == 1:
            await conn.execute('UPDATE Players SET acolyte1 = ? WHERE user_id = ?', (instance_id, user_id))
        else:
            await conn.execute('UPDATE Players SET acolyte2 = ? WHERE user_id = ?', (instance_id, user_id))
        
        await conn.commit()

async def giveAcolyteXP(amount : int, instance_id : int):
    async with aiosqlite.connect(PATH) as conn:
        await conn.execute('UPDATE acolytes SET xp = xp + ? WHERE instance_id = ?', (amount, instance_id))
        await conn.commit()

async def createGuild(name, guild_type, leader, icon):
    async with aiosqlite.connect(PATH) as conn:
        await conn.execute('INSERT INTO guilds (guild_name, guild_type, leader_id, guild_icon) VALUES (?, ?, ?, ?)', (name, guild_type, leader, icon))
        c = await conn.execute('SELECT guild_id FROM guilds WHERE leader_id = ?', (leader,))
        guild_id = await c.fetchone()
        await conn.execute('UPDATE players SET guild = ?, gold = gold - 15000, guild_rank = "Leader" WHERE user_id = ?', (guild_id[0], leader))
        await conn.commit()

async def joinGuild(guild_id, user_id): #DOES NOT VERIFY IF THEY'RE ALREADY IN A GUILD
    async with aiosqlite.connect(PATH) as conn:
        await conn.execute('UPDATE players SET guild = ?, guild_rank = "Member" WHERE user_id = ?', (guild_id, user_id))
        await conn.commit()

async def leaveGuild(user_id : int): #DOES NOT VERIFY IF MEMBER LEAVING IS LEADER USE ON MEMBERS ONLYYY
    async with aiosqlite.connect(PATH) as conn:
        await conn.execute('UPDATE Players SET guild = NULL, guild_rank = NULL WHERE user_id = ?', (user_id,))
        await conn.commit()

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

async def giveGuildXP(amount : int, guild_id : int):
    async with aiosqlite.connect(PATH) as conn:
        await conn.execute('UPDATE guilds SET guild_xp = guild_xp + ? WHERE guild_id = ?', (amount, guild_id))
        await conn.commit()

async def getGuildXP(guild_id : int):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT guild_xp FROM guilds WHERE guild_id = ?', (guild_id,))
        xp = await c.fetchone()
        return xp[0]

async def getGuildMembers(guild_id : int):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute("""SELECT user_id, user_name, guild_rank FROM players WHERE guild = ?
            ORDER BY CASE guild_rank WHEN "Leader" then 1
            WHEN "Officer" THEN 2
            WHEN "Adept" THEN 3
            ELSE 4 END""", (guild_id,))
        members = await c.fetchall()
        return members

async def setGuildDescription(description, guild_id : int):
    async with aiosqlite.connect(PATH) as conn:
        await conn.execute('UPDATE guilds SET guild_desc = ? WHERE guild_id = ?', (description, guild_id))
        await conn.commit()

async def lockGuild(guild_id : int):
    async with aiosqlite.connect(PATH) as conn:
        await conn.execute('UPDATE guilds SET join_status = "closed" WHERE guild_id = ?', (guild_id,))
        await conn.commit()

async def unlockGuild(guild_id : int):
    async with aiosqlite.connect(PATH) as conn:
        await conn.execute('UPDATE guilds SET join_status = "open" WHERE guild_id = ?', (guild_id,))
        await conn.commit()

async def changeGuildRank(rank : str, user_id : int):
    async with aiosqlite.connect(PATH) as conn:
        await conn.execute('UPDATE players SET guild_rank = ? WHERE user_id = ?', (rank, user_id))
        
        if rank == "Leader":
            guild = await getGuildFromPlayer(user_id)
            await conn.execute('UPDATE guilds SET leader_id = ? WHERE guild_id = ?', (user_id, guild['ID']))  

        await conn.commit()  

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
        if material == 'fur':
            await conn.execute('UPDATE resources SET fur = fur + ? WHERE user_id = ?', query)
        if material == 'bone':
            await conn.execute('UPDATE resources SET bone = bone + ? WHERE user_id = ?', query)
        if material == 'silver':
            await conn.execute('UPDATE resources SET silver = silver + ? WHERE user_id = ?', query)

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

async def getClass(user_id : int):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT class FROM players WHERE user_id = ?', (user_id,))
        role = await c.fetchone()
        try:
            return role[0]
        except TypeError:
            return None

async def getPlayerCount():
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT COUNT(*) FROM Players')
        records = await c.fetchone()

        return records[0]

async def getPlayerByID(user_id: int):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute("""SELECT num, user_name, level, equipped_item, acolyte1, acolyte2, guild, guild_rank, 
            gold, class, origin, location, pvpwins, pvpfights, bosswins, bossfights
            FROM players WHERE user_id = ?""", (user_id,))
        info = await c.fetchone()

    player = {
        'Num' : info[0],
        'Name' : info[1],
        'Level' : info[2],
        'Item' : info[3],
        'Acolyte1' : info[4],
        'Acolyte2' : info[5],
        'Guild' : info[6],
        'Rank' : info[7],
        'Gold' : info[8],
        'Class' : info[9],
        'Origin' : info[10],
        'Location' : info[11],
        'pvpwins' : info[12],
        'pvpfights' : info[13],
        'bosswins' : info[14],
        'bossfights' : info[15]
    }

    return player

async def getPlayerByNum(num : int):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT gold, user_id, user_name FROM players WHERE num = ?', (num,))
        gold, idnum, name = await c.fetchone()

        return gold, idnum, name

async def setPlayerClass(role : str, user_id : int):
    async with aiosqlite.connect(PATH) as conn:
        await conn.execute('UPDATE players SET class = ? WHERE user_id = ?', (role, user_id))
        await conn.commit()

async def setPlayerOrigin(role : str, user_id : int):
    async with aiosqlite.connect(PATH) as conn:
        await conn.execute('UPDATE players SET origin = ? WHERE user_id = ?', (role, user_id))
        await conn.commit()

async def getPlayerXP(user_id : int):
    async with aiosqlite.connect(PATH) as conn:
        c = await conn.execute('SELECT level, xp FROM players WHERE user_id = ?', (user_id,))
        level, xp = await c.fetchone()
        return level, xp

async def setPlayerName(user_id : int, name : str):
    async with aiosqlite.connect(PATH) as conn:
        await conn.execute('UPDATE players SET user_name = ? WHERE user_id = ?', (name, user_id))
        await conn.commit()

async def giveBountyRewards(user_id : int, gold : int, xp : int, victory : bool):
    async with aiosqlite.connect(PATH) as conn:
        if victory:
            await conn.execute('UPDATE players SET gold = gold + ?, xp = xp + ?, bosswins = bosswins + 1, bossfights = bossfights + 1 WHERE user_id = ?', (gold, xp, user_id))
        else:
            await conn.execute('UPDATE players SET gold = gold + ?, xp = xp + ?, bossfights = bossfights + 1 WHERE user_id = ?', (gold, xp, user_id))

        await conn.commit()

async def giveAdventureRewards(xp : int, gold : int, location : str, user_id : int):
    async with aiosqlite.connect(PATH) as conn:
        await conn.execute("""UPDATE players SET 
            xp = xp + ?, gold = gold + ?, location = ?, 
            adventure = NULL, destination = NULL 
            WHERE user_id = ?""", (xp, gold, location, user_id))
        await conn.commit()

async def setAdventure(adventure : int, destination : str, user_id : int):
    async with aiosqlite.connect(PATH) as conn:
        await conn.execute('UPDATE players SET adventure = ?, destination = ? WHERE user_id = ?', (adventure, destination, user_id))
        await conn.commit()