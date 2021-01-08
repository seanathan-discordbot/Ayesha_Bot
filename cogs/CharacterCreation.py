import discord
import asyncio

from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

import aiosqlite
from Utilities import Checks

PATH = 'PATH'

class YesNo(menus.Menu):
    def __init__(self, ctx, embed):
        super().__init__(timeout=15.0, delete_message_after=True)
        self.embed = embed
        self.result = None
        
    async def send_initial_message(self, ctx, channel):
        return await channel.send(embed=self.embed)
    
    async def prompt(self, ctx):
        await self.start(ctx, wait=True)
        return self.result
    
    @menus.button('\u2705') # Check mark
    async def on_yes(self, payload):
        self.result = True
        self.stop()
        
    @menus.button('\u274E') # X
    async def on_no(self, payload):
        self.result = False
        self.stop() 

class CharacterCreation(commands.Cog):

    def __init__(self, client):
        self.client = client

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('CC is ready.')

    #INVISIBLE
    async def createCharacter(self, ctx, name):
        user = (ctx.author.id, name)
        async with aiosqlite.connect(PATH) as conn:
            await conn.execute("""
                INSERT INTO players (user_id, user_name)
                VALUES (?, ?)""",
                user)
            await conn.commit()
        await self.createItem('Spear', ctx.author.id, 20, 'Wooden Spear', 'Common')


    async def createItem(self, weapontype, owner_id, attack, name, rarity):
        async with aiosqlite.connect(PATH) as conn:
            item = (weapontype, owner_id, attack, name, rarity)
            await conn.execute("""
                INSERT INTO items (weapontype, owner_id, attack, weapon_name, rarity)
                VALUES (?, ?, ?, ?, ?)""",
                item)
            await conn.commit()

    #COMMANDS
    @commands.command(aliases=['begin','create'], brief='<name : str>', description='Start the game of Seanathan')
    @commands.check(Checks.not_player)
    async def start(self, ctx, *, name : str = None):
        if not name:
            name = ctx.author.display_name
        if len(name) > 32:
                await ctx.send("Name can only be up to 32 characters")
        else:
            prefix = await self.client.get_prefix(ctx.message)
            embed = discord.Embed(title='Start the game of Seanathan?')
            embed.add_field(name=f'Your Name: {name}', value=f'You can customize your name by doing `{prefix}start <name>`')
            start = await YesNo(ctx, embed).prompt(ctx)
            if start:
                await ctx.send(f'Your Name: {name}')
                await self.createCharacter(ctx, name)
                await ctx.send("Success")  

    @commands.command(aliases=['i', 'inv'], description='View your inventory of items')
    @commands.check(Checks.is_player)
    async def inventory(self, ctx):
        user = (ctx.author.id,)
        async with aiosqlite.connect(PATH) as conn:
            c = await conn.execute("""
                SELECT * FROM Items
                WHERE owner_id = ?""",
                user)
            inv = await c.fetchall()
        for row in inv:
            await ctx.send(row)

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
                await ctx.send("No.")
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
                    await ctx.send(f'Unequipped item {olditem[0]} and equipped {item_id}')
                else:
                    await ctx.send(f'Equipped item {item_id}')
            await conn.commit()
        


def setup(client):
    client.add_cog(CharacterCreation(client))
