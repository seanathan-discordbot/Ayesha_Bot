import discord
import asyncio

from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

from Utilities import Checks, AssetCreation, PageSourceMaker
from Utilities.PageSourceMaker import PageMaker

import aiohttp
import time
import random

class Classes(commands.Cog):
    """Customize your character!"""

    def __init__(self, client):
        self.client = client
        self.client.classes = { # Weapon Bonus: [CODE FOUND IN AssetCreation.get_attack_crit_hp()]
            'Soldier' : {
                'Name' : 'Soldier',
                'Desc' : 'You are a retainer of your local lord, trained in the discipline of swordsmanship.',
                'Passive' : '20% bonus to character ATK; +1 gravitas/day',
                'Command' : 'Deal 50% more damage when doing `raid attack`',
                'Weapon' : 'Spear, Sword'
            },
            'Blacksmith' : {
                'Name' : 'Blacksmith',
                'Desc' : 'You\'ve spent years as the apprentice of a hardy blacksmith, and now a master in the art of forging.',
                'Passive' : 'Gain double gold and resources from `mine`, and pay half cost from `upgrade`.',
                'Command' : 'Exclusive access to the `smith` command. Do `help smith` for more info.',
                'Weapon' : 'Greatsword, Gauntlets'
            },
            'Farmer' : {
                'Name' : 'Farmer',
                'Desc' : 'You are a lowly farmer, but farming is no easy job.',
                'Passive' : '+4 gravitas/day',
                'Command' : 'Exclusive access to the `farm` command. Do `help farm` for more info.',
                'Weapon' : 'Sling, Falx'
            },
            'Hunter' : {
                'Name' : 'Hunter',
                'Desc' : 'The wild is your domain; no game is unconquerable.',
                'Passive' : 'Gain double gold and resources from `hunt`.',
                'Command' : 'Exclusive access to the `pet` command. Do `help pet` for more info.',
                'Weapon' : 'Bow, Javelin'
            },
            'Merchant' : {
                'Name' : 'Merchant',
                'Desc' : 'Screw you, exploiter of others\' labor.',
                'Passive' : 'Gain 50% increased gold from the `sell` and `shop sell` command.',
                'Command' : 'Guaranteed item upon defeating a boss in `bounty`.',
                'Weapon' : 'Dagger, Mace'
            },
            'Traveler' : {
                'Name' : 'Traveler',
                'Desc' : 'The wild forests north await, as do the raging seas to the south. What will you discover?',
                'Passive' : 'Gain triple gold from the `travel` command and double materials from the `forage` command.',
                'Command' : '50% chance to gain an acolyte from expeditions lasting longer than 72 hours.',
                'Weapon' : 'Staff, Javelin'
            },
            'Leatherworker' : {
                'Name' : 'Leatherworker',
                'Desc' : 'The finest protective gear, saddles, and equipment have your name on it.',
                'Passive' : '250 more HP',
                'Command' : 'Take 15% less damage from every hit in `bounty` battles.',
                'Weapon' : 'Mace, Axe'
            },
            'Butcher' : {
                'Name' : 'Butcher',
                'Desc' : 'Meat. What would one do without it?',
                'Passive' : '100% increased healing effectiveness in `battle` and `bounty`.',
                'Command' : 'Exclusive access to the `butchery` command. Do `help butchery` for more info.',
                'Weapon' : 'Axe, Dagger'
            },
            'Engineer' : { # Steal 10% of gold instead of 5, 25% buff to guild invest, gain 5 gravitas from cl usurp
                'Name' : 'Engineer',
                'Desc' : 'Your lord praises the seemingly impossible design of his new manor.',
                'Passive' : 'Gain increased rewards from the special commands of whatever association you are in: `bh steal`, `guild invest`, or `cl usurp`.',
                'Command' : 'Critical hits in `battle` and `bounty` deal 1.75x damage instead of 1.5x',
                'Weapon' : 'Trebuchet, Falx'
            },
            'Scribe' : {
                'Name' : 'Scribe',
                'Desc' : 'Despite the might of your lord, you have learned quite a bit about everything, too.',
                'Passive' : '+10 Crit; +1 gravitas daily',
                'Command' : 'Exclusive access to the `scriptorium` command. Do `help scriptorium` for more info.',
                'Weapon' : 'Sword, Dagger'
            }
        }
        self.client.origins = {
            'Aramithea' : {
                'Name' : 'Aramithea',
                'Desc' : 'You\'re a metropolitan. Aramithea, the largest city on Rabidus, must have at least a million people, and a niche for everybody.',
                'Passive' : '+5 gravitas/day' # Gravitas passives found in Profile.update_gravitas()
            },
            'Riverburn' : {
                'Name' : 'Riverburn',
                'Desc' : 'The great rival of Aramithea; Will you bring your city to become the center of the kingdom?',
                'Passive' : '+5 ATK, +3 gravitas/day' # Stat passives found in AssetCreation.get_attack_crit_hp()
            },
            'Thenuille' : {
                'Name' : 'Thenuille',
                'Desc' : 'You love the sea; you love exploration; you love trade. From here one can go anywhere, and be anything.',
                'Passive' : '+25 HP, +3 gravitas/day'
            },  
            'Mythic Forest' : {
                'Name' : 'Mythic Forest',
                'Desc' : 'You come from the lands down south, covered in forest. You could probably hit a deer square between the eyes blindfolded.',
                'Passive' : '+2 Crit, +1 gravitas/day'
            },  
            'Sunset' : {
                'Name' : 'Sunset',
                'Desc' : 'Nothing is more peaceful than an autumn afternoon in the prairie.',
                'Passive' : 'Pay 5% less in taxes.'
            },  
            'Lunaris' : {
                'Name' : 'Lunaris',
                'Desc' : 'The crossroads of civilization; the battleground of those from the north, west, and east. Your times here have hardened you.',
                'Passive' : '+50 HP, +1 gravitas/day'
            },  
            'Crumidia' : {
                'Name' : 'Crumidia',
                'Desc' : 'The foothills have turned you into a strong warrior. Perhaps you will seek domination over your adversaries?',
                'Passive' : '+10 ATK, +1 gravitas/day'
            },  
            'Maritimiala' : {
                'Name' : 'Maritimiala',
                'Desc' : 'North of the mountains, the Maritimialan tribes look lustfully upon the fertile plains below. Will you seek integration, or domination?',
                'Passive' : '+4 Crit'
            },  
            'Glakelys' : {
                'Name' : 'Glakelys',
                'Desc' : 'The small towns beyond Riverburn disregard the Aramithean elite. The first line of defense from invasions from Lunaris, the Glakelys are as tribal as they were 300 years ago.',
                'Passive' : '+5 ATK, +25 HP'
            }
        }

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('Classes is ready.')

    #COMMANDS
    @cooldown(1, 3600, BucketType.user)
    @commands.command(name='class', 
                      description='Choose your player class. This can be changed.')
    async def change_class(self, ctx, player_job : str = None):
        """`player_job`: the class you want to switch to. To see the list of valid classes, just do `class`.

        Choose your player class. This can be changed in the future.
        """
        if player_job is None:
            ctx.command.reset_cooldown(ctx)

            entries = []
            for job in list(self.client.classes.values()):
                embed = discord.Embed(title=f"{job['Name']}: Say `{ctx.prefix}class {job['Name']}` to take this class!", 
                                      description=job['Desc'],
                                      color=self.client.ayesha_blue)
                embed.set_author(name='Class Selection Menu',
                                 icon_url=ctx.author.avatar_url)
                
                embed.add_field(name='Passive Effect',
                                value=job['Passive'])
                embed.add_field(name='Exclusive/Empowered Command',
                                value=job['Command'])
                embed.add_field(name='Gain 20 ATK for having a weapon of one of these types equipped:',
                                value=job['Weapon'],
                                inline=False)

                entries.append(embed)

            entries = PageSourceMaker.PageMaker.number_pages(entries)
            tavern = menus.MenuPages(source=PageMaker(entries), 
                                     clear_reactions_after=True, 
                                     delete_message_after=True)
            await tavern.start(ctx)

        else:
            player_job = player_job.title()

            if player_job not in (list(self.client.classes)):
                return await ctx.reply(f'This is not a valid class. Please do `{ctx.prefix}class` with no arguments to see the list of classes.')

            else:
                await AssetCreation.setPlayerClass(self.client.pg_con, player_job, ctx.author.id)
                await AssetCreation.delete_player_estate(self.client.pg_con, ctx.author.id)
                fmt = f"You are now a **{player_job}**!\n\n__Your Benefits__\n"
                fmt += self.client.classes[player_job]['Passive']
                fmt += "\n" + self.client.classes[player_job]['Command'] + "\n"
                fmt += f"Gain 20 ATK for having a weapon of one of these types equipped: "
                fmt += self.client.classes[player_job]['Weapon']
                await ctx.reply(fmt)
        
    @cooldown(1, 3600, BucketType.user)
    @commands.command(aliases=['background','birthplace'], description='Choose your birthplace.')
    async def origin(self, ctx, *, player_origin : str = None):
        """`player_origin`: Your birthplace. To see the valid areas, just do `origin`

        Choose your homeland.
        """
        if player_origin is None:
            ctx.command.reset_cooldown(ctx)

            entries = []
            for place in list(self.client.origins.values()):
                embed = discord.Embed(title=f"{place['Name']}: Say `{ctx.prefix}origin {place['Name']}` if you like this place!",
                                      description=f"{place['Desc']}\n\n**Passive Effect:** {place['Passive']}",
                                      color=self.client.ayesha_blue)
                embed.set_author(name='Background Selection Menu',
                                 icon_url=ctx.author.avatar_url)          

                entries.append(embed)   

            entries = PageSourceMaker.PageMaker.number_pages(entries)
            tavern = menus.MenuPages(source=PageMaker(entries), 
                                     clear_reactions_after=True, 
                                     delete_message_after=True)
            await tavern.start(ctx)

        else:
            player_origin = player_origin.title()

            if player_origin not in (list(self.client.origins)):
                await ctx.reply(f'This is not a valid place. Please do `{ctx.prefix}origin` with no arguments to see the list of backgrounds.')
                return

            else:
                await AssetCreation.setPlayerOrigin(self.client.pg_con, player_origin, ctx.author.id)
                fmt = f'{ctx.author.mention}, you are from **{player_origin}**!\n\n__Your Benefits__\n'
                fmt += self.client.origins[player_origin]['Passive']
                await ctx.send(fmt)

    # -----------------------------------------
    # ----- BLACKSMITH EXCLUSIVE COMMANDS -----
    # -----------------------------------------

    @commands.command(aliases=['smith'])
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_blacksmith)
    async def forge(self, ctx, buff_item : int, fodder : int):
        """`buff_item`: the item you want strengthened
        `fodder`: the item you are destroying to strengthen the other weapon
        
        [BLACKSMITH EXCLUSIVE] Merge an item into another to boost its ATK by 2. The fodder item must be of the same weapontype and have at least 15 less ATK than the buffed item. Merging this way costs 100,000 gold.
        """
        #Make sure player owns both items and that the fodder is NOT equipped
        if not await AssetCreation.verifyItemOwnership(self.client.pg_con, buff_item, ctx.author.id):
            return await ctx.reply(f'You do not own an item with ID `{buff_item}`.')
        if not await AssetCreation.verifyItemOwnership(self.client.pg_con, fodder, ctx.author.id):
            return await ctx.reply(f'You do not own an item with ID `{fodder}`.')

        if fodder == await AssetCreation.getEquippedItem(self.client.pg_con, ctx.author.id):
            return await ctx.reply('You cannot use your currently equipped item as fodder material.')

        cost_info = await AssetCreation.calc_cost_with_tax_rate(self.client.pg_con, 
                                                                100000, 
                                                                await AssetCreation.getOrigin(self.client.pg_con, 
                                                                                              ctx.author.id))
        if await AssetCreation.getGold(self.client.pg_con, ctx.author.id) < cost_info['total']:
            return await ctx.reply(f"You need at least `{cost_info['total']}` gold to perform this operation.")

        buff_item_info = await AssetCreation.getItem(self.client.pg_con, buff_item)
        fodder_info = await AssetCreation.getItem(self.client.pg_con, fodder)

        if fodder_info['Type'] != buff_item_info['Type']:
            return await ctx.reply('These items must be the same weapontype to be merged.')

        if fodder_info['Attack'] < buff_item_info['Attack'] - 15:
            return await ctx.reply('The fodder item must have at least 15 less ATK than the item being upgraded.')

        #Increase items stats and delete the fodder item
        await AssetCreation.increaseItemAttack(self.client.pg_con, buff_item, 2)
        await AssetCreation.deleteItem(self.client.pg_con, fodder)

        #Perform the transaction
        await AssetCreation.giveGold(self.client.pg_con, cost_info['total']*-1, ctx.author.id)
        await AssetCreation.log_transaction(self.client.pg_con, 
                                            ctx.author.id, 
                                            cost_info['subtotal'],
                                            cost_info['tax_amount'],
                                            cost_info['tax_rate'])

        await ctx.reply(f"You merged your `{fodder_info['Name']} ({fodder})` into `{buff_item_info['Name']} ({buff_item})`, raising its ATK to `{buff_item_info['Attack']+2}`.\nThis cost you `100,000` gold, with an additional `{cost_info['tax_amount']}` in taxes.")

    # -------------------------------------
    # ----- FARMER EXCLUSIVE COMMANDS -----
    # -------------------------------------

    def calculate_farm_rewards(self, crop, hours, multiplier):
        gold = 0
        gravitas = 0

        if hours > 168:
            hours = 168

        if hours < 24:
            gold = hours * 250
            gravitas = hours * .65
        elif hours < 72:
            gold = hours * 275
            gravitas = hours * .8
        else:
            gold = hours * 300
            gravitas = hours

        if crop == 'alfalfa':
            gravitas = int(gravitas / 2)
        else: #crop is lavender
            gold = int(gold / 2)

        return {
            'gold' : int(gold * multiplier),
            'gravitas' : int(gravitas * multiplier)
        }

    def calculate_adventure_length(self, start):
        elapsed_time = time.time() - start

        if elapsed_time >= 86400: #Over a day
            days = int(elapsed_time / 86400)
            leftover = elapsed_time % 86400

            return f"{days}:" + time.strftime("%H:%M:%S",
                                                    time.gmtime(leftover))

        elif elapsed_time >= 3600: #Over an hour
            return time.strftime("%H:%M:%S",
                                 time.gmtime(elapsed_time))

        else:
            return time.strftime("%M:%S",
                                 time.gmtime(elapsed_time))

    @commands.group(invoke_without_command=True, case_insensitive=True)
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_farmer)
    async def farm(self, ctx):
        """[FARMER EXCLUSIVE] View your farm. 
        Farms function similarly to expeditions, except that you are free to travel and go on expeditions while farming.
        You can cultivate two crops: alfalfa and lavender. Farming alfalfa will net you lots of gold, whereas farming lavender will net you gravitas.
        To farm a crop, do `%farm alfalfa` or `%farm lavender`, and your estate will begin cultivating these crops.
        For up to a week, you will accrue rewards from your crop, until you do `%farm cultivate`.      
        """
        #Show the player's farm
        farm_info = await AssetCreation.get_player_estate(self.client.pg_con, ctx.author.id)

        embed = discord.Embed(title=f"{farm_info['user_name']}'s Farm: {farm_info['name']}",
                              description=f'This is your estate, where you grow some crops for yourself. You can also farm one of two crops (alfalfa, lavender) to net you some gold and gravitas. Do `{ctx.prefix}farm help` for more information.',
                              color=self.client.ayesha_blue)
        
        if farm_info['adventure'] is not None:
            hours = (time.time() - farm_info['adventure']) / 3600
            converted_level = (farm_info['prestige'] * 100) + farm_info['lvl']
            reward_multiplier = (int(converted_level/20) / 40) + 1 #2.5% increase in rewards for every 20 levels
            reward_preview = self.calculate_farm_rewards(farm_info['type'], hours, reward_multiplier)

            embed.add_field(name='Current Rewards',
                            value=f"{reward_preview['gold']} Gold | {reward_preview['gravitas']} Gravitas")
            embed.add_field(name='Current Session',
                            value=f"Farming **{farm_info['type']}** for `{self.calculate_adventure_length(farm_info['adventure'])}`")
        else:
            embed.add_field(name='Current Rewards',
                            value=f"Do `{ctx.prefix}farm alfalfa/lavender` to start earning!")
            embed.add_field(name='Current Session',
                            value=f"Nothing set.")

        try:
            embed.set_image(url=farm_info['image'])
            return await ctx.reply(embed=embed)
        except discord.HTTPException:
            embed.set_image(url="https://i.imgur.com/fO5DXLk.jpg")
            return await ctx.reply(embed=embed)

    @farm.command(aliases=['a'])
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_farmer)
    async def alfalfa(self, ctx):
        """Begin farming alfalfa, netting you lots of gold.
        Do `%farm cultivate` anytime within a week of this command to receive your rewards.
        """
        #Check to see if a crop is already being cultivated.
        farm_info = await AssetCreation.get_player_estate(self.client.pg_con, ctx.author.id)

        if farm_info['adventure'] is not None:
            return await ctx.reply(f"You have currently been farming **{farm_info['type']}** for **{self.calculate_adventure_length(farm_info['adventure'])}**. Please do `{ctx.prefix}farm cultivate` if you wish to end this farming session.")

        await AssetCreation.farm_crop(self.client.pg_con, ctx.author.id, 'alfalfa')
        await ctx.reply(f'You have begun farming **alfalfa**. You will gain rewards for up to a week, but can end this farming session at any time by doing `{ctx.prefix}farm cultivate`.')

    @farm.command(aliases=['l'])
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_farmer)
    async def lavender(self, ctx):
        """Begin farming lavender, netting you lots of gravitas.
        Do `%farm cultivate` anytime within a week of this command to receive your rewards.
        """
        #Check to see if a crop is already being cultivated.
        farm_info = await AssetCreation.get_player_estate(self.client.pg_con, ctx.author.id)

        if farm_info['adventure'] is not None:
            return await ctx.reply(f"You have currently been farming **{farm_info['type']}** for **{self.calculate_adventure_length(farm_info['adventure'])}**. Please do `{ctx.prefix}farm cultivate` if you wish to end this farming session.")

        await AssetCreation.farm_crop(self.client.pg_con, ctx.author.id, 'lavender')
        await ctx.reply(f'You have begun farming **lavender**. You will gain rewards for up to a week, but can end this farming session at any time by doing `{ctx.prefix}farm cultivate`.')

    @farm.command(aliases=['c','grow'])
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_farmer)
    async def cultivate(self, ctx):
        """Claim your farm rewards."""
        #Check to see if a crop is already being cultivated.
        farm_info = await AssetCreation.get_player_estate(self.client.pg_con, ctx.author.id)

        if farm_info['adventure'] is None:
            return await ctx.reply(f'You are not currently farming anything. Do `{ctx.prefix}farm alfalfa/lavender` to do so!')

        hours = (time.time() - farm_info['adventure']) / 3600
        converted_level = (farm_info['prestige'] * 100) + farm_info['lvl']
        reward_multiplier = (int(converted_level/20) / 40) + 1 #2.5% increase in rewards for every 20 levels
        rewards = self.calculate_farm_rewards(farm_info['type'], hours, reward_multiplier)

        await AssetCreation.nullify_class_estate(self.client.pg_con, ctx.author.id)
        await AssetCreation.giveGold(self.client.pg_con, rewards['gold'], ctx.author.id)
        await AssetCreation.give_gravitas(self.client.pg_con, ctx.author.id, rewards['gravitas'])

        await ctx.reply(f"You cultivated your crops and received `{rewards['gold']}` gold and `{rewards['gravitas']}` gravitas!")

    @farm.command()
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_farmer)
    async def rename(self, ctx, *, name: str):
        """`name`: the new name of your farm
        
        Rename your estate.
        """
        if len(name) > 32:
            return await ctx.reply(f'Your estate name must be at most 32 characters. You gave {len(name)}.')

        await AssetCreation.rename_estate(self.client.pg_con, ctx.author.id, name)
        await ctx.reply(f'Your farm is now called {name}.')

    @farm.command(aliases=['icon', 'img'])
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_farmer)
    async def image(self, ctx, url : str):
        """`url`: a valid image URL
        
        Change the image displayed when viewing your farm.
        """
        if len(url) > 256:
            return await ctx.reply('Icon URL max 256 characters. Please upload your image to imgur or tinurl for an appropriate link.')

        try:
            async with aiohttp.ClientSession() as client:
                resp = await client.get(url)
                img = resp.headers.get('content-type')
                if img not in ('image/jpeg', 'image/png', 'image/gif'):
                    return await ctx.reply('This is an invalid URL.')

        except aiohttp.InvalidURL:
            return await ctx.reply('This is an invalid URL.')

        #Change icon
        await AssetCreation.change_estate_image(self.client.pg_con, ctx.author.id, url)
        await ctx.reply('Image set!')

    @farm.command()
    async def help(self, ctx):
        """View the list of farmer exclusive commands."""
        helper = menus.MenuPages(source=PageMaker(PageMaker.paginate_help(ctx=ctx,
                                                                          command='farm',
                                                                          help_for='Farm')), 
                                 clear_reactions_after=True, 
                                 delete_message_after=True)
        await helper.start(ctx)

    # -------------------------------------
    # ----- HUNTER EXCLUSIVE COMMANDS -----
    # -------------------------------------

    @commands.group(aliases=['companion', 'familiar'], invoke_without_command=True, case_insensitive=True)
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_hunter)
    async def pet(self, ctx):
        """[HUNTER EXCLUSIVE] See your pet. Rename your pet with the `pet rename` command.
        Pets are your own animal companion and can retrieve various items for you with the `pet retrieve` command. The amount/rarity of what you get scales with your level.
        """
        pet_info = await AssetCreation.get_player_estate(self.client.pg_con, ctx.author.id)

        embed = discord.Embed(title=f"{pet_info['user_name']}'s Pet: {pet_info['name']}",
                              description=f"Your pet can retrieve gold, resources, and items for you!\n`{ctx.prefix}pet retrieve` `{ctx.prefix}pet rename` `{ctx.prefix}pet image`",
                              color=self.client.ayesha_blue)

        try:
            embed.set_image(url=pet_info['image'])
            return await ctx.reply(embed=embed)
        except discord.HTTPException:
            embed.set_image(url="https://i.imgur.com/s9t3zdi.png")
            return await ctx.reply(embed=embed)
        

    @pet.command(aliases=['play', 'get'])
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_hunter)
    @cooldown(1, 10800, type=BucketType.user)
    async def retrieve(self, ctx):
        """Have your pet retrieve an item for you. You may get gold, resources, or a weapon."""
        # 33% chance each for gold, resources, weapon
        prestige = await AssetCreation.getPrestige(self.client.pg_con, ctx.author.id)
        level = await AssetCreation.getLevel(self.client.pg_con, ctx.author.id)
        converted_level = int(((prestige * 100) + level) / 20) + 1 # Upgrade every 20 levels

        pet_info = await AssetCreation.get_player_estate(self.client.pg_con, ctx.author.id)
        
        thing = random.choice(['Gold', 'Resources', 'Weapon'])

        if thing == 'Gold':
            gold = random.randint(15000, 25000)
            gold = int(gold * ((converted_level/50)+1)) #2% increase every 20 levels
            await AssetCreation.giveGold(self.client.pg_con, gold, ctx.author.id)
            await ctx.reply(f"**{pet_info['name']}** retrieved `{gold}` gold for you!")

        elif thing == 'Resources':
            material = random.choice('fur', 'bone', 'iron', 'silver', 'wood', 'wheat', 'oat', 'reeds', 'pine', 'moss', 'cacao')
            amount = int(random.randint(400, 700) * ((converted_level/50)+1))
            await AssetCreation.giveMat(self.client.pg_con, material, amount, ctx.author.id)
            await ctx.reply(f"**{pet_info['name']}** retrieved `{amount} {material}` gold for you!")

        else:
            rarity = random.choices(['Uncommon','Rare','Epic','Legendary'],
                                    [60, 34, 5, 1])[0]
            if rarity == 'Uncommon':
                attack = random.randint(30, 60)

            elif rarity == 'Rare':
                attack = random.randint(45, 90)

            elif rarity == 'Epic':
                attack = random.randint(75, 120)

            else:
                attack = random.randint(100, 150)

            item = await AssetCreation.createItem(self.client.pg_con, ctx.author.id, attack, rarity, returnstats=True)

            await ctx.reply(f"**{pet_info['name']}** retrieved the {item['Rarity']} **{item['Name']}** for you! Find it in your `{ctx.prefix}inventory`!")

    @pet.command()
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_hunter)
    async def rename(self, ctx, *, name: str):
        """`name`: the new name of your pet
        
        Rename your pet.
        """
        pet_info = await AssetCreation.get_player_estate(self.client.pg_con, ctx.author.id)
        if len(name) > 32:
            return await ctx.reply(f'Your pet\'s name can be at most 32 characters. You gave {len(name)}.')

        await AssetCreation.rename_estate(self.client.pg_con, ctx.author.id, name)
        await ctx.reply(f'Your pet is now named {name}.')

    @pet.command(aliases=['icon', 'img'])
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_hunter)
    async def image(self, ctx, url : str):
        """`url`: a valid image URL
        
        Change the image displayed when viewing your pet.
        """
        pet_info = await AssetCreation.get_player_estate(self.client.pg_con, ctx.author.id)
        if len(url) > 256:
            return await ctx.reply('Icon URL max 256 characters. Please upload your image to imgur or tinurl for an appropriate link.')

        try:
            async with aiohttp.ClientSession() as client:
                resp = await client.get(url)
                img = resp.headers.get('content-type')
                if img not in ('image/jpeg', 'image/png', 'image/gif'):
                    return await ctx.reply('This is an invalid URL.')

        except aiohttp.InvalidURL:
            return await ctx.reply('This is an invalid URL.')

        #Change icon
        await AssetCreation.change_estate_image(self.client.pg_con, ctx.author.id, url)
        await ctx.reply('Image set!')

    @pet.command()
    async def help(self, ctx):
        """View the list of hunter exclusive commands."""
        helper = menus.MenuPages(source=PageMaker(PageMaker.paginate_help(ctx=ctx,
                                                                          command='pet',
                                                                          help_for='Hunter Companions')), 
                                 clear_reactions_after=True, 
                                 delete_message_after=True)
        await helper.start(ctx)
            
    # --------------------------------------
    # ----- BUTCHER EXCLUSIVE COMMANDS -----
    # --------------------------------------

    def calculate_butcher_rewards(self, hours, multiplier):
        """Return xp gained given the time passed (hours) and the reward multiplier given."""
        xp = 0

        if hours > 168:
            hours = 168

        if hours < 24:
            xp = hours * 550
        elif hours < 72:
            xp = hours * 580
        else:
            xp = hours * 600

        return int(xp * multiplier)

    @commands.group(aliases=['bu'], invoke_without_command=True, case_insensitive=True)
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_butcher)
    async def butchery(self, ctx):
        """[BUTCHER EXCLUSIVE] View your butchery. Do `%bu help` for related commands.
        Your butchery functions similar to expeditions, except that you primarily gain xp using the `%bu cut` command.
        For up to a week, you will accrue rewards from your crop, until you do `%bu clean`.  
        """
        #Show the player's butcher shop
        info = await AssetCreation.get_player_estate(self.client.pg_con, ctx.author.id)

        embed = discord.Embed(title=f"{info['user_name']}'s Butchery: {info['name']}",
                              description=f'This is your estate, where you cut, cure, and sell meats. You gain xp with the expedition-like `{ctx.prefix}bu cut` command. Do `{ctx.prefix}bu help` for more information.',
                              color=self.client.ayesha_blue)
        
        if info['adventure'] is not None:
            hours = (time.time() - info['adventure']) / 3600
            converted_level = (info['prestige'] * 100) + info['lvl']
            reward_multiplier = (int(converted_level/20) / 40) + 1 #2.5% increase in rewards for every 20 levels
            xp_preview = self.calculate_butcher_rewards(hours, reward_multiplier)

            embed.add_field(name='Current Rewards',
                            value=f"{xp_preview} Experience")
            embed.add_field(name='Current Session',
                            value=f"Working for `{self.calculate_adventure_length(info['adventure'])}`")
        else:
            embed.add_field(name='Current Rewards',
                            value=f"Do `{ctx.prefix}bu cut` to start earning!")
            embed.add_field(name='Current Session',
                            value=f"Nothing set.")

        try:
            embed.set_image(url=info['image'])
            return await ctx.reply(embed=embed)
        except discord.HTTPException:
            embed.set_image(url="https://i.imgur.com/IYp55Cv.png")
            return await ctx.reply(embed=embed)

    @butchery.command(aliases=['c','work'])
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_butcher)
    async def cut(self, ctx):
        """Begin working your butchery, netting you (and your acolytes) experience.
        Do `%bu clean` anytime within a week of this command to receive your rewards.
        """
        #Check to see if an expedition is already being done.
        info = await AssetCreation.get_player_estate(self.client.pg_con, ctx.author.id)

        if info['adventure'] is not None:
            return await ctx.reply(f"You have currently been working at your butchery for **{self.calculate_adventure_length(info['adventure'])}**. Please do `{ctx.prefix}bu cut` if you wish to end this session.")

        await AssetCreation.begin_estate_session(self.client.pg_con, ctx.author.id)
        await ctx.reply(f'You have begun working at your butchery. You will gain rewards for up to a week, but can stop at any time by doing `{ctx.prefix}bu clean`.')

    @butchery.command()
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_butcher)
    async def clean(self, ctx):
        """Claim your butchery rewards."""
        #Check to see if work is being performed.
        info = await AssetCreation.get_player_estate(self.client.pg_con, ctx.author.id)

        if info['adventure'] is None:
            return await ctx.reply(f'You are not currently working your butchery. Do `{ctx.prefix}bu cut` to do so!')

        #Calculate rewards
        hours = (time.time() - info['adventure']) / 3600
        converted_level = (info['prestige'] * 100) + info['lvl']
        reward_multiplier = (int(converted_level/20) / 40) + 1 #2.5% increase in rewards for every 20 levels
        xp = self.calculate_butcher_rewards(hours, reward_multiplier)

        #Give rewards
        await AssetCreation.nullify_class_estate(self.client.pg_con, ctx.author.id)
        await AssetCreation.givePlayerXP(self.client.pg_con, xp, ctx.author.id)

        acolyte1, acolyte2 = await AssetCreation.getAcolyteFromPlayer(self.client.pg_con, ctx.author.id)
        if acolyte1 is not None:
            await AssetCreation.giveAcolyteXP(self.client.pg_con, int(xp/10), acolyte1)
        if acolyte2 is not None:
            await AssetCreation.giveAcolyteXP(self.client.pg_con, int(xp/10), acolyte2)

        await ctx.reply(f"You cleaned up your shop after working, gaining `{xp}` xp.")
        await AssetCreation.checkLevel(self.client.pg_con, ctx, ctx.author.id, aco1=acolyte1, aco2=acolyte2)

    @butchery.command()
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_butcher)
    async def rename(self, ctx, *, name: str):
        """`name`: the new name of your butcher shop
        
        Rename your estate.
        """
        if len(name) > 32:
            return await ctx.reply(f'Your estate name must be at most 32 characters. You gave {len(name)}.')

        await AssetCreation.rename_estate(self.client.pg_con, ctx.author.id, name)
        await ctx.reply(f'Your butchery is now called {name}.')

    @butchery.command(aliases=['icon','img'])
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_butcher)
    async def image(self, ctx, url : str):
        """`url`: a valid image URL
        
        Change the image displayed when viewing your butchery.
        """
        if len(url) > 256:
            return await ctx.reply('Icon URL max 256 characters. Please upload your image to imgur or tinurl for an appropriate link.')

        try:
            async with aiohttp.ClientSession() as client:
                resp = await client.get(url)
                img = resp.headers.get('content-type')
                if img not in ('image/jpeg', 'image/png', 'image/gif'):
                    return await ctx.reply('This is an invalid URL.')

        except aiohttp.InvalidURL:
            return await ctx.reply('This is an invalid URL.')

        #Change icon
        await AssetCreation.change_estate_image(self.client.pg_con, ctx.author.id, url)
        await ctx.reply('Image set!')

    @butchery.command()
    async def help(self, ctx):
        """View the list of butcher exclusive commands."""
        helper = menus.MenuPages(source=PageMaker(PageMaker.paginate_help(ctx=ctx,
                                                                          command='butchery',
                                                                          help_for='Butchery')), 
                                 clear_reactions_after=True, 
                                 delete_message_after=True)
        await helper.start(ctx)

    # -------------------------------------
    # ----- SCRIBE EXCLUSIVE COMMANDS -----
    # -------------------------------------

    def calculate_scribe_rewards(self, hours, multiplier):
        """Return gravitas gained given the time passed (hours) and the reward multiplier given."""
        gravitas = 0

        if hours > 168:
            hours = 168

        if hours < 24:
            gravitas = hours * .85
        elif hours < 72:
            gravitas = hours
        else:
            gravitas = hours * 1.15

        return int(gravitas * multiplier)

    @commands.group(aliases=['sc'], invoke_without_command=True, case_insensitive=True)
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_scribe)
    async def scriptorium(self, ctx):
        """[SCRIBE EXCLUSIVE] View your scriptorium. Do `%sc help` for related commands.
        Your butchery functions similar to expeditions, except that you primarily gain gravitas using the `%sc write` command.
        For up to a week, you will accrue rewards from writing, until you do `%sc publish`.  
        """
        #Show the player's butcher shop
        info = await AssetCreation.get_player_estate(self.client.pg_con, ctx.author.id)

        embed = discord.Embed(title=f"{info['user_name']}'s Scriptortium: {info['name']}",
                              description=f'This is your estate, where write, copy, and research. You gain gravitas with the expedition-like `{ctx.prefix}sc write` command. Do `{ctx.prefix}sc help` for more information.',
                              color=self.client.ayesha_blue)
        
        if info['adventure'] is not None:
            hours = (time.time() - info['adventure']) / 3600
            converted_level = (info['prestige'] * 100) + info['lvl']
            reward_multiplier = (int(converted_level/20) / 40) + 1 #2.5% increase in rewards for every 20 levels
            gravitas_preview = self.calculate_scribe_rewards(hours, reward_multiplier)

            embed.add_field(name='Current Rewards',
                            value=f"{gravitas_preview} Gravitas")
            embed.add_field(name='Current Session',
                            value=f"Writing for `{self.calculate_adventure_length(info['adventure'])}`")
        else:
            embed.add_field(name='Current Rewards',
                            value=f"Do `{ctx.prefix}sc write` to start earning!")
            embed.add_field(name='Current Session',
                            value=f"Nothing set.")

        try:
            embed.set_image(url=info['image'])
            return await ctx.reply(embed=embed)
        except discord.HTTPException:
            embed.set_image(url="https://i.imgur.com/eMth0Jg.png")
            return await ctx.reply(embed=embed)

    @scriptorium.command(aliases=['w','work','copy'])
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_scribe)
    async def write(self, ctx):
        """Begin writing in your scriptorium, netting you gravitas.
        Do `%sc publish` anytime within a week of this command to receive your rewards.
        """
        #Check to see if an expedition is already being done.
        info = await AssetCreation.get_player_estate(self.client.pg_con, ctx.author.id)

        if info['adventure'] is not None:
            return await ctx.reply(f"You have currently been working at your desk for **{self.calculate_adventure_length(info['adventure'])}**. Please do `{ctx.prefix}sc publish` if you wish to end this session.")

        await AssetCreation.begin_estate_session(self.client.pg_con, ctx.author.id)
        await ctx.reply(f'You have begun working at your scriptorium. You will gain rewards for up to a week, but can stop at any time by doing `{ctx.prefix}sc publish`.')

    @scriptorium.command()
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_scribe)
    async def publish(self, ctx):
        """Claim your scriptorium rewards."""
        #Check to see if work is being performed.
        info = await AssetCreation.get_player_estate(self.client.pg_con, ctx.author.id)

        if info['adventure'] is None:
            return await ctx.reply(f'You are not currently working your desk. Do `{ctx.prefix}sc write` to do so!')

        #Calculate rewards
        hours = (time.time() - info['adventure']) / 3600
        converted_level = (info['prestige'] * 100) + info['lvl']
        reward_multiplier = (int(converted_level/20) / 40) + 1 #2.5% increase in rewards for every 20 levels
        gravitas = self.calculate_scribe_rewards(hours, reward_multiplier)

        #Give rewards
        await AssetCreation.nullify_class_estate(self.client.pg_con, ctx.author.id)
        await AssetCreation.give_gravitas(self.client.pg_con, ctx.author.id, gravitas)

        await ctx.reply(f"You published your manuscripts, gaining `{gravitas}` gravitas.")

    @scriptorium.command()
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_scribe)
    async def rename(self, ctx, *, name: str):
        """`name`: the new name of your scriptorium
        
        Rename your estate.
        """
        if len(name) > 32:
            return await ctx.reply(f'Your estate name must be at most 32 characters. You gave {len(name)}.')

        await AssetCreation.rename_estate(self.client.pg_con, ctx.author.id, name)
        await ctx.reply(f'Your scriptorium is now called {name}.')

    @scriptorium.command(aliases=['icon', 'img'])
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_scribe)
    async def image(self, ctx, url : str):
        """`url`: a valid image URL
        
        Change the image displayed when viewing your scriptorium.
        """
        if len(url) > 256:
            return await ctx.reply('Icon URL max 256 characters. Please upload your image to imgur or tinurl for an appropriate link.')

        try:
            async with aiohttp.ClientSession() as client:
                resp = await client.get(url)
                img = resp.headers.get('content-type')
                if img not in ('image/jpeg', 'image/png', 'image/gif'):
                    return await ctx.reply('This is an invalid URL.')

        except aiohttp.InvalidURL:
            return await ctx.reply('This is an invalid URL.')

        #Change icon
        await AssetCreation.change_estate_image(self.client.pg_con, ctx.author.id, url)
        await ctx.reply('Image set!')

    @scriptorium.command()
    async def help(self, ctx):
        """View the list of scribe exclusive commands."""
        helper = menus.MenuPages(source=PageMaker(PageMaker.paginate_help(ctx=ctx,
                                                                          command='scriptorium',
                                                                          help_for='Scriptorium')), 
                                 clear_reactions_after=True, 
                                 delete_message_after=True)
        await helper.start(ctx)


def setup(client):
    client.add_cog(Classes(client))