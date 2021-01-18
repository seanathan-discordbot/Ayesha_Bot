import discord
import asyncio

from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

import aiosqlite
from Utilities import Checks, AssetCreation, PageSourceMaker

import random
import math

PATH = 'PATH'

class Acolytes(commands.Cog):

    def __init__(self, client):
        self.client = client

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('Acolytes is ready.')

    #INVISIBLE
    def write(self, start, inv, player):
        embed = discord.Embed(title=f'{player}\'s Tavern', color=0xBEDCF6)

        iteration = 0
        while start < len(inv) and iteration < 5: #Loop til 5 entries or none left
            if inv[start][5] == 1 or inv[start][5] == 2:
                acolyte = AssetCreation.getAcolyteByName(inv[start][2])
                embed.add_field(name = f"({acolyte['Rarity']}\u2B50) {inv[start][2]}: `{inv[start][0]}` [Equipped]",
                    value = f"**Level:** {inv[start][3]}, **Attack:** {int(acolyte['Attack'] + (acolyte['Scale'] * inv[start][3]))}, **Crit:** {acolyte['Crit']}%\n**Effect:** {acolyte['Effect']}",
                    inline=False
                )
            else:
                acolyte = AssetCreation.getAcolyteByName(inv[start][2])
                embed.add_field(name = f"({acolyte['Rarity']}\u2B50) {inv[start][2]}: `{inv[start][0]}`",
                    value = f"**Level:** {inv[start][3]}, **Attack:** {int(acolyte['Attack'] + (acolyte['Scale'] * inv[start][3]))}, **Crit:** {acolyte['Crit']}%\n**Effect:** {acolyte['Effect']}",
                    inline=False
                )
            iteration += 1
            start += 1
        return embed
    
    #COMMANDS
    @commands.command(aliases=['acolytes'], description='View your acolytes')
    @commands.check(Checks.is_player)
    async def tavern(self, ctx):
        user = (ctx.author.id,)
        async with aiosqlite.connect(PATH) as conn:
            c = await conn.execute("""
                SELECT * FROM Acolytes
                WHERE owner_id = ? AND (is_equipped = 1 OR is_equipped = 2)""",
                user)
            inv = await c.fetchall()
            c = await conn.execute("""
                SELECT * FROM Acolytes
                WHERE owner_id = ? AND is_equipped = 0""",
                user)
            for item in (await c.fetchall()): 
                inv.append(item) 
            invpages = []
            for i in range(0, len(inv), 5): #list 5 entries at a time
                invpages.append(self.write(i, inv, ctx.author.display_name)) # Write will create the embeds
        if len(invpages) == 0:
            await ctx.reply('Your tavern is empty!')
        else:
            tavern = menus.MenuPages(source=PageSourceMaker.PageMaker(invpages), clear_reactions_after=True, delete_message_after=True)
            await tavern.start(ctx)

    @commands.command(brief='<acolyte_id : int> <slot : int>', description='Add an acolyte to your party')
    @commands.check(Checks.is_player)
    async def recruit(self, ctx, instance_id : int, slot : int):
        if slot < 1 or slot > 2:
            await ctx.reply('You can only place an acolyte in slots 1 or 2 of your party.')
            return
        query = (instance_id, ctx.author.id) # Make sure that 1. acolyte exists 2. they own this item
        async with aiosqlite.connect(PATH) as conn:
            c = await conn.execute('SELECT * FROM Acolytes WHERE instance_id = ? AND owner_id = ?', query)
            acolyte = await c.fetchone()
            if acolyte is None:
                await ctx.reply("This acolyte isn\'t in your tavern.")
                return
            #Equip new acolyte, update new acolyte, update old acolyte
            d = await conn.execute('SELECT instance_id, is_equipped FROM Acolytes WHERE owner_id = ? AND is_equipped = 1', (ctx.author.id,))
            e = await conn.execute('SELECT instance_id, is_equipped FROM Acolytes WHERE owner_id = ? AND is_equipped = 2', (ctx.author.id,))
            if slot == 1:
                oldacolyte = await d.fetchone()
                other = await e.fetchone()
            else:
                oldacolyte = await e.fetchone()
                other = await d.fetchone()

            #Make sure they don't try to use the same acolyte twice - if you find a better way to do this change it
            try:
                if oldacolyte[0] == instance_id:
                    await ctx.send('This acolyte is already in your party')
                    return
            except TypeError:
                pass

            try:
                if other[0] == instance_id:
                    await ctx.send('This acolyte is already in your party')
                    return
            except TypeError:
                pass

            try:
                await conn.execute('UPDATE Acolytes SET is_equipped = 0 WHERE instance_id = ?', (oldacolyte[0],))
            except TypeError:
                pass

            # Otherwise add the new acolyte
            added = await AssetCreation.getAcolyteByID(instance_id)

            await conn.execute('UPDATE Acolytes SET is_equipped = ? WHERE instance_id = ?', (slot, instance_id))
            if slot == 1:
                await conn.execute('UPDATE Players SET acolyte1 = ? WHERE user_id = ?', (instance_id, ctx.author.id))
            else:
                await conn.execute('UPDATE Players SET acolyte2 = ? WHERE user_id = ?', (instance_id, ctx.author.id))
            await ctx.reply(f"Added `{instance_id}: {added['Name']}` to your party.")
            await conn.commit()

    @commands.command(brief='<slot : int>', description='Dismiss an acolyte from the slot in your party.')
    @commands.check(Checks.is_player)
    async def dismiss(self, ctx, slot : int):
        if slot < 1 or slot > 2:
            await ctx.reply('Please input a valid slot (1 or 2).')
            return
        query = (ctx.author.id,)
        async with aiosqlite.connect(PATH) as conn:
            if slot == 1:
                c = await conn.execute('SELECT acolyte1 FROM Players WHERE user_id = ?', query)
            else:
                c = await conn.execute('SELECT acolyte2 FROM Players WHERE user_id = ?', query)
            equipped = await c.fetchone()
            if equipped is None:
                await ctx.reply('You don\'t have an acolyte equipped in that slot.')
                return
            if slot == 1:
                await conn.execute('UPDATE Players SET acolyte1 = NULL where user_id = ?', query)
            else:
                await conn.execute('UPDATE Players SET acolyte2 = NULL where user_id = ?', query)
            await conn.execute('UPDATE Acolytes SET is_equipped = 0 WHERE owner_id = ? AND is_equipped = ?', (ctx.author.id, slot))
            await conn.commit()
            removed = await AssetCreation.getAcolyteByID(equipped[0])
            await ctx.reply(f"Dismissed acolyte `{equipped[0]}: {removed['Name']}`")

def setup(client):
    client.add_cog(Acolytes(client))