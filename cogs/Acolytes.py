import discord
import asyncio

from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

from Utilities import Checks, AssetCreation, PageSourceMaker

import random
import math

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
            if inv[start][3] == 1 or inv[start][3] == 2:
                acolyte = AssetCreation.getAcolyteByName(inv[start][1])
                embed.add_field(name = f"({acolyte['Rarity']}\u2B50) {inv[start][1]}: `{inv[start][0]}` [Equipped]",
                    value = f"**Level:** {inv[start][2]}, **Attack:** {int(acolyte['Attack'] + (acolyte['Scale'] * inv[start][2]))}, **Crit:** {acolyte['Crit']}%\n**Effect:** {acolyte['Effect']}",
                    inline=False
                )
            else:
                acolyte = AssetCreation.getAcolyteByName(inv[start][1])
                embed.add_field(name = f"({acolyte['Rarity']}\u2B50) {inv[start][1]}: `{inv[start][0]}`",
                    value = f"**Level:** {inv[start][2]}, **Attack:** {int(acolyte['Attack'] + (acolyte['Scale'] * inv[start][2]))}, **Crit:** {acolyte['Crit']}%\n**Effect:** {acolyte['Effect']}",
                    inline=False
                )
            iteration += 1
            start += 1
        return embed
    
    #COMMANDS
    @commands.command(aliases=['acolytes'], description='View your acolytes')
    @commands.check(Checks.is_player)
    async def tavern(self, ctx):
        inv = await AssetCreation.getAllAcolytesFromPlayer(ctx.author.id)

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

        if not await AssetCreation.verifyAcolyteOwnership(instance_id, ctx.author.id):
            await ctx.reply('This acolyte isn\'t in your tavern.')
            return

        #Equip new acolyte, update new acolyte, update old acolyte
        acolyte1, acolyte2 = await AssetCreation.getAcolyteFromPlayer(ctx.author.id)
        
        if slot == 1:
            oldacolyte = acolyte1
            other = acolyte2
        else:
            oldacolyte = acolyte2
            other = acolyte1

        #Make sure they don't try to use the same acolyte twice - if you find a better way to do this change it
        try:
            if oldacolyte == instance_id:
                await ctx.send('This acolyte is already in your party.')
                return
        except TypeError:
            pass

        try:
            if other == instance_id:
                await ctx.send('This acolyte is already in your party.')
                return
        except TypeError:
            pass

        try:
            await AssetCreation.unequipAcolyte(oldacolyte)
        except TypeError:
            pass

        # Otherwise add the new acolyte
        added = await AssetCreation.getAcolyteByID(instance_id)
        await AssetCreation.equipAcolyte(instance_id, slot, ctx.author.id)
        await ctx.reply(f"Added `{instance_id}: {added['Name']}` to your party.")

    @commands.command(brief='<slot : int>', description='Dismiss an acolyte from the slot in your party.')
    @commands.check(Checks.is_player)
    async def dismiss(self, ctx, slot : int):
        if slot < 1 or slot > 2:
            await ctx.reply('Please input a valid slot (1 or 2).')
            return
        
        #Make sure the slot they ask for has something in it
        acolyte1, acolyte2 = await AssetCreation.getAcolyteFromPlayer(ctx.author.id)
        if slot == 1:
            if acolyte1 is None:
                await ctx.reply('You don\'t have an acolyte equipped in that slot.')
                return
        else:
            if acolyte2 is None:
                await ctx.reply('You don\'t have an acolyte equipped in that slot.')
                return

        #Unequip the acolyte
        if slot == 1:
            await AssetCreation.unequipAcolyte(acolyte1, 1, ctx.author.id)
            removed = await AssetCreation.getAcolyteByID(acolyte1)
        if slot == 2:
            await AssetCreation.unequipAcolyte(acolyte2, 2, ctx.author.id)
            removed = await AssetCreation.getAcolyteByID(acolyte2)

        await ctx.reply(f"Dismissed acolyte `{removed['ID']}: {removed['Name']}`")

    @commands.command(brief='<acolyte id>', description='Train your acolyte, giving it xp and potentially levelling it up!')
    @commands.check(Checks.is_player)
    async def train(self, ctx, instance_id : int):
        if not await AssetCreation.verifyAcolyteOwnership(instance_id, ctx.author.id):
            await ctx.reply('This acolyte isn\'t in your tavern.')
            return

        acolyte = await AssetCreation.getAcolyteByID(instance_id)
        if acolyte['Level'] >= 100:
            await ctx.reply(f"{acolyte['Name']} is already at maximum level!")
            return

        #Make sure player has the resources and gold to train
        #5000 xp = 50 of the mat + 250 gold
        material = await AssetCreation.getPlayerMat(acolyte['Mat'], ctx.author.id)
        gold = await AssetCreation.getGold(ctx.author.id)

        if material < 50 or gold < 250:
            await ctx.reply(f"Training your acolyte costs `50` {acolyte['Mat']} and `250` gold. You don\'t have enough resources to train.")
            return
        
        await AssetCreation.giveAcolyteXP(5000, instance_id)
        await AssetCreation.giveGold(-250, ctx.author.id)
        await AssetCreation.takeMat(acolyte['Mat'], 50, ctx.author.id)

        await ctx.reply(f"You trained with `{acolyte['Name']}`, consuming `50` {acolyte['Mat']} and `250` gold in the process. As a result, `{acolyte['Name']}` gained 5,000 exp!`")
        await AssetCreation.checkAcolyteLevel(ctx, instance_id)

def setup(client):
    client.add_cog(Acolytes(client))