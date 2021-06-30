import discord
import asyncio

from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

from Utilities import Checks, AssetCreation, PageSourceMaker

import time

occupations = {
    'Soldier' : 'You are a retainer of a local lord, trained in the discipline of swordsmanship.\nYour base character ATK is boosted by 20% and you get a bonus 10 ATK.',
    'Blacksmith' : 'You\'ve spent years as the apprentice of a hardy blacksmith, and now a master in the art of forging.\nYour weapon ATK is boosted by 10% and you get a bonus 10 ATK.',
    'Farmer' : 'You are a lowly farmer, but farming is no easy job.\nYou gain extra gravitas every day.',
    'Hunter' : 'The wild is your domain; no game unconquerable.\nYou gain double rewards from hunting.',
    'Merchant' : 'Screw you, exploiter of others\' labor.\nYou gain 50% increased income from selling items.',
    'Traveler' : 'The wild forests up north await, as do the raging seas to the south. What will you discover?\nYou gain triple gold from travel and double rewards from foraging.',
    'Leatherworker' : 'The finest protective gear, saddles, and equipment have your name on it.\nYou have 200 increased HP.',
    'Butcher' : 'Meat. What would one do without it?\nYou have double healing effectiveness.',
    'Engineer' : 'Your lord praises the seemingly impossible design of his new manor.\nYou will gain increased rewards from exclusive association commands.',
    'Scribe' : 'Despite the might of your lord, you\'ve learned a little bit about everything too.\nYou have an additional 10% crit rate.'
}

origins = {
    'Aramithea' : 'You\'re a metropolitan. Aramithea, the largest city on Rabidus, must have at least a million people, and a niche for everybody',
    'Riverburn' : 'The great rival of Aramithea; Will you bring your town to victory?',
    'Thenuille' : 'You love the sea; you love exploration; you love trade. From here one can go anywhere, and be anything',
    'Mythic Forest' : 'You come from the lands down south, covered in forest. You could probably hit a deer square between the eyes blindfolded.',
    'Sunset' : 'Nothing is more peaceful than an autumn afternoon in the prairie.',
    'Lunaris' : 'The crossroads of civilization; the battleground of those from the north, west, and east. Your times here have hardened you.',
    'Crumidia' : 'The foothills have turned you into a strong warrior. Perhaps you will seek domination over your adversaries?',
    'Maritimiala' : 'North of the mountains, the Maritimialan tribes look lustfully upon the fertile plains below. Will you seek integration, or domination?',
    'Glakelys' : 'The small towns beyond Riverburn disregard the Aramithean elite. The first line of defense from invasions from Lunaris, the Glakelys are as tribal as they were 300 years ago.'
}

occ = enumerate(occupations)
occ = list(occ)

# 8. Engineer - buff steal/invest slightly - implemented

ori = enumerate(origins)
ori = list(ori)

class Classes(commands.Cog):
    """Customize your character!"""

    def __init__(self, client):
        self.client = client
        self.client.classes = ('Soldier', # 20% bonus to character ATK; 1 gravitas daily
                                    # Command: 50% more damage from raid attack
                                    # Weapon Bonus: Spear, Sword [CODE FOUND IN AssetCreation.get_attack_crit_hp()]
                               'Blacksmith', # Double gold and materials from mine; Half cost from upgrading weapons
                                    # Command: smith - merge command with +2 ATK and 100k gold cost
                                    # Weapon Bonus: Greatsword, Gauntlets
                               'Farmer', # 4 gravitas daily
                                    # Command: farm - passively gain gold and gravitas
                                    # Weapon Bonus: Sling, Falx
                               'Hunter', # Double gold and materials from hunt
                                    # Command: raise - have a pet that gets you other things
                                    # Weapon Bonus: Bow, Javelin
                               'Merchant', # 50% increase gold from selling
                                    # Command: 50% increased gold from shop sell
                                    # Weapon Bonus: Dagger, Mace
                               'Traveler', # Triple gold from traveling, double materials from forage
                                    # Command: 50% to gain an acolyte from a long expedition
                                    # Weapon Bonus: Staff, Javelin
                               'Leatherworker', # 250 more hp
                                    # Command: Take 15% less damage from every hit in PvE
                                    # Weapon Bonus: Mace, Axe
                               'Butcher', # heal double (pve and pvp)
                                    # Command: slaughter - passively gain xp
                                    # Weapon Bonus: Axe, Dagger
                               'Engineer', # Associations: Steal 10% of gold instead of 5, 25% buff to guild invest, gain 5 gravitas from cl usurp
                                    # Command: Crit hits in PvE and PvP deal 1.75x damage instead of 1.5x
                                    # Weapon Bonus: Trebuchet, Falx
                               'Scribe') # 10 Crit; 1 gravitas daily
                                    # Command: research - passively gain gravitas
                                    # Weapon Bonus: Sword, Dagger

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
            for job in occupations:
                embed = discord.Embed(title='Class Selection Menu', 
                                      color=self.client.ayesha_blue)
                embed.add_field(name=f'{job}: Say `{ctx.prefix}class {job}` to take this class!', 
                                value=f'{occupations[job]}')
                entries.append(embed)

            tavern = menus.MenuPages(source=PageSourceMaker.PageMaker(entries), 
                                     clear_reactions_after=True, 
                                     delete_message_after=True)
            await tavern.start(ctx)

        else:
            player_job = player_job.title()

            if player_job not in (occupations):
                return await ctx.reply(f'This is not a valid class. Please do `{ctx.prefix}class` with no arguments to see the list of classes.')

            else:
                await AssetCreation.setPlayerClass(self.client.pg_con, player_job, ctx.author.id)
                await AssetCreation.delete_player_estate(self.client.pg_con, ctx.author.id)
                await ctx.reply(f'You are now a {player_job}!')
        
    @cooldown(1, 3600, BucketType.user)
    @commands.command(aliases=['background','birthplace'], description='Choose your birthplace.')
    async def origin(self, ctx, *, player_origin : str = None):
        """`player_origin`: Your birthplace. To see the valid areas, just do `origin`

        Choose your homeland.
        """
        if player_origin is None:
            ctx.command.reset_cooldown(ctx)

            entries = []
            for place in origins:
                embed = discord.Embed(title='Background Selection Menu', color=self.client.ayesha_blue)
                embed.add_field(name=f'{place}: Say `{ctx.prefix}origin {place}` if you like this place!', 
                                value=f'{origins[place]}')
                entries.append(embed)   

            tavern = menus.MenuPages(source=PageSourceMaker.PageMaker(entries), 
                                     clear_reactions_after=True, 
                                     delete_message_after=True)
            await tavern.start(ctx)

        else:
            player_origin = player_origin.title()

            if player_origin not in (origins):
                await ctx.reply(f'This is not a valid place. Please do `{ctx.prefix}origin` with no arguments to see the list of backgrounds.')
                return

            else:
                await AssetCreation.setPlayerOrigin(self.client.pg_con, player_origin, ctx.author.id)
                await ctx.send(f'{ctx.author.mention}, you are from {player_origin}!')

    @commands.command(aliases=['smith'])
    @commands.check(Checks.is_player)
    async def forge(self, ctx, buff_item : int, fodder : int):
        """`buff_item`: the item you want strengthened
        `fodder`: the item you are destroying to strengthen the other weapon
        
        [BLACKSMITH EXCLUSIVE] Merge an item into another to boost its ATK by 2. The fodder item must be of the same weapontype and have at least 15 less ATK than the buffed item. Merging this way costs 100,000 gold.
        """
        #Make sure the player is a blacksmith
        if await AssetCreation.getClass(self.client.pg_con, ctx.author.id) != 'Blacksmith':
            return await ctx.reply(f'This command is exclusive to blacksmiths only! You can use the similar `{ctx.prefix}merge` command. \nIf you wish to change classes, do `{ctx.prefix}class Blacksmith`.')

        #Make sure player owns both items and that the fodder is NOT equipped
        if not await AssetCreation.verifyItemOwnership(self.client.pg_con, buff_item, ctx.author.id):
            return await ctx.reply(f'You do not own an item with ID `{buff_item}`.')
        if not await AssetCreation.verifyItemOwnership(self.client.pg_con, fodder, ctx.author.id):
            return await ctx.reply(f'You do not own an item with ID `{fodder}`.')

        if fodder == await AssetCreation.getEquippedItem(self.client.pg_con, ctx.author.id):
            return await ctx.reply('You cannot use your currently equipped item as fodder material.')

        cost_info = await AssetCreation.calc_cost_with_tax_rate(self.client.pg_con, 100000)
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

    def calculate_farm_rewards(self, crop, hours, multiplier):
        gold = 0
        gravitas = 0

        if hours < 24:
            gold = hours * 250
            gravitas = hours * .65
        elif hours > 72:
            gold = hours * 275
            gravitas = hours * .8
        else:
            if hours > 168:
                hours = 168
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
    async def farm(self, ctx):
        """[FARMER EXCLUSIVE] View your farm. 
        Farms function similarly to expeditions, except that you are free to travel and go on expeditions while farming.
        You can cultivate two crops: alfalfa and lavender. Farming alfalfa will net you lots of gold, whereas farming lavender will net you gravitas.
        To farm a crop, do `%farm alfalfa` or `%farm lavender`, and your estate will begin cultivating these crops.
        For up to a week, you will accrue rewards from your crop, until you do `%farm cultivate`.      
        """
        #Make sure this player is a farmer
        if await AssetCreation.getClass(self.client.pg_con, ctx.author.id) != 'Farmer':
            return await ctx.reply(f'This command is exclusive to farmers only!\nIf you wish to change classes, do `{ctx.prefix}class Farmer`.')

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

        return await ctx.reply(embed=embed)

    @farm.command(aliases=['a'])
    @commands.check(Checks.is_player)
    async def alfalfa(self, ctx):
        """Begin farming alfalfa, netting you lots of gold.
        Do `%farm cultivate` anytime within a week of this command to receive your rewards.
        """
        #Make sure this player is a farmer
        if await AssetCreation.getClass(self.client.pg_con, ctx.author.id) != 'Farmer':
            return await ctx.reply(f'This command is exclusive to farmers only!\nIf you wish to change classes, do `{ctx.prefix}class Farmer`.')

        #Check to see if a crop is already being cultivated.
        farm_info = await AssetCreation.get_player_estate(self.client.pg_con, ctx.author.id)

        if farm_info['adventure'] is not None:
            return await ctx.reply(f"You have currently been farming **{farm_info['type']}** for **{self.calculate_adventure_length(farm_info['adventure'])}**. Please do `{ctx.prefix}farm cultivate` if you wish to end this farming session.")

        await AssetCreation.farm_crop(self.client.pg_con, ctx.author.id, 'alfalfa')
        await ctx.reply(f'You have begun farming **alfalfa**. You will gain rewards for up to a week, but can end this farming session at any time by doing `{ctx.prefix}farm cultivate`.')

    @farm.command(aliases=['l'])
    @commands.check(Checks.is_player)
    async def lavender(self, ctx):
        """Begin farming lavender, netting you lots of gravitas.
        Do `%farm cultivate` anytime within a week of this command to receive your rewards.
        """
        #Make sure this player is a farmer
        if await AssetCreation.getClass(self.client.pg_con, ctx.author.id) != 'Farmer':
            return await ctx.reply(f'This command is exclusive to farmers only!\nIf you wish to change classes, do `{ctx.prefix}class Farmer`.')

        #Check to see if a crop is already being cultivated.
        farm_info = await AssetCreation.get_player_estate(self.client.pg_con, ctx.author.id)

        if farm_info['adventure'] is not None:
            return await ctx.reply(f"You have currently been farming **{farm_info['type']}** for **{self.calculate_adventure_length(farm_info['adventure'])}**. Please do `{ctx.prefix}farm cultivate` if you wish to end this farming session.")

        await AssetCreation.farm_crop(self.client.pg_con, ctx.author.id, 'lavender')
        await ctx.reply(f'You have begun farming **lavender**. You will gain rewards for up to a week, but can end this farming session at any time by doing `{ctx.prefix}farm cultivate`.')

    @farm.command(aliases=['c'])
    @commands.check(Checks.is_player)
    async def cultivate(self, ctx):
        """Claim your farm rewards."""
        #Make sure this player is a farmer
        if await AssetCreation.getClass(self.client.pg_con, ctx.author.id) != 'Farmer':
            return await ctx.reply(f'This command is exclusive to farmers only!\nIf you wish to change classes, do `{ctx.prefix}class Farmer`.')

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
    async def rename(self, ctx, *, name: str):
        """`name`: the new name of your farm
        
        Rename your estate.
        """
        #Make sure this player is a farmer
        if await AssetCreation.getClass(self.client.pg_con, ctx.author.id) != 'Farmer':
            return await ctx.reply(f'This command is exclusive to farmers only!\nIf you wish to change classes, do `{ctx.prefix}class Farmer`.')

        if len(name) > 32:
            return await ctx.reply(f'Your estate name must be at most 32 characters. You gave {len(name)}.')

        await AssetCreation.rename_estate(self.client.pg_con, ctx.author.id, name)
        await ctx.reply(f'Your farm is now called {name}.')

    @farm.command()
    async def help(self, ctx):
        """View the list of farmer exclusive commands."""
        def write_help_embed(ctx, start, entries):
            """Return a help embed for up to 5 commands in the given list.
            
            Parameters
            ----------
            ctx: commands.Context
                the context of the command invocation
            start: int
                the index of the first value in entries being written
            entries: list
                a list of commands
            cog: str
                the name of the cog for which help is being sought

            Returns
            -------
            helpEmbed: discord.Embed
                an embed to be displayed to the user
            """
            helpEmbed = discord.Embed(title=f'Ayesha Help: Farm')
            helpEmbed.set_thumbnail(url=ctx.author.avatar_url)
            
            iteration = 0
            while start < len(entries) and iteration < 5: #Will loop until 5 entries are processed or there's nothing left in the queue
                command_info = write_help_for_command(entries[start])
                helpEmbed.add_field(name=command_info['name'],
                                    value=command_info['help'],
                                    inline=False)

                iteration += 1
                start +=1 
                
            return helpEmbed

        def write_help_for_command(command : commands.Command):
            """Return a dict containing the help output of a command.
            Dict: 'name': str including parent, name, and parameters
                'help': str containing description and aliases
            """
            if command.parent is None:
                parent = ''
            else:
                parent = command.parent.name + ' '

            if len(command.aliases) == 0:
                aliases = ''
            else:
                aliases = '**Aliases: **'
                for alias in command.aliases:
                    aliases += f'`{alias}` '

            if len(command.signature) == 0:
                params = ''
            else:
                params = f'`{command.signature}`'

            return {
                'name' : f'{parent}{command.name} {params}',
                'help' : f'{command.help}\n{aliases}'
            }

        cmds, embeds = [], []
        for command in self.client.get_command('farm').walk_commands():
            cmds.append(command)
        for i in range(0, len(cmds), 5):
            embeds.append(write_help_embed(ctx, i, cmds))

        helper = menus.MenuPages(source=PageSourceMaker.PageMaker(embeds), 
                                 clear_reactions_after=True, 
                                 delete_message_after=True)
        await helper.start(ctx)



def setup(client):
    client.add_cog(Classes(client))