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
# 7. Staff -tr
# 8. Greatsword
# 9. Axe
# 10. Sling
# 11. Javelin
# 12. Falx
# 13. Mace

class Items(commands.Cog):
    """View and manipulate inventory"""

    def __init__(self, client):
        self.client = client
        self.client.weapontypes = ('Spear',
                                   'Sword',
                                   'Dagger',
                                   'Bow',
                                   'Trebuchet',
                                   'Gauntlets',
                                   'Staff',
                                   'Greatsword',
                                   'Axe',
                                   'Sling',
                                   'Javelin',
                                   'Falx',
                                   'Mace')

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
    # @commands.command(aliases=['i', 'inv'], description='View your inventory of items')
    # @commands.check(Checks.is_player)
    # async def inventory(self, ctx, sort = None):
    #     """`sort`: the way you want to sort your items. Sort by `Rarity` or `Crit`. Sorts by Attack by default.
        
    #     View your inventory of items. Each item has an ID listed next to its name that can be referenced for related commands.
    #     """
    #     invpages = []
    #     inv = await AssetCreation.getAllItemsFromPlayer(self.client.pg_con, ctx.author.id, sort)
    #     for i in range(0, len(inv), 5): #list 5 entries at a time
    #         invpages.append(self.write(i, inv, ctx.author.display_name)) # Write will create the embeds
    #     if len(invpages) == 0:
    #         await ctx.reply('Your inventory is empty!')
    #     else:
    #         inventory = menus.MenuPages(source=PageSourceMaker.PageMaker(invpages), 
    #                                     clear_reactions_after=True, 
    #                                     delete_message_after=True)
    #         await inventory.start(ctx)
    
    @commands.command(aliases=['i', 'inv'], description='View your inventory of items')
    @commands.check(Checks.is_player)
    async def inventory(self, ctx, *, query = ''):
        """`query`: the way you want to sort your items. Put a weapontype, rarity, and order by attack or crit.

        View your inventory of items. Each item has an ID listed netx to its name that can be referenced for related commands.
        You can also sort specifically by weapontype, rarity, and order by attack or crit. Simply add the things you want to sort by in the command to get a smaller inventory.
        For example, to get all common swords in your inventory, do `%inventory common sword`. You can also do `%inventory crit` to sort all your weapons by crit.
        """
        #Create a list of all the queries for individual filtering
        sort = [term.title() for term in query.split()]

        #These functions will see how the items are sorted
        def filter_weapontypes(query):
            weapontypes = self.client.weapontypes
            if query in weapontypes:
                return True
            else:
                return False
            
        def filter_rarity(query):
            rarities = ['Common','Uncommon','Rare','Epic','Legendary']
            if query in rarities:
                return True
            else:
                return False

        def filter_metric(query):
            stats = ['Attack','Crit']
            if query in stats:
                return True
            else:
                return False

        filtered_type = filter(filter_weapontypes, sort)
        filtered_rarity = filter(filter_rarity, sort)
        filtered_stat = filter(filter_metric, sort)

        try:
            weapontype = list(filtered_type)[0]
        except IndexError:
            weapontype = None

        try:
            rarity = list(filtered_rarity)[0]
        except IndexError:
            rarity = None

        try:
            stat = list(filtered_stat)[0]
        except IndexError:
            stat = 'attack'

        #Retrieve the player's inventory based off the queries, but put equipped item first always
        inventory = []
        equipped_item = await self.client.pg_con.fetchrow('SELECT item_id, weapontype, attack, crit, weapon_name, rarity, is_equipped FROM items WHERE owner_id = $1 AND is_equipped = True', ctx.author.id)
        if equipped_item is not None:
            inventory.append(equipped_item)

        psql = 'SELECT item_id, weapontype, attack, crit, weapon_name, rarity, is_equipped FROM items WHERE owner_id = $1 AND is_equipped = False '

        if stat == 'attack':
            psql2 = ' ORDER BY attack DESC'
        else:
            psql2 = ' ORDER BY crit DESC'

        if weapontype is not None and rarity is not None:
            psql += 'AND weapontype = $2 AND rarity = $3 ' + psql2
            inv = await self.client.pg_con.fetch(psql, ctx.author.id, weapontype, rarity)

        elif weapontype is None and rarity is not None:
            psql += 'AND rarity = $2 ' + psql2
            inv = await self.client.pg_con.fetch(psql, ctx.author.id, rarity)

        elif weapontype is not None and rarity is None:
            psql += 'AND weapontype = $2 ' + psql2
            inv = await self.client.pg_con.fetch(psql, ctx.author.id, weapontype)

        else:
            psql += psql2
            inv = await self.client.pg_con.fetch(psql, ctx.author.id)

        for item in inv:
            inventory.append(item)

        invpages = []
        for i in range(0, len(inv), 5): #list 5 entries at a time
            invpages.append(self.write(i, inventory, ctx.author.display_name)) # Write will create the embeds
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
        """`item_id`: the ID of the weapon; can be found from `inventory`

        Equip an item from your inventory using its ID.
        """
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
        """Unequip your currently equipped item."""
        await AssetCreation.unequipItem(self.client.pg_con, ctx.author.id)
        await ctx.reply('Unequipped your item.')

    @commands.command(brief='<buffed item id> <fodder item id>',
                      description='Merge an item into another to boost its ATK by 1. The fodder item must be of the same weapontype and have at least 15 less ATK than the buffed item. Merging items costs `10,000` gold.')
    @commands.check(Checks.is_player)
    async def merge(self, ctx, buff_item : int, fodder : int):
        """`buff_item`: the item you want strengthened
        `fodder`: the item you are destroying to strengthen the other weapon

        Merge an item into another to boost its ATK by 1. The fodder item must be of the same weapontype and have at least 15 less ATK than the buffed item. Merging items costs 10,000 gold.
        """
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
        """`item_id`: the ID of the weapon; can be found from `inventory`

        Sell an item for a random price.
        """
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
        """`items`: the IDs of the items being sold, separated by spaces

        Sell multiple items for random prices.
        """
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
        await AssetCreation.log_transaction(self.client.pg_con,
                                            ctx.author.id,
                                            cost_info['subtotal'],
                                            cost_info['tax_amount'],
                                            cost_info['tax_rate'])

        if len(errors) == 0:
            await ctx.reply(f"You received `{subtotal}` gold for selling these items. You paid `{cost_info['tax_amount']}` gold in income taxes.")
        else:
            await ctx.reply(f"You received `{subtotal}` gold for selling these items but paid `{cost_info['tax_amount']}` in income taxes. Did not sell items {errors}.")

    @commands.command(brief='<rarity>', description='Sell all the items in your inventory of the stated rarity.')
    @commands.check(Checks.is_player)
    async def sellall(self, ctx, rarity : str):
        """`rarity`: the rarity of the items you want to sell.

        Sell all items in your inventory of the stated rarity.
        """
        #Ensure that a valid rarity is input
        rarities = ('Common', 'Uncommon', 'Rare', 'Epic', 'Legendary')
        rarity = rarity.title()
        if rarity not in rarities:
            await ctx.reply('That is not a valid rarity.')
            return
        try:
            items, gold, tax = await AssetCreation.sellAllItems(self.client.pg_con, ctx.author.id, rarity)
            await ctx.reply(f'You sold all {items} of your {rarity.lower()} items for `{gold}` gold. You paid `{tax}` gold in income taxes.')
        except ValueError:
            await ctx.reply('You have no items in your inventory of that rarity.')

    @commands.command(brief='<player> <item_id : int> <price : int>', description='Sell an item to someone')
    @commands.check(Checks.is_player)
    async def offer(self, ctx, player : commands.MemberConverter, item_id : int, price : int):
        """`player`: the player you want to offer the item to
        `item_id`: the ID of the weapon; can be found from `inventory`
        `price`: the rate you are selling the weapon for

        Sell an item to someone.
        """
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
        """`gold`: the amount of gold you want to give
        `player`: the player you are giving gold to

        Give some gold to the target player.
        """
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
        """`item_id`: the ID of the weapon; can be found from `inventory`
        `weaponname`: the name of the weapon

        Name your weapon anything you want (within utf-8 encoding)!
        """
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