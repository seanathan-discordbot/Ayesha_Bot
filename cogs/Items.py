import discord
import asyncio

from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

from Utilities import Checks, AssetCreation, PageSourceMaker

import random

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
        embed = discord.Embed(title=f'{player}\'s Inventory', 
                              color=self.client.ayesha_blue)

        iteration = 0
        while start < len(inv) and iteration < 5: #Loop til 5 entries or none left
            if inv[start][6] == 1:
                embed.add_field(name = f'{inv[start][4]}: `{inv[start][0]}` [Equipped]',
                    value = f'**Attack:** {inv[start][2]}, **Crit:** {inv[start][3]}%, **Type:** {inv[start][1]}, **Rarity:** {inv[start][5]}',
                    inline=False
                )
            else:
                embed.add_field(name = f'{inv[start][4]}: `{inv[start][0]}`',
                    value = f'**Attack:** {inv[start][2]}, **Crit:** {inv[start][3]}%, **Type:** {inv[start][1]}, **Rarity:** {inv[start][5]}',
                    inline=False
                )
            iteration += 1
            start += 1
        return embed
    
    #COMMANDS
    @commands.command(aliases=['i', 'inv'], description='View your inventory of items')
    @commands.check(Checks.is_player)
    async def inventory(self, ctx, sort = None):
        invpages = []
        inv = await AssetCreation.getAllItemsFromPlayer(self.client.pg_con, ctx.author.id, sort)
        for i in range(0, len(inv), 5): #list 5 entries at a time
            invpages.append(self.write(i, inv, ctx.author.display_name)) # Write will create the embeds
        if len(invpages) == 0:
            await ctx.reply('Your inventory is empty!')
        else:
            inventory = menus.MenuPages(source=PageSourceMaker.PageMaker(invpages), 
                                        clear_reactions_after=True, 
                                        delete_message_after=True)
            await inventory.start(ctx)

    @commands.command(aliases=['use','wield'], 
                      brief='<item_id : int>', 
                      description='Equip an item from your inventory using its ID')
    @commands.check(Checks.is_player)
    async def equip(self, ctx, item_id : int):
        # Make sure that 1. item exists 2. they own this item
        item_is_valid = await AssetCreation.verifyItemOwnership(self.client.pg_con, item_id, ctx.author.id)
        if not item_is_valid:
            await ctx.reply('No such item of yours exists.')
            return
        
        #Else equip new item, update new item, update old item
        #Unequip old item
        try:
            olditem = await AssetCreation.getEquippedItem(self.client.pg_con, ctx.author.id)
            if olditem == item_id:
                await ctx.send("This item is already equipped")
                return
            await AssetCreation.unequipItem(self.client.pg_con, ctx.author.id, olditem)
        except TypeError:
            olditem = None

        #Equip new item
        await AssetCreation.equipItem(self.client.pg_con, item_id, ctx.author.id)
        if olditem is not None:
            await ctx.reply(f'Unequipped item `{olditem}` and equipped `{item_id}`.')
        else:
            await ctx.reply(f'Equipped item `{item_id}`.')

    @commands.command(description='Unequip your item')
    @commands.check(Checks.is_player)
    async def unequip(self, ctx):
        await AssetCreation.unequipItem(self.client.pg_con, ctx.author.id)
        await ctx.reply('Unequipped your item.')

    @commands.command(brief='<buffed item id> <fodder item id>',
                      description='Merge an item into another to boost its ATK by 1. The fodder item must be of the same weapontype and have at least 15 less ATK than the buffed item. Merging items costs `10,000` gold.')
    @commands.check(Checks.is_player)
    async def merge(self, ctx, buff_item : int, fodder : int):
        #Make sure player owns both items and that the fodder is NOT equipped
        if not await AssetCreation.verifyItemOwnership(self.client.pg_con, buff_item, ctx.author.id):
            return await ctx.reply(f'You do not own an item with ID `{buff_item}`.')
        if not await AssetCreation.verifyItemOwnership(self.client.pg_con, fodder, ctx.author.id):
            return await ctx.reply(f'You do not own an item with ID `{fodder}`.')

        if fodder == await AssetCreation.getEquippedItem(self.client.pg_con, ctx.author.id):
            return await ctx.reply('You cannot use your currently equipped item as fodder material.')

        cost_info = await AssetCreation.calc_cost_with_tax_rate(self.client.pg_con, 10000)
        if await AssetCreation.getGold(self.client.pg_con, ctx.author.id) < cost_info['total']:
            return await ctx.reply(f"You need at least `{cost_info['total']}` gold to perform this operation.")

        buff_item_info = await AssetCreation.getItem(self.client.pg_con, buff_item)
        fodder_info = await AssetCreation.getItem(self.client.pg_con, fodder)

        if fodder_info['Type'] != buff_item_info['Type']:
            return await ctx.reply('These items must be the same weapontype to be merged.')

        if fodder_info['Attack'] < buff_item_info['Attack'] - 15:
            return await ctx.reply('The fodder item must have at least 15 less ATK than the item being upgraded.')

        #Increase items stats and delete the fodder item
        await AssetCreation.increaseItemAttack(self.client.pg_con, buff_item, 1)
        await AssetCreation.deleteItem(self.client.pg_con, fodder)

        #Perform the transaction
        await AssetCreation.giveGold(self.client.pg_con, cost_info['total']*-1, ctx.author.id)
        await AssetCreation.log_transaction(self.client.pg_con, 
                                            ctx.author.id, 
                                            cost_info['subtotal'],
                                            cost_info['tax_amount'],
                                            cost_info['tax_rate'])

        await ctx.reply(f"You merged your `{fodder_info['Name']} ({fodder})` into `{buff_item_info['Name']} ({buff_item})`, raising its ATK to `{buff_item_info['Attack']+1}`.\nThis cost you `10,000` gold, with an additional `{cost_info['tax_amount']}` in taxes.")

    @commands.command(brief='<item_id : int>', description='Sell an item for a random price.')
    @commands.check(Checks.is_player)
    async def sell(self, ctx, item_id : int):
        #Make sure item exists and author owns it
        item_is_valid = await AssetCreation.verifyItemOwnership(self.client.pg_con, item_id, ctx.author.id)
        if not item_is_valid:
            await ctx.reply('No such item of yours exists.')
            return

        #Otherwise get item and calc compensation
        item = await AssetCreation.getItem(self.client.pg_con, item_id)
        if item['Equip'] == 1:
            await ctx.reply('You can\'t sell your equipped item.')
            return

        for i in range(0,5):
            if item['Rarity'] == WeaponValues[i][0]:
                gold = random.randint(WeaponValues[i][1], WeaponValues[i][2])
                break

        #Consider class, guild, comptroller bonus
        # sale_bonus = 1
        # playerjob = await AssetCreation.getClass(self.client.pg_con, ctx.author.id)
        # if playerjob == 'Merchant':
        #     sale_bonus += .5

        # try:
        #     guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        #     if guild['Type'] == 'Guild':
        #         guild_level = await AssetCreation.getGuildLevel(self.client.pg_con, guild['ID'])
        #         sale_bonus += .5 + (guild_level * .1)
        # except TypeError:
        #     pass

        # if await AssetCreation.check_for_comptroller_bonus(self.client.pg_con, ctx.author.id, 'sales'):
        #     comp_bonus = await AssetCreation.get_comptroller_bonus(self.client.pg_con)
        #     sale_bonus += .04 + (.04 * comp_bonus['Level'])
        sale_bonus = await AssetCreation.applySaleBonuses(self.client.pg_con, ctx.author.id)

        subtotal = int(gold * sale_bonus)
        cost_info = await AssetCreation.calc_cost_with_tax_rate(self.client.pg_con, subtotal)
        payout = cost_info['subtotal'] - cost_info['tax_amount']

        #Delete item and give gold to player
        await AssetCreation.giveGold(self.client.pg_con, payout, ctx.author.id)
        await AssetCreation.log_transaction(self.client.pg_con,
                                            ctx.author.id,
                                            cost_info['subtotal'],
                                            cost_info['tax_amount'],
                                            cost_info['tax_rate'])
        await AssetCreation.deleteItem(self.client.pg_con, item_id)

        await ctx.reply(f"You received `{subtotal}` gold for selling `{item_id}`. You paid `{cost_info['tax_amount']}` in income taxes.")

    @commands.command(brief='<items>', description='Sell multiple items for random prices.')
    @commands.check(Checks.is_player)
    async def sellmultiple(self, ctx, *, items : str):
        itemlist = items.split()
        errors = ''
        total = 0

        #Consider class, guild, comptroller bonus
        # sale_bonus = 1
        # playerjob = await AssetCreation.getClass(self.client.pg_con, ctx.author.id)
        # if playerjob == 'Merchant':
        #     sale_bonus += .5

        # try:
        #     guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        #     if guild['Type'] == 'Guild':
        #         guild_level = await AssetCreation.getGuildLevel(self.client.pg_con, guild['ID'])
        #         sale_bonus += .5 + (guild_level * .1)
        # except TypeError:
        #     pass

        # if await AssetCreation.check_for_comptroller_bonus(self.client.pg_con, ctx.author.id, 'sales'):
        #     comp_bonus = await AssetCreation.get_comptroller_bonus(self.client.pg_con)
        #     sale_bonus += .04 + (.04 * comp_bonus['Level'])
        sale_bonus = await AssetCreation.applySaleBonuses(self.client.pg_con, ctx.author.id)

        #Calculate and delete items one-by-one
        for item_id in itemlist:
            try:
                item = await AssetCreation.getItem(self.client.pg_con, int(item_id))
            except ValueError:
                errors = errors + f'`{item_id}` '
                continue

            if item['Owner'] != ctx.author.id:
                errors = errors + f'`{item_id}` '
                continue

            try:
                if item['Equip'] == 1:
                    errors = errors + f'`{item_id}` '
                    continue
                # Otherwise item is owned and can be deleted
                for i in range(0,5):
                    if item['Rarity'] == WeaponValues[i][0]: 
                        gold = random.randint(WeaponValues[i][1], WeaponValues[i][2])
                        total = total + gold
                        await AssetCreation.deleteItem(self.client.pg_con, int(item_id))
                        break 
            except TypeError:
                errors = errors + f'`{item_id}` '

        subtotal = int(total * sale_bonus) #Apply all bonuses
        cost_info = await AssetCreation.calc_cost_with_tax_rate(self.client.pg_con, subtotal)
        payout = subtotal - cost_info['tax_amount']

        await AssetCreation.giveGold(self.client.pg_con, payout, ctx.author.id)

        if len(errors) == 0:
            await ctx.reply(f"You received `{subtotal}` gold for selling these items. You paid `{cost_info['tax_amount']}` gold in income taxes.")
        else:
            await ctx.reply(f"You received `{subtotal}` gold for selling these items but paid `{cost_info['tax_amount']}` in income taxes. Did not sell items {errors}.")

    @commands.command(brief='<rarity>', description='Sell all the items in your inventory of the stated rarity.')
    @commands.check(Checks.is_player)
    async def sellall(self, ctx, rarity : str):
        #Ensure that a valid rarity is input
        rarities = ('Common', 'Uncommon', 'Rare', 'Epic', 'Legendary')
        rarity = rarity.title()
        if rarity not in rarities:
            await ctx.reply('That is not a valid rarity.')
            return
        items, gold, tax = await AssetCreation.sellAllItems(self.client.pg_con, ctx.author.id, rarity)
        await ctx.reply(f'You sold all {items} of your {rarity.lower()} items for `{gold}` gold. You paid `{tax}` gold in income taxes.')

    @commands.command(brief='<player> <item_id : int> <price : int>', description='Sell an item to someone')
    @commands.check(Checks.is_player)
    async def offer(self, ctx, player : commands.MemberConverter, item_id : int, price : int):
        #Make sure second player is also a player
        if player.id == ctx.author.id:
            await ctx.reply('Dude...no.')
            return
        if not await Checks.has_char(self.client.pg_con, player):
            await ctx.reply('This person does not have a character.')
            return
        
        #Make sure that item exists and author owns it
        item_is_valid = await AssetCreation.verifyItemOwnership(self.client.pg_con, item_id, ctx.author.id)
        if not item_is_valid:
            await ctx.reply('No such item of yours exists.')
            return

        item = await AssetCreation.getItem(self.client.pg_con, item_id)
        if item['Equip'] == 1:
            await ctx.reply('You can\'t sell your equipped item')
            return

        #Make sure price is valid
        if not price >= 0:
            await ctx.reply('Not a valid price.')
            return

        gold = await AssetCreation.getGold(self.client.pg_con, player.id)
        if price >= gold:
            await ctx.reply('They can\'t afford that.')
            return
                
        # Otherwise player owns item and can sell it
        message = await ctx.send(f"{player.mention}, {ctx.author.mention} is offering you an item:\n**ID:** `{item_id}`, a {item['Type'].lower()} named `{item['Name']}`\n**Rarity:** `{item['Rarity']}`, **Attack: **`{item['Attack']}`")

        # Now let second player accept/reject
        await message.add_reaction('\u2705') #Check
        await message.add_reaction('\u274E') #X

        def check(reaction, user):
            return user == player and reaction.message.id == message.id

        reaction = None
        readReactions = True
        while readReactions: 
            if str(reaction) == '\u2705': #Then exchange stuff
                await message.delete()

                #Repeat this just in case they did a simultaneous reaction
                gold = await AssetCreation.getGold(self.client.pg_con, player.id)
                if price >= gold:
                    return await ctx.reply('The buyer has since lost money and is no longer able to afford your offer.')

                await AssetCreation.setItemOwner(self.client.pg_con, item_id, player.id)
                await AssetCreation.giveGold(self.client.pg_con, price, ctx.author.id)
                await AssetCreation.giveGold(self.client.pg_con, 0 - price, player.id)
                await ctx.send(f"Successfully sold `{item['Name']}` for `{price}` gold")
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

    @commands.command(brief='<gold> <player>', description='Give some gold to the target player.')
    @commands.check(Checks.is_player)
    async def give(self, ctx, gold : int, player : commands.MemberConverter):
        #Make sure second player is also a player
        if player.id == ctx.author.id:
            await ctx.reply('Dude...no.')
            return
        if not await Checks.has_char(self.client.pg_con, player):
            await ctx.reply('This person does not have a character.')
            return

        #Make sure this person actually has gold
        if gold < 0:
            return await ctx.reply('That is impossible.')

        player_gold = await AssetCreation.getGold(self.client.pg_con, ctx.author.id)
        if gold > player_gold:
            return await ctx.reply('You don\'t have that much gold to give away.')

        #Perform transaction
        await AssetCreation.giveGold(self.client.pg_con, gold * -1, ctx.author.id)
        await AssetCreation.giveGold(self.client.pg_con, gold, player.id)

        await ctx.reply(f'Gave `{gold}` gold to {player.display_name}. You now have `{player_gold - gold}` gold.')
    
    @commands.command(brief='<item ID> <new name>', description='Name your weapon anything you want!')
    @commands.check(Checks.is_player)
    async def weaponname(self, ctx, item_id : int, *, weaponname : str):
        if len(weaponname) > 20:
            await ctx.reply('Name can only be 20 characters or less.')
            return
        #Make sure that item exists and author owns it
        item_is_valid = await AssetCreation.verifyItemOwnership(self.client.pg_con, item_id, ctx.author.id)
        if not item_is_valid:
            await ctx.reply('No such item of yours exists.')
            return

        await AssetCreation.setItemName(self.client.pg_con, item_id, weaponname)
        await ctx.reply(f'Changed item `{item_id}`\'s name to `{weaponname}`.')


def setup(client):
    client.add_cog(Items(client))