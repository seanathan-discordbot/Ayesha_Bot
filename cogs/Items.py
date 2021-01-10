import discord
import asyncio

from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

import aiosqlite
from Utilities import Checks, AssetCreation, PageSourceMaker

PATH = 'PATH'

class CharacterCreation(commands.Cog):

    def __init__(self, client):
        self.client = client

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('CC is ready.')

    #INVISIBLE
    def write(self, start, inv, player):
        embed = discord.Embed(set_author=f'{player}\'s Inventory', color=0xBEDCF6)

        iteration = 0
        while start < len(inv) and iteration < 5: #Loop til 5 entries or none left
            if inv[start][6] == 1:
                embed.add_field(name = f'{inv[start][4]}: `{inv[start][0]}` [Equipped]',
                    value = f'**Attack:** {inv[start][3]}, **Type:** {inv[start][1]}, **Rarity:** {inv[start][5]}',
                    inline=False
                )
            else:
                embed.add_field(name = f'{inv[start][4]}: `{inv[start][0]}`',
                    value = f'**Attack:** {inv[start][3]}, **Type:** {inv[start][1]}, **Rarity:** {inv[start][5]}',
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
                invpages.append(self.write(i, inv, ctx.author.id)) # Write will create the embeds
        if len(invpages) == 0:
            await ctx.reply('Your inventory is empty!')
        else:
            inventory = menus.MenuPages(source=PageSourceMaker.PageMaker(invpages), clear_reactions_after=True, delete_message_after=True)
            await inventory.start(ctx)

    @commands.command(brief='<item_id : int>', description='Equip an item from your inventory using its ID')
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

def setup(client):
    client.add_cog(CharacterCreation(client))
