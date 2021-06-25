import discord

from discord.ext import commands, menus

from Utilities import Checks, AssetCreation, PageSourceMaker, Links

import json
import math

class Acolytes(commands.Cog):
    """Commands involving party members"""

    def __init__(self, client):
        self.client = client

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('Acolytes is ready.')

    #INVISIBLE
    async def write(self, start, inv, player):
        embed = discord.Embed(title=f'{player}\'s Tavern', 
                              color=self.client.ayesha_blue)

        iteration = 0
        while start < len(inv) and iteration < 5: #Loop til 5 entries or none left
            attack, crit, hp = await AssetCreation.getAcolyteAttack(self.client.pg_con, inv[start][0])
            if inv[start][3] == 1 or inv[start][3] == 2:
                acolyte = AssetCreation.getAcolyteByName(inv[start][1])
                embed.add_field(name = f"({acolyte['Rarity']}\u2B50) {inv[start][1]}: `{inv[start][0]}` [Equipped]",
                    value = f"**Level:** {inv[start][2]}, **Attack:** {attack}, **Crit:** {crit}%, **Dupes:** {inv[start][4]}\n**Effect:** {acolyte['Effect']}",
                    inline=False
                )
            else:
                acolyte = AssetCreation.getAcolyteByName(inv[start][1])
                embed.add_field(name = f"({acolyte['Rarity']}\u2B50) {inv[start][1]}: `{inv[start][0]}`",
                    value = f"**Level:** {inv[start][2]}, **Attack:** {attack}, **Crit:** {crit}%, **Dupes:** {inv[start][4]}\n**Effect:** {acolyte['Effect']}",
                    inline=False
                )
            iteration += 1
            start += 1
        return embed
    
    #COMMANDS
    @commands.command(aliases=['acolytes'], description='View your acolytes')
    @commands.check(Checks.is_player)
    async def tavern(self, ctx):
        """View a list of all the acolytes you own.
        Each acolyte has an ID number listed next to them, with which you can reference them in other commands.
        """
        inv = await AssetCreation.getAllAcolytesFromPlayer(self.client.pg_con, ctx.author.id)

        invpages = []
        for i in range(0, len(inv), 5): #list 5 entries at a time
            invpages.append(await self.write(i, inv, ctx.author.display_name)) # Write will create the embeds
        if len(invpages) == 0:
            await ctx.reply('Your tavern is empty!')
        else:
            tavern = menus.MenuPages(source=PageSourceMaker.PageMaker(invpages), 
                                     clear_reactions_after=True, 
                                     delete_message_after=True)
            await tavern.start(ctx)

    @commands.command(aliases=['hire'], 
                      brief='<acolyte_id : int> <slot (1 or 2)>', 
                      description='Add an acolyte to your party')
    @commands.check(Checks.is_player)
    async def recruit(self, ctx, instance_id : int, slot : int):
        """`instance_id` : the ID of the acolyte, listed next to their name in `tavern`
        `slot`: 1 or 2, which place of your team they will take

        Add an acolyte to your party.
        """
        if slot < 1 or slot > 2:
            return await ctx.reply('You can only place an acolyte in slots 1 or 2 of your party.')

        if not await AssetCreation.verifyAcolyteOwnership(self.client.pg_con, instance_id, ctx.author.id):
            return await ctx.reply('This acolyte isn\'t in your tavern.')

        #Equip new acolyte, update new acolyte, update old acolyte
        acolyte1, acolyte2 = await AssetCreation.getAcolyteFromPlayer(self.client.pg_con, ctx.author.id)
        
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
            await AssetCreation.unequipAcolyte(self.client.pg_con, oldacolyte)
        except TypeError:
            pass

        # Otherwise add the new acolyte
        added = await AssetCreation.getAcolyteByID(self.client.pg_con, instance_id)
        await AssetCreation.equipAcolyte(self.client.pg_con, instance_id, slot, ctx.author.id)
        await ctx.reply(f"Added `{instance_id}: {added['Name']}` to your party.")

    @commands.command(brief='<slot : int>', description='Dismiss an acolyte from the slot in your party.')
    @commands.check(Checks.is_player)
    async def dismiss(self, ctx, slot : int):
        """`slot`: the slot of your party you want to empty

        Dismiss an acolyte from the named slot in your party.
        """
        if slot < 1 or slot > 2:
            await ctx.reply('Please input a valid slot (1 or 2).')
            return
        
        #Make sure the slot they ask for has something in it
        acolyte1, acolyte2 = await AssetCreation.getAcolyteFromPlayer(self.client.pg_con, ctx.author.id)
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
            await AssetCreation.unequipAcolyte(self.client.pg_con, acolyte1, 1, ctx.author.id)
            removed = await AssetCreation.getAcolyteByID(self.client.pg_con, acolyte1)
        if slot == 2:
            await AssetCreation.unequipAcolyte(self.client.pg_con, acolyte2, 2, ctx.author.id)
            removed = await AssetCreation.getAcolyteByID(self.client.pg_con, acolyte2)

        await ctx.reply(f"Dismissed acolyte `{removed['ID']}: {removed['Name']}`")

    @commands.command(brief='<acolyte id> <amount = 1>', 
                      description='Train your acolyte, giving it xp and potentially levelling it up! Each training session with your acolyte costs 50 of its upgrade material and 250 gold.')
    @commands.check(Checks.is_player)
    async def train(self, ctx, instance_id : int, iterations : int = 1):
        """`instance_id`: the ID of the acolyte, listed next to their name in `tavern`
        `iterations`: the amount of times you want to train your acolyte

        Train your acolyte, giving it xp and potentially levelling it up! Each training session with your acolyte costs 50 of its upgrade material and 250 gold.
        """
        if not await AssetCreation.verifyAcolyteOwnership(self.client.pg_con, instance_id, ctx.author.id):
            await ctx.reply('This acolyte isn\'t in your tavern.')
            return

        acolyte = await AssetCreation.getAcolyteByID(self.client.pg_con, instance_id)
        if acolyte['Level'] >= 100:
            await ctx.reply(f"{acolyte['Name']} is already at maximum level!")
            return

        if iterations < 1:
            await ctx.reply('No.')
            return

        #Make sure player has the resources and gold to train
        #5000 xp = 50 of the mat + 250 gold
        material = await AssetCreation.getPlayerMat(self.client.pg_con, acolyte['Mat'], ctx.author.id)
        gold = await AssetCreation.getGold(self.client.pg_con, ctx.author.id)
        material_cost = iterations * 50
        gold_cost = iterations * 250

        if material < material_cost or gold < gold_cost:
            await ctx.reply(f"Training your acolyte costs `{material_cost}` {acolyte['Mat']} and `{gold_cost}` gold. You don\'t have enough resources to train.")
            return
        
        await AssetCreation.giveAcolyteXP(self.client.pg_con, 5000 * iterations, instance_id)
        await AssetCreation.giveGold(self.client.pg_con, -250 * iterations, ctx.author.id)
        await AssetCreation.giveMat(self.client.pg_con, acolyte['Mat'], -50 * iterations, ctx.author.id)

        await ctx.reply(f"You trained with `{acolyte['Name']}`, consuming `{material_cost}` {acolyte['Mat']} and `{gold_cost}` gold in the process. As a result, `{acolyte['Name']}` gained {5000 * iterations} exp!")
        await AssetCreation.checkAcolyteLevel(self.client.pg_con, ctx, instance_id)

    @commands.command(brief='<name>', description='Learn more about each of your acolytes!')
    async def acolyte(self, ctx, *, name):
        """`name`: the name of the acolyte you want to see

        Learn more about an acolyte, viewing their game-related info and backstory.
        """
        with open(Links.acolyte_list, "r") as f:
            info = json.load(f)

        try:
            if name.lower() == "prxrdr":
                name = 'PrxRdr'
            else:
                name = name.title()
            acolyte = info[name]
        except KeyError:
            await ctx.reply('No acolyte goes by that name.')
            return

        embed = discord.Embed(title=f"{acolyte['Name']}", color=self.client.ayesha_blue)
        if acolyte['Image'] is not None:
            embed.set_thumbnail(url=acolyte['Image']) 
        embed.add_field(name="Backstory", value=f"{acolyte['Story']}")
        embed.add_field(name='Effect', value=f"{acolyte['Effect']}", inline=False)
        embed.add_field(name="Stats", 
                        value=f"Attack: {acolyte['Attack']} + {acolyte['Scale']}/lvl\nCrit: {acolyte['Crit']}\nHP: {acolyte['HP']}")
        embed.add_field(name="Details", 
                        value=f"Rarity: {acolyte['Rarity']}\u2B50\nUpgrade Material: {acolyte['Mat'].title()}")

        await ctx.reply(embed=embed)

    @commands.command(aliases=['al'], description='See a list of all acolytes attainable ingame.')
    async def acolytelist(self, ctx):
        """See the list of all acolytes attainable ingame."""
        with open(Links.acolyte_list, "r") as f:
            info = json.load(f)

        acolyte_embeds = []
        for acolyte in info:
            embed = discord.Embed(title=f"{info[acolyte]['Name']}", color=self.client.ayesha_blue)
            if info[acolyte]['Image'] is not None:
                embed.set_thumbnail(url=info[acolyte]['Image']) 
            embed.add_field(name="Backstory", value=f"{info[acolyte]['Story']}")
            embed.add_field(name='Effect', value=f"{info[acolyte]['Effect']}", inline=False)
            embed.add_field(name="Stats", 
                            value=f"Attack: {info[acolyte]['Attack']} + {info[acolyte]['Scale']}/lvl\nCrit: {info[acolyte]['Crit']}\nHP: {info[acolyte]['HP']}")
            embed.add_field(name="Details", 
                            value=f"Rarity: {info[acolyte]['Rarity']}\u2B50\nUpgrade Material: {info[acolyte]['Mat'].title()}")
            acolyte_embeds.append(embed)

        acolist = menus.MenuPages(source=PageSourceMaker.PageMaker(acolyte_embeds), 
                                 clear_reactions_after=True, 
                                 delete_message_after=True)
        await acolist.start(ctx)

    @commands.command(brief='<acolyte ID>', description='Check your acolyte\'s xp and level.')
    @commands.check(Checks.is_player)
    async def acolytexp(self, ctx, instance_id : int):
        """`instance_id` : the ID of the acolyte, listed next to their name in `tavern`

        Check your acolyte's xp and level.
        """
        if not await AssetCreation.verifyAcolyteOwnership(self.client.pg_con, instance_id, ctx.author.id):
            await ctx.reply('This acolyte isn\'t in your tavern.')
            return

        info = await AssetCreation.getAcolyteXP(self.client.pg_con, instance_id)
        tonext = int(300 * ((info['lvl']+1)**2) - info['xp'])

        embed = discord.Embed(color=self.client.ayesha_blue)
        embed.add_field(name='Level', value=f"{info['lvl']}")
        embed.add_field(name='EXP', value=f"{info['xp']}")
        if info['lvl'] != 100:
            embed.add_field(name=f"EXP until Level {info['lvl']+1}", value=f"{tonext}")
        else:
            embed.add_field(name=f"EXP until Level {info['lvl']+1}", value="∞")
        await ctx.reply(embed=embed)

def setup(client):
    client.add_cog(Acolytes(client))