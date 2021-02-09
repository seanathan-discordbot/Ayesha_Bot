import discord
import asyncio

from discord.ext import commands, menus

import asyncpg

import json
import random
import math
import time
import coolname

from Utilities import Links

ACOLYTE_PATH = Links.acolyte_list

weapontypes = ['Spear', 'Sword', 'Dagger', 'Bow', 'Trebuchet', 'Gauntlets', 'Staff', 'Greatsword', 'Axe', 'Sling', 'Javelin', 'Falx', 'Mace']

Weaponvalues = {
    'Common' : (1, 20),
    'Uncommon' : (15, 30),
    'Rare' : (75, 150),
    'Epic' : (400, 700),
    'Legendary' : (2000, 3000)
}

dashes = []
for i in range(0,10):
    dashes.append("".join(["▬"]*i))

def getRandomName():
    """Returns a str: random combination of words up to 20 characters."""
    
    length = random.randint(1,3)

    if length == 1:
        name = coolname.generate()
        name = name[2]
    else:
        name = coolname.generate_slug(length)

    if len(name) > 20:
        name = name[0:20] 

    name = name.replace('-', ' ')
    name = name.title()

    return name

async def createCharacter(pool, user_id, name):
    """Insert into given database default character info for the given ID"""
    async with pool.acquire() as conn:
        await conn.execute('INSERT INTO players (user_id, user_name) VALUES ($1, $2)', user_id, name)
        await conn.execute('INSERT INTO resources (user_id) VALUES ($1)', user_id)
        await conn.execute('INSERT INTO strategy (user_id) VALUES ($1)', user_id)
    await pool.release(conn)
    await createItem(pool, user_id, 20, 'Common', crit=0, weaponname='Wooden Spear', weapontype='Spear')

async def createItem(pool, owner_id, attack, rarity, crit = None, weaponname = None, weapontype=None, returnstats = False):
    """Create item with given or randomized stats. Returns a dict of the item's info if requested."""
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
        weaponname = getRandomName()

    async with pool.acquire() as conn:
        await conn.execute("""INSERT INTO items (weapontype, owner_id, attack, crit, weapon_name, rarity)
            VALUES ($1, $2, $3, $4, $5, $6)""", weapontype, owner_id, attack, crit, weaponname, rarity)
        await pool.release(conn)

    if returnstats:
        item_info = {
            'Attack' : attack,
            'Rarity' : rarity,
            'Crit' : crit,
            'Name' : weaponname,
            'Type' : weapontype
        }
        return item_info

async def getAllItemsFromPlayer(pool, user_id : int, sort):
    """Returns a list of all the items the specified user owns."""
    async with pool.acquire() as conn:
        if sort is not None:
            if sort.title() == 'Rarity':
                inv = await conn.fetch('SELECT item_id, weapontype, attack, crit, weapon_name, rarity, is_equipped FROM items WHERE owner_id = $1 AND is_equipped = True', user_id)
                other = await conn.fetch("SELECT item_id, weapontype, attack, crit, weapon_name, rarity, is_equipped FROM items WHERE owner_id = $1 AND is_equipped = False ORDER BY CASE rarity WHEN 'Legendary' THEN 1 WHEN 'Epic' THEN 2 WHEN 'Rare' THEN 3 WHEN 'Uncommon' THEN 4 ELSE 5 END", user_id)
            elif sort.title() == 'Crit':
                inv = await conn.fetch('SELECT item_id, weapontype, attack, crit, weapon_name, rarity, is_equipped FROM items WHERE owner_id = $1 AND is_equipped = True', user_id)
                other = await conn.fetch('SELECT item_id, weapontype, attack, crit, weapon_name, rarity, is_equipped FROM items WHERE owner_id = $1 AND is_equipped = False ORDER BY crit DESC', user_id)
            else:
                inv = await conn.fetch('SELECT item_id, weapontype, attack, crit, weapon_name, rarity, is_equipped FROM items WHERE owner_id = $1 AND is_equipped = True', user_id)
                other = await conn.fetch('SELECT item_id, weapontype, attack, crit, weapon_name, rarity, is_equipped FROM items WHERE owner_id = $1 AND is_equipped = False ORDER BY attack DESC', user_id)
        else:
            inv = await conn.fetch('SELECT item_id, weapontype, attack, crit, weapon_name, rarity, is_equipped FROM items WHERE owner_id = $1 AND is_equipped = True', user_id)
            other = await conn.fetch('SELECT item_id, weapontype, attack, crit, weapon_name, rarity, is_equipped FROM items WHERE owner_id = $1 AND is_equipped = False ORDER BY attack DESC', user_id)

        for item in other:
            inv.append(item)
        await pool.release(conn)
    
    return inv

async def verifyItemOwnership(pool, item_id : int, user_id : int):
    """Returns bool. True if the given item_id is in the user's inventory"""
    async with pool.acquire() as conn:
        item = await conn.fetchrow('SELECT weapon_name FROM items WHERE item_id = $1 AND owner_id = $2', item_id, user_id)
        await pool.release(conn)

        if item is None:
            return False
        else:
            return True

async def getEquippedItem(pool, user_id : int):
    """Returns the ID of the item equipped by the given player."""
    async with pool.acquire() as conn:
        item = await conn.fetchrow('SELECT item_id FROM items WHERE owner_id = $1 AND is_equipped = True', user_id)
        return item['item_id']

async def unequipItem(pool, user_id : int, item_id : int = None):
    """Sets to NULL the equipped_item value for the player."""
    async with pool.acquire() as conn:
        if item_id is None:
            item_id = await getEquippedItem(pool, user_id)

        await conn.execute('UPDATE items SET is_equipped = False WHERE item_id = $1', item_id)
        await conn.execute('UPDATE players SET equipped_item = NULL WHERE user_id = $1', user_id)
        await pool.release(conn)

async def equipItem(pool, item_id : int, user_id : int):
    """Equips an item on the given player. Does NOT verify ownership."""
    async with pool.acquire() as conn:
        await conn.execute('UPDATE items SET is_equipped = True WHERE item_id = $1', item_id)
        await conn.execute('UPDATE players SET equipped_item = $1 WHERE user_id = $2', item_id, user_id)
        await pool.release(conn)

async def getItem(pool, item_id : int):
    """Returns a dict of the given item ID."""
    async with pool.acquire() as conn:
        info = await conn.fetchrow('SELECT weapontype, owner_id, attack, crit, weapon_name, rarity, is_equipped FROM items WHERE item_id = $1', item_id)
        await pool.release(conn)

    item = {
        'ID' : item_id,
        'Type' : info['weapontype'],
        'Owner' : info['owner_id'],
        'Attack' : info['attack'],
        'Crit' : info['crit'],
        'Name' : info['weapon_name'],
        'Rarity' : info['rarity'],
        'Equip' : info['is_equipped']
    }

    return item

async def deleteItem(pool, item_id : int):
    """Deletes from the database the given item."""
    async with pool.acquire() as conn:
        await conn.execute('DELETE FROM items WHERE item_id = $1', item_id)
        await pool.release(conn)

async def setItemOwner(pool, item_id : int, user_id : int):
    """Changes the owner_id of the given item."""
    async with pool.acquire() as conn:
        await conn.execute('UPDATE items SET owner_id = $1 WHERE item_id = $2', user_id, item_id)
        await pool.release(conn)

async def setItemName(pool, item_id : int, name : str):
    """Changes the item_name of the given item."""
    async with pool.acquire() as conn:
        await conn.execute('UPDATE items SET weapon_name = $1 WHERE item_id = $2', name, item_id)
        await pool.release(conn)

async def increaseItemAttack(pool, item_id : int, increase : int):
    """Increases the attack of the given item by the amount given."""
    async with pool.acquire() as conn:
        await conn.execute('UPDATE items SET attack = attack + $1 WHERE item_id = $2', increase, item_id)
        await pool.release(conn)

async def sellAllItems(pool, user_id : int, rarity : str):
    """Deletes all items of a given player and rarity. Returns two integers: amount of items deleted, corresponding gold value."""
    async with pool.acquire() as conn:
        amount = await conn.fetchval('SELECT COUNT(item_id) FROM items WHERE owner_id = $1 AND rarity = $2 AND is_equipped = FALSE', user_id, rarity)
        
        if amount == 0:
            await pool.release(conn)
            return 0, 0
        
        gold = random.randint(Weaponvalues[rarity][0], Weaponvalues[rarity][1]) * amount
        await conn.execute('UPDATE players SET gold = gold + $1 WHERE user_id = $2', gold, user_id)
        await conn.execute('DELETE FROM items WHERE owner_id = $1 AND rarity = $2 AND is_equipped = FALSE', user_id, rarity)
        await pool.release(conn)
    return amount, gold

async def createAcolyte(pool, owner_id, acolyte_name):
    """Inserts new acolyte of given user and type into database"""
    async with pool.acquire() as conn:
        await conn.execute('INSERT INTO acolytes (owner_id, acolyte_name) VALUES ($1, $2)', owner_id, acolyte_name)
        await pool.release(conn)

async def checkAcolyteLevel(pool, ctx, instance_id):
    """Updates given acolyte's level if necessary. Prints its own output."""
    async with pool.acquire() as conn:
        current = await conn.fetchrow('SELECT acolyte_name, lvl, xp FROM acolytes WHERE instance_id = $1', instance_id)
        if current['lvl'] < getAcolyteLevel(current['xp']):
            await conn.execute('UPDATE acolytes SET lvl = lvl + 1 WHERE instance_id = $1', instance_id)
            await pool.release(conn)
            
            await ctx.send(f"{current['acolyte_name']} levelled up to level {current['lvl'] + 1}!")

async def checkLevel(pool, ctx, user_id, aco1=None, aco2=None):
    """Updates given player's level if necessary, as well that player's acolytes. Prints its own output."""
    async with pool.acquire() as conn:
        current = await conn.fetchrow('SELECT lvl, xp, user_name FROM Players WHERE user_id = $1', user_id)
        if current['lvl'] < calcLevel(current['xp']):
            #Give some rewards
            gold = (current['lvl'] + 1) * 500
            rubidic = math.ceil((current['lvl'] + 1) / 10)
            await conn.execute('UPDATE Players SET lvl = lvl + 1, gold = gold + $1, rubidic = rubidic + $2 WHERE user_id = $3', gold, rubidic, user_id)

            #Send level-up message
            embed = discord.Embed(title=f"You've levelled up to level {current['lvl']+1}!", color=0xBEDCF6)
            embed.add_field(name=f"{current['user_name']}, you gained some rewards:", value=f'**Gold:** {gold}\n**Rubidics:** {rubidic}')
            await ctx.send(embed=embed)
        await pool.release(conn)
    if aco1 is not None:
        await checkAcolyteLevel(pool, ctx, aco1)
    if aco2 is not None:
        await checkAcolyteLevel(pool, ctx, aco2)

def getAcolyteLevel(xp):
    """Calculate an acolyte's level. Returns an int."""
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
    """Calculate a player's level. Returns an int."""
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

async def getLevel(pool, user_id : int):
    """Returns the given player's level (int)."""
    async with pool.acquire() as conn:
        level = await conn.fetchrow('SELECT lvl FROM Players WHERE user_id = $1', user_id)
        return level['lvl']

async def getAcolyteXP(pool, instance_id : int):
    """Returns a record/dict of acolyte's lvl and xp."""
    async with pool.acquire() as conn:
        info = await conn.fetchrow('SELECT lvl, xp FROM acolytes WHERE instance_id = $1', instance_id)
        await pool.release(conn)

    return info

async def getAcolyteAttack(pool, instance_id : int):
    """Returns an acolyte's ATK, CRIT, and HP (integers)."""
    info = await getAcolyteByID(pool, instance_id)
    if info['Dupes'] > 5:
        info['Dupes'] = 5
    if info['Rarity'] == 4:
        attack = int(info['Attack'] + (info['Scale'] * info['Level']) + (info['Dupes'] * 7.5))
        crit = int(info['Crit'] + info['Dupes'] * 1.5)
        hp = int(info['HP'] + (info['Dupes'] * 30))
    elif info['Rarity'] == 5:
        attack = int(info['Attack'] + (info['Scale'] * info['Level']) + (info['Dupes'] * 10))
        crit = int(info['Crit'] + info['Dupes'] * 2)
        hp = int(info['HP'] + (info['Dupes'] * 40))
    else:
        attack = int(info['Attack'] + (info['Scale'] * info['Level']) + (info['Dupes'] * 5))
        crit = int(info['Crit'] + info['Dupes'])
        hp = int(info['HP'] + (info['Dupes'] * 20))
    return attack, crit, hp

async def getAttack(pool, user_id, returnothers = False):
    """Returns a player's attack and crit (integers). If specified, also returns HP, class, and acolytes."""
    charattack, weaponattack, guildattack, acolyteattack, attack, crit, hp = 20, 0, 0, 0, 0, 5, 500
    async with pool.acquire() as conn:
        char = await conn.fetchrow('SELECT lvl, equipped_item, acolyte1, acolyte2, occupation, prestige FROM players WHERE user_id = $1', user_id)
        charattack += char['lvl'] * 2

        if char['equipped_item'] is not None:
            item = await conn.fetchrow('SELECT attack, crit FROM items WHERE item_id = $1', char['equipped_item'])
            weaponattack = item['attack']
            crit += item['crit']

        if char['acolyte1'] is not None:
            a1atk, a1crit, a1hp = await getAcolyteAttack(pool, char['acolyte1'])
            acolyteattack += a1atk
            crit += a1crit
            hp += a1hp

        if char['acolyte2'] is not None:
            a2atk, a2crit, a2hp = await getAcolyteAttack(pool, char['acolyte2'])
            acolyteattack += a2atk
            crit += a2crit
            hp += a2hp

        if char['occupation'] == 'Soldier':
            charattack = math.floor(charattack * 1.2) + 10
        if char['occupation'] == 'Blacksmith':
            weaponattack = math.floor(weaponattack * 1.1) + 10
        if char['occupation'] == 'Scribe':
            crit += 10
        if char['occupation'] == 'Leatherworker':
            hp += 200

        try:
            guild = await getGuildFromPlayer(pool, user_id)
            guild_level = await getGuildLevel(pool, guild['ID'])
            if guild['Type'] == 'Brotherhood':
                guildattack = guild_level * (guild_level + 1) / 2
                crit = crit + guild_level
        except TypeError:
            pass

        #Add prestige bonus
        charattack += 30 * char['prestige']
        hp += 50 * char['prestige']

        attack = charattack + weaponattack + acolyteattack + guildattack

        await pool.release(conn)

    if not returnothers:
        return int(attack), crit
    else:
        return int(attack), crit, hp, char['occupation'], char['acolyte1'], char['acolyte2'] #returns Class, then acolytes

def getAcolyteByName(name : str):
    """Returns a dict of the general info of the acolyte."""
    with open(ACOLYTE_PATH, 'r') as acolyte_list:
        acolytes = json.load(acolyte_list) #acolytes is a dict
        acolyte_list.close()
    return acolytes[name]

async def getAcolyteByID(pool, instance : int):
    """Returns a dict, containing the info specific to the given ID along with the general info."""
    async with pool.acquire() as conn:
        info = await conn.fetchrow('SELECT acolyte_name, lvl, is_equipped, duplicate FROM Acolytes WHERE instance_id = $1', instance)
        acolyte = getAcolyteByName(info['acolyte_name'])

        acolyte['Level'] = info['lvl']
        acolyte['ID'] = instance
        acolyte['Equip'] = info['is_equipped']
        acolyte['Dupes'] = info['duplicate']
        
        await pool.release(conn)

    return acolyte

async def getAcolyteFromPlayer(pool, user_id : int): #Returns the IDs of the equipped acolytes
    """Returns the IDs of the player's equipped acolytes (integers)."""
    async with pool.acquire() as conn:
        acolytes = await conn.fetchrow('SELECT acolyte1, acolyte2 FROM players WHERE user_id = $1', user_id)
        acolyte1 = acolytes['acolyte1']
        acolyte2 = acolytes['acolyte2']
        await pool.release(conn)
    
    return acolyte1, acolyte2

async def getAllAcolytesFromPlayer(pool, user_id : int): #Returns tuple of every acolyte a player owns
    """Returns a list of records/dicts of all the acolyte's a player owns."""
    async with pool.acquire() as conn:
        inv = await conn.fetch("""SELECT instance_id, acolyte_name, lvl, is_equipped, duplicate FROM acolytes
                WHERE owner_id = $1 AND (is_equipped = 1 OR is_equipped = 2)""", user_id)
        other = await conn.fetch("""SELECT instance_id, acolyte_name, lvl, is_equipped, duplicate FROM acolytes
                WHERE owner_id = $1 AND is_equipped = 0 ORDER BY acolyte_name""", user_id)
        for item in other: 
            inv.append(item)
        await pool.release(conn)

    return inv

async def checkDuplicate(pool, user_id : int, acolyte_name : str):
    """Verifies if an acolyte (by name) is owned by a player. Returns a record/dict of the acolyte (ID and duplicates) if one exists."""
    async with pool.acquire() as conn:
        acolyte = await conn.fetchrow('SELECT instance_id, duplicate FROM acolytes WHERE owner_id = $1 AND acolyte_name = $2', user_id, acolyte_name)
        if acolyte is None:
            return None
        else:
            return acolyte

async def verifyAcolyteOwnership(pool, instance_id : int, user_id : int):
    """Returns a bool: True if given acolyte ID is in player's tavern."""
    async with pool.acquire() as conn:
        acolyte = await conn.fetchrow('SELECT instance_id FROM Acolytes WHERE instance_id = $1 AND owner_id = $2', instance_id, user_id)
        await pool.release(conn)
        
    if acolyte is None:
        return False
    else:
        return True #Then something came up and teh acolyte actually is in this player's tavern

async def unequipAcolyte(pool, instance_id : int, slot : int = None, user_id : int = None):
    """Unequips an acolyte from a player."""
    async with pool.acquire() as conn:
        await conn.execute('UPDATE Acolytes SET is_equipped = 0 WHERE instance_id = $1', instance_id)

        if slot == 1:
            await conn.execute('UPDATE players SET acolyte1 = NULL where user_id = $1', user_id)
        if slot == 2:
            await conn.execute('UPDATE players SET acolyte2 = NULL where user_id = $1', user_id)

        await pool.release(conn)

async def equipAcolyte(pool, instance_id : int, slot : int, user_id : int):
    """Equip an acolyte to a player in the given slot."""
    async with pool.acquire() as conn:
        await conn.execute('UPDATE Acolytes SET is_equipped = $1 WHERE instance_id = $2', slot, instance_id)
        if slot == 1:
            await conn.execute('UPDATE Players SET acolyte1 = $1 WHERE user_id = $2', instance_id, user_id)
        else:
            await conn.execute('UPDATE Players SET acolyte2 = $1 WHERE user_id = $2', instance_id, user_id)
        
        await pool.release(conn)

async def addAcolyteDuplicate(pool, instance_id : int):
    """Sets the duplicates of an acolyte a player owns."""
    async with pool.acquire() as conn:
        await conn.execute('UPDATE acolytes SET duplicate = duplicate + 1 WHERE instance_id = $1', instance_id)
        await pool.release(conn)

async def giveAcolyteXP(pool, amount : int, instance_id : int):
    """Update the xp of the given acolyte."""
    async with pool.acquire() as conn:
        await conn.execute('UPDATE acolytes SET xp = xp + $1 WHERE instance_id = $2', amount, instance_id)
        await pool.release(conn)

async def givePlayerXP(pool, amount : int, user_id : int):
    """Update the xp of the given player."""
    async with pool.acquire() as conn:
        await conn.execute('UPDATE players SET xp = xp + $1 WHERE user_id = $2', amount, user_id)
        await pool.release(conn)

async def createGuild(pool, name, guild_type, leader, icon):
    """Creates an association with the given info."""
    async with pool.acquire() as conn:
        await conn.execute('INSERT INTO guilds (guild_name, guild_type, leader_id, guild_icon) VALUES ($1, $2, $3, $4)', name, guild_type, leader, icon)
        guild_id = await conn.fetchrow('SELECT guild_id FROM guilds WHERE leader_id = $1', leader)
        await conn.execute("UPDATE players SET guild = $1, gold = gold - 15000, guild_rank = 'Leader' WHERE user_id = $2", guild_id['guild_id'], leader)
        await pool.release(conn)

async def joinGuild(pool, guild_id, user_id): #DOES NOT VERIFY IF THEY'RE ALREADY IN A GUILD
    """Adds a specific player to a guild."""
    async with pool.acquire() as conn:
        await conn.execute("UPDATE players SET guild = $1, guild_rank = 'Member' WHERE user_id = $2", guild_id, user_id)
        await pool.release(conn)

async def leaveGuild(pool, user_id : int): #DOES NOT VERIFY IF MEMBER LEAVING IS LEADER USE ON MEMBERS ONLYYY
    """Removes a player from a guild."""
    async with pool.acquire() as conn:
        await conn.execute('UPDATE Players SET guild = NULL, guild_rank = NULL WHERE user_id = $1', user_id)
        await pool.release(conn)

async def getGuildFromPlayer(pool, user_id : int):
    """Returns a dict containing the info of the guild the specified player is in.
    Dict: ID, Name, Type, XP, Leader, Desc, Icon, Join"""
    async with pool.acquire() as conn:
        guild_id = await conn.fetchval('SELECT guild FROM players WHERE user_id = $1', user_id)
        await pool.release(conn) 
    
    return await getGuildByID(pool, guild_id)

async def getGuildByID(pool, guild_id : int):
    """Returns a dict containing the info of the specified guild.
    Dict: ID, Name, Type, XP, Leader, Desc, Icon, Join"""
    async with pool.acquire() as conn:
        info = await conn.fetchrow('SELECT guild_id, guild_name, guild_type, guild_xp, leader_id, guild_desc, guild_icon, join_status FROM guilds WHERE guild_id = $1', guild_id)
        await pool.release(conn)

    guild = {
        'ID' : info['guild_id'],
        'Name' : info['guild_name'],
        'Type' : info['guild_type'],
        'XP' : info['guild_xp'],
        'Leader' : info['leader_id'],
        'Desc' : info['guild_desc'],
        'Icon' : info['guild_icon'],
        'Join' : info['join_status']
    }

    return guild

async def getGuildLevel(pool, guild_id : int, returnline = False):
    """Returns the level (int) of the specified guild. If requested, also gives a str representing its levelling status."""
    async with pool.acquire() as conn:
        level = await conn.fetchval('SELECT guild_level FROM guild_levels WHERE guild_id = $1', guild_id)
        if level > 10:
            level = 10

        if returnline: #Also create a string to show progress
            xp = await conn.fetchval('SELECT guild_xp FROM guilds WHERE guild_id = $1', guild_id)
            progress = int((xp % 1000000) / 100000)
            progressStr = dashes[progress]+'◆'+dashes[9-progress]
            await pool.release(conn)
            return level, progressStr
        else:
            await pool.release(conn)
            return level

async def getGuildMemberCount(pool, guild_id : int):
    """Returns the amount of players in the specified guild (int)."""
    async with pool.acquire() as conn:
        count = await conn.fetchrow('SELECT member_count FROM guild_membercount WHERE guild_id = $1', guild_id)
        await pool.release(conn)
    
    return count['member_count']

async def getGuildCapacity(pool, guild_id : int):
    """Returns the maximum amount of player's a guild can have (int)."""
    async with pool.acquire() as conn:
        capacity = await conn.fetchval('SELECT capacity FROM guild_capacities WHERE guild_id = $1', guild_id)
        if capacity > 50:
            capacity = 50
        await pool.release(conn)
        
    return capacity

async def giveGuildXP(pool, amount : int, guild_id : int):
    """Add to the given guild's xp."""
    async with pool.acquire() as conn:
        await conn.execute('UPDATE guilds SET guild_xp = guild_xp + $1 WHERE guild_id = $2', amount, guild_id)
        await pool.release(conn)

async def getGuildXP(pool, guild_id : int):
    """Returns an int of the total xp the specified guild has."""
    async with pool.acquire() as conn:
        xp = await conn.fetchrow('SELECT guild_xp FROM guilds WHERE guild_id = $1', guild_id)
        await pool.release(conn)
    
    return xp['guild_xp']

async def getGuildMembers(pool, guild_id : int):
    """Returns a list of all the members in the specified guild."""
    async with pool.acquire() as conn:
        members = await conn.fetch("""SELECT user_id, user_name, guild_rank FROM players WHERE guild = $1
            ORDER BY CASE guild_rank WHEN 'Leader' then 1
            WHEN 'Officer' THEN 2
            WHEN 'Adept' THEN 3
            ELSE 4 END""", guild_id)
        await pool.release(conn)
    
    return members

async def setGuildDescription(pool, description, guild_id : int):
    """Set the description of the given guild."""
    async with pool.acquire() as conn:
        await conn.execute('UPDATE guilds SET guild_desc = $1 WHERE guild_id = $2', description, guild_id)
        await pool.release(conn)

async def setGuildIcon(pool, url : str, guild_id : int):
    """Set the icon of the given guild."""
    async with pool.acquire() as conn:
        await conn.execute('UPDATE guilds SET guild_icon = $1 WHERE guild_id = $2', url, guild_id)
        await pool.release(conn)

async def lockGuild(pool, guild_id : int):
    """Set the lock-status of the given guild to closed."""
    async with pool.acquire() as conn:
        await conn.execute("UPDATE guilds SET join_status = 'closed' WHERE guild_id = $1", guild_id)
        await pool.release(conn)

async def unlockGuild(pool, guild_id : int):
    """Set the lock-status of the given guilt to open."""
    async with pool.acquire() as conn:
        await conn.execute("UPDATE guilds SET join_status = 'open' WHERE guild_id = $1", guild_id)
        await pool.release(conn)

async def changeGuildRank(pool, rank : str, user_id : int):
    """Set the guild_rank of the specified player."""
    async with pool.acquire() as conn:
        await conn.execute('UPDATE players SET guild_rank = $1 WHERE user_id = $2', rank, user_id)
        
        if rank == "Leader":
            guild = await getGuildFromPlayer(pool, user_id)
            await conn.execute('UPDATE guilds SET leader_id = $1 WHERE guild_id = $2', user_id, guild['ID'])  

        await pool.release(conn)

async def getAdventure(pool, user_id : int):
    """Returns a dict of the player's adventure info.
    Dict: adventure (int specifying time), destination (str)"""
    async with pool.acquire() as conn:
        adventure = await conn.fetchrow('SELECT adventure, destination FROM players WHERE user_id = $1', user_id)
        

        adv = {
            'adventure' : adventure['adventure'],
            'destination' : adventure['destination']
        }

        #Implement Radishes Acolyte Passive (here is best)
        #What this does is change the start time in such a way to increase the total length by 5% for later calculations
        if adventure['destination'] == 'EXPEDITION':
            acolyte1, acolyte2 = await getAcolyteFromPlayer(pool, user_id)
            if acolyte1 is not None:
                a1 = await getAcolyteByID(pool, acolyte1)
            else:
                a1 = {'Name' : None}
            if acolyte2 is not None:
                a2 = await getAcolyteByID(pool, acolyte2)
            else:
                a2 = {'Name' : None}

            try:
                if a1['Name'] == 'Radishes' or a2['Name'] == 'Radishes':
                    time_diff = int(time.time() - adventure['adventure'])
                    ten_percent_bonus = int(time_diff / 10)
                    adv['adventure'] -= ten_percent_bonus
            except KeyError:
                pass

        await pool.release(conn)
    
    return adv

async def getLocation(pool, user_id : int):
    """Returns the player's current location (str)."""
    async with pool.acquire() as conn:
        location = await conn.fetchval('SELECT loc FROM players WHERE user_id = $1', user_id)
        await pool.release(conn)
    
    return location

async def giveMat(pool, material : str, amount : int, user_id : int):
    """Gives the specified player a resource of the given type."""
    async with pool.acquire() as conn:

        if material == 'wheat':
            await conn.execute('UPDATE resources SET wheat = wheat + $1 WHERE user_id = $2', amount, user_id)
        if material == 'oat':
            await conn.execute('UPDATE resources SET oat = oat + $1 WHERE user_id = $2', amount, user_id)
        if material == 'wood':
            await conn.execute('UPDATE resources SET wood = wood + $1 WHERE user_id = $2', amount, user_id)
        if material == 'reeds':
            await conn.execute('UPDATE resources SET reeds = reeds + $1 WHERE user_id = $2', amount, user_id)
        if material == 'pine':
            await conn.execute('UPDATE resources SET pine = pine + $1 WHERE user_id = $2', amount, user_id)
        if material == 'moss':
            await conn.execute('UPDATE resources SET moss = moss + $1 WHERE user_id = $2', amount, user_id)
        if material == 'iron':
            await conn.execute('UPDATE resources SET iron = iron + $1 WHERE user_id = $2', amount, user_id)
        if material == 'cacao':
            await conn.execute('UPDATE resources SET cacao = cacao + $1 WHERE user_id = $2', amount, user_id)
        if material == 'fur':
            await conn.execute('UPDATE resources SET fur = fur + $1 WHERE user_id = $2', amount, user_id)
        if material == 'bone':
            await conn.execute('UPDATE resources SET bone = bone + $1 WHERE user_id = $2', amount, user_id)
        if material == 'silver':
            await conn.execute('UPDATE resources SET silver = silver + $1 WHERE user_id = $2', amount, user_id)

        await pool.release(conn)

async def takeMat(pool, material : str, amount : int, user_id : int): #DEPRECATED
    """DEPRECATED - USE giveMat with negative input.
    Removes from the specified player a given resource. Does not verify valid removal."""
    async with pool.acquire() as conn:

        if material == 'wheat':
            await conn.execute('UPDATE resources SET wheat = wheat - $1 WHERE user_id = $2', amount, user_id)
        if material == 'oat':
            await conn.execute('UPDATE resources SET oat = oat - $1 WHERE user_id = $2', amount, user_id)
        if material == 'wood':
            await conn.execute('UPDATE resources SET wood = wood - $1 WHERE user_id = $2', amount, user_id)
        if material == 'reeds':
            await conn.execute('UPDATE resources SET reeds = reeds - $1 WHERE user_id = $2', amount, user_id)
        if material == 'pine':
            await conn.execute('UPDATE resources SET pine = pine - $1 WHERE user_id = $2', amount, user_id)
        if material == 'moss':
            await conn.execute('UPDATE resources SET moss = moss - $1 WHERE user_id = $2', amount, user_id)
        if material == 'iron':
            await conn.execute('UPDATE resources SET iron = iron - $1 WHERE user_id = $2', amount, user_id)
        if material == 'cacao':
            await conn.execute('UPDATE resources SET cacao = cacao - $1 WHERE user_id = $2', amount, user_id)

        await pool.release(conn)

async def getPlayerMat(pool, material : str, user_id : int):
    """Returns the amount of materials of given type the player owns (int)."""
    async with pool.acquire() as conn:
        if material == 'wheat':
            c = await conn.fetchrow('SELECT wheat FROM resources WHERE user_id = $1', user_id)
        if material == 'oat':
            c = await conn.fetchrow('SELECT oat FROM resources WHERE user_id = $1', user_id)
        if material == 'wood':
            c = await conn.fetchrow('SELECT wood FROM resources WHERE user_id = $1', user_id)
        if material == 'reeds':
            c = await conn.fetchrow('SELECT reeds FROM resources WHERE user_id = $1', user_id)
        if material == 'pine':
            c = await conn.fetchrow('SELECT pine FROM resources WHERE user_id = $1', user_id)
        if material == 'moss':
            c = await conn.fetchrow('SELECT moss FROM resources WHERE user_id = $1', user_id)
        if material == 'iron':
            c = await conn.fetchrow('SELECT iron FROM resources WHERE user_id = $1', user_id)
        if material == 'cacao':
            c = await conn.fetchrow('SELECT cacao FROM resources WHERE user_id = $1', user_id)
        if material == 'fur':
            c = await conn.fetchrow('SELECT fur FROM resources WHERE user_id = $1', user_id)
        if material == 'bone':
            c = await conn.fetchrow('SELECT bone FROM resources WHERE user_id = $1', user_id)
        if material == 'silver':
            c = await conn.fetchrow('SELECT silver FROM resources WHERE user_id = $1', user_id)

        await pool.release(conn) 
    
    return c[0]

async def resetResources(pool, user_id : int):
    """Set all resources to 0 for the given player."""
    async with pool.acquire() as conn:
        await conn.execute('UPDATE resources SET fur = 0, bone = 0, iron = 0, silver = 0, wood = 0, wheat = 0, oat = 0, reeds = 0, pine = 0, moss = 0, cacao = 0 WHERE user_id = $1', user_id)
        await pool.release(conn)

async def giveGold(pool, amount : int, user_id : int):
    """Gives the specified gold the given amount of gold."""
    async with pool.acquire() as conn:
        await conn.execute('UPDATE players SET gold = gold + $1 WHERE user_id = $2', amount, user_id)
        await pool.release(conn)

async def getGold(pool, user_id : int):
    """Returns the amount of gold a player has (int)."""
    async with pool.acquire() as conn:
        gold = await conn.fetchrow('SELECT gold FROM players WHERE user_id = $1', user_id)
        return gold['gold']

async def setGold(pool, user_id : int, gold : int):
    """Set the amount of gold a player has."""
    async with pool.acquire() as conn:
        await conn.execute('UPDATE players SET gold = $1 WHERE user_id = $2', gold, user_id)
        await pool.release(conn)

async def getClass(pool, user_id : int):
    """Returns the class of the given player (str)."""
    async with pool.acquire() as conn:
        role = await conn.fetchrow('SELECT occupation FROM players WHERE user_id = $1', user_id)
        await pool.release(conn)

    try:
        return role['occupation']
    except TypeError:
        return None

async def getPlayerCount(pool):
    """Returns the amount of player's in the database (int)."""
    async with pool.acquire() as conn:
        records = await conn.fetchrow('SELECT COUNT(*) FROM Players')
        await pool.release(conn)

    return records[0]

async def getPlayerByID(pool, user_id: int):
    """Returns the info of a player of the specified ID.
    Dict: Num, Name, Level, Item, Acolyte1, Acolyte2, Guild, Rank (guild_rank), Gold, 
    Class, Origin, Location, 
    pvpwins, pvpfights, bosswins, bossfights, prestige"""
    async with pool.acquire() as conn:
        info = await conn.fetchrow("""SELECT num, user_name, lvl, equipped_item, acolyte1, acolyte2, guild, guild_rank, 
            gold, occupation, origin, loc, pvpwins, pvpfights, bosswins, bossfights, prestige
            FROM players WHERE user_id = $1""", user_id)
        await pool.release(conn)

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
        'bossfights' : info[15],
        'prestige' : info[16]
    }

    return player

async def getPlayerByNum(pool, num : int):
    """Returns the gold, ID (integers), and name (str) of the player with the corresponding number."""
    async with pool.acquire() as conn:
        info = await conn.fetchrow('SELECT gold, user_id, user_name FROM players WHERE num = $1', num)
        await pool.release(conn)
    
    gold = info['gold'] 
    idnum = info['user_id']
    name = info['user_name']

    return gold, idnum, name

async def setPlayerClass(pool, role : str, user_id : int):
    """Sets the player's class."""
    async with pool.acquire() as conn:
        await conn.execute('UPDATE players SET occupation = $1 WHERE user_id = $2', role, user_id)
        await pool.release(conn)

async def setPlayerOrigin(pool, role : str, user_id : int):
    """Sets the player's origin."""
    async with pool.acquire() as conn:
        await conn.execute('UPDATE players SET origin = $1 WHERE user_id = $2', role, user_id)
        await pool.release(conn)

async def getPlayerXP(pool, user_id : int):
    """Returns the player's level and xp (integers)."""
    async with pool.acquire() as conn:
        info = await conn.fetchrow('SELECT lvl, xp FROM players WHERE user_id = $1', user_id)
        await pool.release(conn)

    level = info['lvl'] 
    xp = info['xp']

    return level, xp

async def resetPlayerLevel(pool, user_id : int): #DONT USE THIS
    """Sets the player's level and xp to 0. USE ONLY FOR PRESTIGE"""
    async with pool.acquire() as conn:
        await conn.execute('UPDATE players SET lvl = 0, xp = 0 WHERE user_id = $1', user_id)
        await pool.release(conn)

async def setPlayerName(pool, user_id : int, name : str):
    """Sets the payer's user_name."""
    async with pool.acquire() as conn:
        await conn.execute('UPDATE players SET user_name = $1 WHERE user_id = $2', name, user_id)
        await pool.release(conn)

async def giveBountyRewards(pool, user_id : int, gold : int, xp : int, victory : bool):
    """Update the player's gold, xp, bosswins, and bossfights. For use in PvE."""
    async with pool.acquire() as conn:
        if victory:
            await conn.execute('UPDATE players SET gold = gold + $1, xp = xp + $2, bosswins = bosswins + 1, bossfights = bossfights + 1 WHERE user_id = $3', gold, xp, user_id)
        else:
            await conn.execute('UPDATE players SET gold = gold + $1, xp = xp + $2, bossfights = bossfights + 1 WHERE user_id = $3', gold, xp, user_id)

        await pool.release(conn)

async def giveAdventureRewards(pool, xp : int, gold : int, location : str, user_id : int):
    """Update the player's gold, xp, location, destination, and adventure. For use in Travel."""
    async with pool.acquire() as conn:
        await conn.execute("""UPDATE players SET 
            xp = xp + $1, gold = gold + $2, loc = $3, 
            adventure = NULL, destination = NULL 
            WHERE user_id = $4""", xp, gold, location, user_id)
        await pool.release(conn)

async def setAdventure(pool, adventure : int, destination : str, user_id : int):
    """Sets the player's adventure and destination.
    Adventure should be an int specifying time."""
    async with pool.acquire() as conn:
        await conn.execute('UPDATE players SET adventure = $1, destination = $2 WHERE user_id = $3', adventure, destination, user_id)
        await pool.release(conn)

async def getTopXP(pool):
    """Returns a list of records/dicts giving the top 5 players in xp.
    Record: user_id, user_name, lvl, xp, prestige"""
    async with pool.acquire() as conn:
        board = await conn.fetch("""SELECT user_id, user_name, lvl, xp, prestige FROM players
            ORDER BY prestige DESC, xp DESC LIMIT 5""")
        await pool.release(conn)
    
    return board

async def getTopBosses(pool):
    """Returns a list of records/dicts giving the top 5 players in bosswins.
    Record: user_id, user_name, bosswins"""
    async with pool.acquire() as conn:
        board = await conn.fetch("""SELECT user_id, user_name, bosswins FROM players
            ORDER BY bosswins DESC LIMIT 5""")
        await pool.release(conn)
    
    return board

async def getTopGold(pool):
    """Returns a list of records/dicts giving the top 5 players in gold.
    Record: user_id, user_name, gold"""
    async with pool.acquire() as conn:
        board = await conn.fetch("""SELECT user_id, user_name, gold FROM players
            ORDER BY gold DESC LIMIT 5""")
        await pool.release(conn)

    return board

async def getTopPvP(pool):
    """Returns a list of records/dicts giving the top 5 players in pvpwins.
    Record: user_id, user_name, pvpwins"""
    async with pool.acquire() as conn:
        board = await conn.fetch("""SELECT user_id, user_name, pvpwins FROM players
            ORDER BY bosswins DESC LIMIT 5""")
        await pool.release(conn)

    return board  

async def getRubidics(pool, user_id : int):
    """Returns a record/dict giving the rubidics and pity info of the given player.
    Record: rubidic, pitycounter (integers)"""
    async with pool.acquire() as conn:
        info = await conn.fetchrow('SELECT rubidic, pitycounter FROM players WHERE user_id = $1', user_id)
        await pool.release(conn)

    return info

async def resetPityCounter(pool, user_id : int): #CURRENTLY NOT IN USE
    """Sets pitycounter to 0."""
    async with pool.acquire() as conn:
        await conn.execute('UPDATE players SET pitycounter = 0 WHERE user_id = $1', user_id)
        await pool.release(conn)

async def setPityCounter(pool, user_id : int, pity : int):
    """Set pitycounter to specified amount."""
    async with pool.acquire() as conn:
        await conn.execute('UPDATE players SET pitycounter = $1 WHERE user_id = $2', pity, user_id)
        await pool.release(conn)

async def setRubidics(pool, user_id, rubidics : int):
    """Set rubidics to specified amount."""
    async with pool.acquire() as conn:
        await conn.execute('UPDATE players SET rubidic = $1 WHERE user_id = $2', rubidics, user_id)
        await pool.release(conn)

async def giveRubidics(pool, amount : int, user_id : int):
    """Gives the given amount of rubidics to a player."""
    async with pool.acquire() as conn:
        await conn.execute('UPDATE players SET rubidic = rubidic + $1 WHERE user_id = $2', amount, user_id)
        await pool.release(conn)

async def setStrategy(pool, user_id : int, attack : int, block : int, parry : int, heal : int, bide : int):
    """Sets the strategy record of a given player."""
    async with pool.acquire() as conn:
        await conn.execute('UPDATE strategy SET attack = $1, block = $2, parry = $3, heal = $4, bide = $5 WHERE user_id = $6', attack, block, parry, heal, bide, user_id)
        await pool.release(conn)

async def getStrategy(pool, user_id : int):
    """Returns a record/dict of the strategy of a certain player.
    Record: attack, block, parry, heal, bide (integers adding up to 100)."""
    async with pool.acquire() as conn:
        strategy = await conn.fetchrow('SELECT attack, block, parry, heal, bide FROM strategy WHERE user_id = $1', user_id)
        await pool.release(conn)

    return strategy

async def prestigeCharacter(pool, user_id : int):
    """Adds 1 to a player's prestige and returns the new amount (int)."""
    async with pool.acquire() as conn:
        await pool.execute('UPDATE players SET prestige = prestige + 1 WHERE user_id = $1', user_id)
        prestige = await pool.fetchval('SELECT prestige FROM players WHERE user_id = $1', user_id)
        await pool.release(conn)

    return prestige