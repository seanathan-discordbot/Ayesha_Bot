import discord
import asyncio

from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

import aiosqlite
from Utilities import Checks, AssetCreation, PageSourceMaker

import random

PATH = 'PATH'

WeaponValues = (
    ('Common', 1, 20),
    ('Uncommon', 15, 30),
    ('Rare', 75, 150),
    ('Epic', 400, 700),
    ('Legendary', 2000, 3000)
)

# WEAPON TYPES
# 1. Spear
# 2. Sword
# 3. Dagger
# 4. Bow
# 5. Trebuchet
# 6. Gauntlets
# 7. Staff
# 8. Greatsword
# 9. Axe
# 10. Sling
# 11. Javelin
# 12. Falx
# 13. Mace

class Items(commands.Cog):

    def __init__(self, client):
        self.client = client

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('Items is ready.')

    #INVISIBLE
    def write(self, start, inv, player):
        embed = discord.Embed(title=f'{player}\'s Inventory', color=0xBEDCF6)

        iteration = 0
        while start < len(inv) and iteration < 5: #Loop til 5 entries or none left
            if inv[start][7] == 1:
                embed.add_field(name = f'{inv[start][5]}: `{inv[start][0]}` [Equipped]',
                    value = f'**Attack:** {inv[start][3]}, **Crit:** {inv[start][4]}%, **Type:** {inv[start][1]}, **Rarity:** {inv[start][6]}',
                    inline=False
                )
            else:
                embed.add_field(name = f'{inv[start][5]}: `{inv[start][0]}`',
                    value = f'**Attack:** {inv[start][3]}, **Crit:** {inv[start][4]}%, **Type:** {inv[start][1]}, **Rarity:** {inv[start][6]}',
                    inline=False
                )
            iteration += 1
            start += 1
        return embed
    
    #COMMANDS
    @commands.command(aliases=['i', 'inv'], description='View your inventory of items')
    @commands.check(Checks.is_player)
    async def inventory(self, ctx):
        user = (ctx.author.id,)
        async with aiosqlite.connect(PATH) as conn:
            c = await conn.execute("""
                SELECT * FROM Items
                WHERE owner_id = ? AND is_equipped = 1""",
                user)
            inv = await c.fetchall()
            c = await conn.execute("""
                SELECT * FROM Items
                WHERE owner_id = ? AND is_equipped = 0""",
                user)
            for item in (await c.fetchall()): 
                inv.append(item) 
            invpages = []
            for i in range(0, len(inv), 5): #list 5 entries at a time
                invpages.append(self.write(i, inv, ctx.author.display_name)) # Write will create the embeds
        if len(invpages) == 0:
            await ctx.reply('Your inventory is empty!')
        else:
            inventory = menus.MenuPages(source=PageSourceMaker.PageMaker(invpages), clear_reactions_after=True, delete_message_after=True)
            await inventory.start(ctx)

    @commands.command(aliases=['use','wield'], brief='<item_id : int>', description='Equip an item from your inventory using its ID')
    @commands.check(Checks.is_player)
    async def equip(self, ctx, item_id : int):
        query = (item_id, ctx.author.id) # Make sure that 1. item exists 2. they own this item
        async with aiosqlite.connect(PATH) as conn:
            c = await conn.execute("""
                SELECT * FROM items
                WHERE item_id = ? AND owner_id = ?""", 
                query)
            item = await c.fetchone()
            if item is None:
                await ctx.reply("No such item of yours exists.")
            else: #Equip new item, update new item, update old item
                user = (ctx.author.id,)
                c = await conn.execute("""
                SELECT item_id, owner_id, is_equipped
                FROM Items
                WHERE owner_id = ?
                AND is_equipped = 1""", user)
                olditem = await c.fetchone()
                if olditem is not None: #Skip updating old item if there is no old item
                    if olditem[0] == item_id: #If they try to re-equip their item
                        await ctx.send("This item is already equipped")
                        return
                    else:
                        await conn.execute("""
                        UPDATE Items
                        SET is_equipped = 0
                        WHERE item_id = ?""", (olditem[0],))
                await conn.execute("""
                UPDATE Items
                SET is_equipped = 1
                WHERE item_id = ?""", (query[0],))
                await conn.execute("""
                UPDATE Players
                SET equipped_item = ?
                WHERE user_id = ?""", query)
                if olditem is not None:
                    await ctx.reply(f'Unequipped item {olditem[0]} and equipped {item_id}')
                else:
                    await ctx.reply(f'Equipped item {item_id}')
            await conn.commit()

    @commands.command(description='Unequip your item')
    @commands.check(Checks.is_player)
    async def unequip(self, ctx):
        query = (ctx.author.id,)
        async with aiosqlite.connect(PATH) as conn:
            c = await conn.execute('SELECT equipped_item FROM Players WHERE user_id = ?', query)
            equipped = await c.fetchone()
            if equipped is None:
                await ctx.reply('You don\'t have an item equipped.')
                return
            await conn.execute('UPDATE Players SET equipped_item = NULL WHERE user_id = ?', query)
            await conn.execute("""UPDATE Items SET is_equipped = 0
                WHERE owner_id = ? AND is_equipped = 1""", query)
            await conn.commit()
            await ctx.reply('Unequipped your item')


    @commands.command(brief='<item_id : int>', description='Sell an item for a random price.')
    @commands.check(Checks.is_player)
    async def sell(self, ctx, item_id : int):
        query = (item_id, ctx.author.id) #Make sure that item exists and author owns it
        async with aiosqlite.connect(PATH) as conn:
            c = await conn.execute("""SELECT item_id, owner_id, is_equipped, rarity FROM Items
                WHERE item_id = ? AND owner_id = ?""", query)
            d = await conn.execute('SELECT class FROM players WHERE user_id = ?', (ctx.author.id,))
            item = await c.fetchone()
            playerjob = await d.fetchone()
            try:
                if item[2] == 1:
                    await ctx.reply('You can\'t sell your equipped item.')
                    return
                # Otherwise item is owned and can be deleted
                for i in range(0,5):
                    if item[3] == WeaponValues[i][0]: 
                        gold = random.randint(WeaponValues[i][1], WeaponValues[i][2])
                        if playerjob == 'Merchant':
                            gold = int(gold * 1.5)
                        await conn.execute('UPDATE players SET gold = gold + ? WHERE user_id = ?', (gold, ctx.author.id))
                        await conn.execute('DELETE FROM Items WHERE item_id = ?', (item_id,))
                        await conn.commit()
                        await ctx.reply(f'You received {gold} gold for selling {item_id}.')
                        break
            except TypeError:
                await ctx.reply('You don\'t own this item')

    @commands.command(brief='<items>', description='Sell multiple items for random prices.')
    @commands.check(Checks.is_player)
    async def sellmultiple(self, ctx, *, items : str):
        itemlist = items.split()
        errors = ''
        total = 0
        async with aiosqlite.connect(PATH) as conn:
            d = await conn.execute('SELECT class FROM players WHERE user_id = ?', (ctx.author.id,))
            playerjob = await d.fetchone()
            for item_id in itemlist:
                try:
                    query = (int(item_id), ctx.author.id)
                except ValueError:
                    errors = errors + f'`{item_id}` '

                c = await conn.execute("""SELECT item_id, owner_id, is_equipped, rarity FROM Items
                    WHERE item_id = ? AND owner_id = ?""", query)
                item = await c.fetchone()

                try:
                    if item[2] == 1:
                        errors = errors + f'`{item_id}` '
                        continue
                    # Otherwise item is owned and can be deleted
                    for i in range(0,5):
                        if item[3] == WeaponValues[i][0]: 
                            gold = random.randint(WeaponValues[i][1], WeaponValues[i][2])
                            if playerjob == 'Merchant':
                                gold = int(gold * 1.5)
                            total = total + gold
                            await conn.execute('DELETE FROM Items WHERE item_id = ?', (item_id,))
                            break 
                except TypeError:
                    errors = errors + f'`{item_id}` '

            await conn.execute('UPDATE players SET gold = gold + ? WHERE user_id = ?', (total, ctx.author.id))
            await conn.commit()
            if len(errors) == 0:
                await ctx.reply(f'You received {total} gold for selling these items.')
            else:
                await ctx.reply(f'You received {total} gold for selling these items. Did not sell items {errors}')

    @commands.command(brief='<player> <item_id : int> <price : int>', description='Sell an item to someone')
    @commands.check(Checks.is_player)
    async def offer(self, ctx, player : commands.MemberConverter, item_id : int, price : int):
        #Make sure second player is also a player
        if player.id == ctx.author.id:
            await ctx.reply('Dude...no.')
            return
        if not await Checks.has_char(player):
            await ctx.reply('This person does not have a character.')
            return
        query = (item_id, ctx.author.id) #Make sure that item exists and author owns it
        async with aiosqlite.connect(PATH) as conn:
            c = await conn.execute("""SELECT is_equipped, attack, rarity, weapon_name, weapontype FROM Items
                WHERE item_id = ? AND owner_id = ?""", query)
            try:
                is_equipped, attack, rarity, weapon_name, weapontype = await c.fetchone()
            except TypeError:
                await ctx.reply('You don\'t own this item')
                return
            if is_equipped == 1:
                await ctx.reply('You can\'t sell your equipped item')
                return
            #Make sure price is valid
            if not price >= 0:
                await ctx.reply('Not a valid price.')
                return
            d = await conn.execute('SELECT gold FROM Players WHERE user_id = ?', (player.id,))
            gold = await d.fetchone()
            if price >= gold[0]:
                await ctx.reply('They can\'t afford that.')
                return
                
            # Otherwise player owns item and can sell it
            message = await ctx.send(f'{player.mention}, {ctx.author.mention} is offering you an item:\n**ID:** `{item_id}`, a {weapontype.lower()} named `{weapon_name}`\n**Rarity:** `{rarity}`, **Attack: **`{attack}`')

            # Now let second player accept/reject
            await message.add_reaction('\u2705') #Check
            await message.add_reaction('\u274E') #X

            def check(reaction, user):
                return user == player

            reaction = None
            readReactions = True
            while readReactions: 
                if str(reaction) == '\u2705': #Then exchange stuff
                    await message.delete()
                    await conn.execute('UPDATE Items SET owner_id = ? WHERE item_id = ?', (player.id, item_id))
                    await conn.execute('UPDATE Players SET gold = gold + ? WHERE user_id = ?', (price, ctx.author.id))
                    await conn.execute('UPDATE Players SET gold = gold - ? WHERE user_id = ?', (price, player.id))
                    await conn.commit()
                    await ctx.send(f'Successfully sold `{weapon_name}` for `{price}` gold')
                    break
                if str(reaction) == '\u274E':
                    await message.delete()
                    await ctx.send('They declined your offer.')
                    break

                try:
                    reaction, user = await self.client.wait_for('reaction_add', check=check, timeout=15.0)
                    await message.remove_reaction(reaction, user)
                except asyncio.TimeoutError:
                    readReactions = not readReactions
                    await message.delete()
                    await ctx.send('They did not respond to your offer.')
    
    @commands.command()
    @commands.check(Checks.is_player)
    async def weaponname(self, ctx, item_id : int, *, weaponname : str):
        if len(weaponname) > 20:
            await ctx.reply('Name can only be 20 characters or less.')
            return
        query = (item_id, ctx.author.id) #Make sure that item exists and author owns it
        async with aiosqlite.connect(PATH) as conn:
            c = await conn.execute("""SELECT item_id, owner_id, weapon_name FROM Items
                WHERE item_id = ? AND owner_id = ?""", query)
            item = await c.fetchone()
            if item is not None:
                await conn.execute('UPDATE Items SET weapon_name = ? WHERE item_id = ?', (weaponname, item_id))
                await conn.commit()
                await ctx.reply(f'Changed item `{item_id}`\'s name to `{weaponname}`')
            else:
                await ctx.reply('You don\'t own this item.')


def setup(client):
    client.add_cog(Items(client))