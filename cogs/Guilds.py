import discord
import asyncio

from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

from Utilities import Checks, AssetCreation, PageSourceMaker

import random
import math
import aiohttp
import time

# There will be brotherhoods, guilds, and later colleges for combat, economic, and political gain

class Guilds(commands.Cog):
    """Association Type for Wealth"""
    def __init__(self, client):
        self.client = client

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('Guilds is ready.')

    @commands.group(invoke_without_command=True, case_insensitive=True, description='See your guild.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_guild)
    async def guild(self, ctx):
        """View your guild. Guilds are a financially-oriented association. Its members gain more money from selling items. They also gain access to the `invest` command.
        `guild help` will show all other commands related to this association type.
        """
        info = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        getLeader = commands.UserConverter()
        leader = await getLeader.convert(ctx, str(info['Leader']))
        level, progress = await AssetCreation.getGuildLevel(self.client.pg_con, info['ID'], returnline=True)
        members = await AssetCreation.getGuildMemberCount(self.client.pg_con, info['ID'])
        capacity = await AssetCreation.getGuildCapacity(self.client.pg_con, info['ID'])

        embed = discord.Embed(title=f"{info['Name']}", color=self.client.ayesha_blue)
        embed.set_thumbnail(url=f"{info['Icon']}")
        embed.add_field(name='Leader', value=f"{leader.mention}")
        embed.add_field(name='Members', value=f"{members}/{capacity}")
        embed.add_field(name='Level', value=f"{level}")
        embed.add_field(name='EXP Progress', value=f'{progress}')
        embed.add_field(name='Base', value=f"{info['Base']}")
        embed.add_field(name=f"This {info['Type']} is {info['Join']} to new members.", 
                        value=f"{info['Desc']}", 
                        inline=False)
        embed.set_footer(text=f"Guild ID: {info['ID']}")
        await ctx.reply(embed=embed)

    @guild.command(aliases=['found', 'establish', 'form', 'make'], 
                   brief='<name>', 
                   description='Found a guild. Costs 15,000 gold.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.not_in_guild)
    async def create(self, ctx, *, name : str):
        """`name`: the name of your guild

        Found a guild. This operation costs 15,000 gold.
        """
        if len(name) > 32:
            await ctx.reply('Name max 32 characters')
            return
        # Make sure they have the money and an open name
        if not await Checks.guild_can_be_created(ctx, name):
            return
        # Otherwise create the guild
        await AssetCreation.createGuild(self.client.pg_con, 
                                        name, 
                                        "Guild", 
                                        ctx.author.id, 
                                        'https://cdn4.iconfinder.com/data/icons/ionicons/512/icon-ios7-contact-512.png')
        await ctx.reply('Guild founded. Do `guild` to see it or `guild help` for more commands!')

    @guild.command(description='Leave your guild.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_guild)
    @commands.check(Checks.is_not_guild_leader)
    async def leave(self, ctx):
        """Leave your guild."""
        bank_info = await AssetCreation.get_guild_account(self.client.pg_con, ctx.author.id)
        if bank_info is not None:
            gold_payment = await AssetCreation.close_guild_account(self.client.pg_con)
            await AssetCreation.giveGold(self.client.pg_con, gold_payment, ctx.author.id)

        await AssetCreation.leaveGuild(self.client.pg_con, ctx.author.id)
        await ctx.reply('You left your guild.')

    @guild.command(aliases=['inv'], brief='<url>', description='Invite a player to your guild.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_guild_officer)
    @commands.check(Checks.guild_has_vacancy)
    async def invite(self, ctx, player : commands.MemberConverter):
        """`player`: the player you want to invite

        [OFFICER+] Invite a player to your guild, provided that there is space available. 
        """
        #Ensure target player has a character and is not in a guild
        if not await Checks.has_char(self.client.pg_con, player):
            await ctx.reply('This person does not have a character.')
            return
        if not await Checks.target_not_in_guild(self.client.pg_con, player):
            await ctx.reply('This player is already in an association.')
            return

        #See how recently they joined an association
        last_join = await AssetCreation.check_last_guild_join(self.client.pg_con, player.id)
        if last_join.total_seconds() < 86400:
            cd = 86400 - last_join.total_seconds()
            return await ctx.reply(f'Joining associations has a 24 hour cooldown. This player can join another association in `{time.strftime("%H:%M:%S", time.gmtime(cd))}`.')

        #Otherwise invite the player
        #Load the guild
        guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        #Create and send embed invitation
        embed = discord.Embed(color=self.client.ayesha_blue)
        embed.add_field(name=f"Invitation to {guild['Name']}", 
                        value=f"{player.mention}, {ctx.author.mention} is inviting you to join their {guild['Type']}.")

        message = await ctx.reply(embed=embed)
        await message.add_reaction('\u2705') #Check
        await message.add_reaction('\u274E') #X

        def check(reaction, user):
            return user == player and reaction.message.id == message.id

        reaction = None
        readReactions = True
        while readReactions: 
            if str(reaction) == '\u2705': #Then exchange stuff
                await message.delete()
                await AssetCreation.joinGuild(self.client.pg_con, guild['ID'], player.id)
                await ctx.send(f"Welcome to {guild['Name']}, {player.mention}!")
                break
            if str(reaction) == '\u274E':
                await message.delete()
                await ctx.reply('They declined your invitation.')
                break

            try:
                reaction, user = await self.client.wait_for('reaction_add', check=check, timeout=15.0)
                await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                readReactions = not readReactions
                await message.delete()
                await ctx.send('They did not respond to your invitation.')

    @guild.command(aliases=['donate'], 
                   brief='<money : int>', 
                   description='Donate to your association, increasing its xp!')
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_guild)
    async def contribute(self, ctx, donation : int):
        """`donation`: the amount of money you want to give your guild

        Contribute money to the strength of your guild. Every 1,000,000 gold contributed will level it up, strengthening its bonuses, up to level 10.
        """
        #Make sure they have the money they're paying and that the guild is <lvl 10
        guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        level = await AssetCreation.getGuildLevel(self.client.pg_con, guild['ID'])
        if level >= 10:
            return await ctx.reply('Your guild is already at its maximum level')

        if donation > await AssetCreation.getGold(self.client.pg_con, ctx.author.id):
            return await ctx.reply('You don\'t have that much money to donate.')

        #Remove money from account and add xp to guild
        await AssetCreation.giveGold(self.client.pg_con, 0 - donation, ctx.author.id)
        await AssetCreation.giveGuildXP(self.client.pg_con, donation, guild['ID'])

        #Also calculate how much more xp is needed for a level up
        xp = await AssetCreation.getGuildXP(self.client.pg_con, guild['ID'])
        needed = 1000000 - (xp % 1000000)
        await ctx.reply(f'You contributed `{donation}` gold to your guild. It will become level `{int(xp/1000000)+1}` at `{needed}` more xp.')

    @guild.command(description='View the other members of your guild.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_guild)
    async def members(self, ctx):
        """See a list of all your guild's members, their rank, and some stats."""
        # Get the list of members, theoretically sorted by rank
        guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        members = await AssetCreation.getGuildMembers(self.client.pg_con, guild['ID'])
        # Sort them into dpymenus pages
        member_list = []

        async def write(start, members):
            page = discord.Embed(title=f"{guild['Name']}: Members")
            iteration = 0

            while start < len(members) and iteration < 10:
                # attack, crit = await AssetCreation.getAttack(self.client.pg_con, members[start][0])
                battle_stats = await AssetCreation.get_attack_crit_hp(self.client.pg_con, members[start][0])
                level = await AssetCreation.getLevel(self.client.pg_con, members[start][0])
                player = await self.client.fetch_user(members[start][0])
                page.add_field(name=f'{player.name}: {members[start][1]} [{members[start][2]}]', 
                    value=f"Level `{level}`, with `{battle_stats['Attack']}` attack and `{battle_stats['Crit']}` crit.", inline=False)
                start += 1
                iteration += 1

            return page

        for i in range(0, len(members), 10):
            member_list.append(await write(i, members))

        member_pages = menus.MenuPages(source=PageSourceMaker.PageMaker(member_list), 
                                       clear_reactions_after=True, 
                                       delete_message_after=True)
        await member_pages.start(ctx)

    @guild.command(brief='<gold : int>', 
                   description='Invest in a project at a random location and gain/lose some money. 2 hour cooldown.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_guild)
    @cooldown(1, 7200, BucketType.user)
    async def invest(self, ctx, capital : int):
        """Invest in a project at a random location and gain/lose some money."""
        #Ensure they have enough money to invest
        if await AssetCreation.getGold(self.client.pg_con, ctx.author.id) < capital:
            await ctx.reply('You don\'t have enough money to invest that much.')
            ctx.command.reset_cooldown(ctx)
            return
        if capital > 250000:
            await ctx.reply('Whoa, that investment is too excessive. Please invest only up to 250,000 gold.')
            ctx.command.reset_cooldown(ctx)
            return

        #Get a random multplier of the money
        multplier = random.randint(40,150) / 100.0
        capital_gain = int(capital * multplier)

        #Class bonus
        role = await AssetCreation.getClass(self.client.pg_con, ctx.author.id)
        if role == 'Engineer':
            capital_gain = int(capital_gain * 1.25)

        #Choose a random project and location
        projects = ('a museum', 'a church', 'a residence', 'a fishing company', 
            'a game company', 'a guild', 'a boat', 'road construction')
        locations = ('Aramithea', 'Riverburn', 'Thenuille', 'the Mythic Forest', 
            'Fernheim', 'Thanderlands Marsh', 'Glakelys', 'Croire', 'Crumidia', 
            'Mooncastle', 'Felescity', 'Mysteria', 'a local village', 
            'your hometown', 'Oshwega')
        project = random.choice(projects)
        location = random.choice(locations)

        #Update player's money and send output
        await AssetCreation.giveGold(self.client.pg_con, capital_gain, ctx.author.id)
        await ctx.reply(f'You invested `{capital}` gold in {project} in {location} and earned a return of `{capital_gain}` gold.')

    @guild.group(aliases=['a'], invoke_without_command=True, case_insensitive=True, description='See your guild bank funds.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_guild)
    async def account(self, ctx):
        """See your guild bank account. The capacity of your account increases as your guild level increases."""
        bank_info = await AssetCreation.get_guild_account(self.client.pg_con, ctx.author.id)

        if bank_info is None:
            return await ctx.reply('You do not have a guild bank account. Do `{ctx.prefix}guild account open` to make one!')

        embed = discord.Embed(title=f"Bank of {bank_info['guild_name']}: {bank_info['user_name']}'s Account",
                              color=self.client.ayesha_blue)
        embed.add_field(name='Bank Balance', value=f"{bank_info['account_funds']} / {bank_info['capacity']}")
        embed.set_footer(text='Increase your bank capacity by levelling it up.')

        await ctx.reply(embed=embed)

    @account.command(brief='<initial deposit = 0', description='Open a bank account with your guild! If you wish, also deposit a certain amount of money once opened.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_guild)
    @commands.check(Checks.not_has_bank_account)
    async def open(self, ctx, initial_deposit : int = 0):
        """`initial_deposit`: the amount of gold you want to deposit, if you want to

        Open a bank account within your guild and store an amount of money in it.
        """
        #Check for invalid input
        if initial_deposit < 0:
            return await ctx.reply('The bank cannot complete this deposit.')

        player_gold = await AssetCreation.getGold(self.client.pg_con, ctx.author.id)
        if player_gold < initial_deposit:
            return await ctx.reply('You cannot deposit more money than you own!')

        guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        if initial_deposit > math.floor(guild['XP'] / 1000000) * 1000000:
            return await ctx.reply(f"The most you can store in your guild bank account is `{math.floor(guild['XP'] / 1000000) * 1000000}` gold.")

        #Open the account
        await AssetCreation.open_guild_account(self.client.pg_con, ctx.author.id, initial_deposit)
        return await ctx.reply(f"You opened a bank account with your guild. Do `{ctx.prefix}guild account` to view it!")

    @account.command(aliases=['d','save'], brief='<deposit>', description='Deposit some of your money into your guild bank account.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_guild)
    @commands.check(Checks.has_bank_account)
    async def deposit(self, ctx, deposit : int):
        """`deposit`: the amount of gold you are depositing

        Store some gold into your bank account.
        """
        #Check for invalid input
        if deposit < 0:
            return await ctx.reply(f'Please use `{ctx.prefix}guild account withdraw` instead.')

        player_gold = await AssetCreation.getGold(self.client.pg_con, ctx.author.id)
        if player_gold < deposit:
            return await ctx.reply('You cannot deposit more money than you own!')

        bank_info = await AssetCreation.get_guild_account(self.client.pg_con, ctx.author.id)
        if deposit > bank_info['capacity'] - bank_info['account_funds']:
            return await ctx.reply(f"This transaction will overfill your account. Please deposit `{bank_info['capacity'] - bank_info['account_funds']}` gold at most.")

        #Deposit money and give receipt
        await AssetCreation.giveGold(self.client.pg_con, deposit*-1, ctx.author.id)
        await AssetCreation.guild_bank_deposit(self.client.pg_con, ctx.author.id, deposit)

        await ctx.reply(f"You deposited `{deposit}` gold into your guild bank account.\nYou have `{player_gold - deposit}` gold and `{bank_info['account_funds'] + deposit}` gold in your account.")

    @account.command(aliases=['w','pay'], brief='<deposit>', description='Deposit some of your money into your guild bank account.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_guild)
    @commands.check(Checks.has_bank_account)
    async def withdraw(self, ctx, withdrawal : int):
        """`withdrawl`: the amount of gold you want to take out of your account

        Withdraw some of the money from your guild bank account.
        """
        #Check for invalid input
        if withdrawal < 0:
            return await ctx.reply(f"Please use `{ctx.prefix}guild account deposit` instead.")

        bank_info = await AssetCreation.get_guild_account(self.client.pg_con, ctx.author.id)
        if withdrawal > bank_info['account_funds']:
            return await ctx.reply(f"You cannot withdraw that amount as you only have `{bank_info['account_funds']}` saved.")

        #Withdraw money and give receipt
        await AssetCreation.giveGold(self.client.pg_con, withdrawal, ctx.author.id)
        await AssetCreation.guild_bank_deposit(self.client.pg_con, ctx.author.id, withdrawal*-1)
        player_gold = await AssetCreation.getGold(self.client.pg_con, ctx.author.id)

        await ctx.reply(f"You withdrew `{withdrawal}` gold from your guild bank account.\nYou have `{player_gold}` gold and `{bank_info['account_funds'] - withdrawal}` gold in your account.")

    @guild.command(brief='<area>', description='Select an area to base your association in. The valid locations are:\n`Aramithea`, `Riverburn`, `Thenuille`')
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_guild_leader)
    async def base(self, ctx, *, area : str):
        """`area`: One of these locations: `Aramithea`, `Riverburn`, `Thenuille`
        
        [LEADER] Designate an area of the map as your guild's headquarters.
        """
        #Make sure input is valid.
        area = area.title()
        areas = ('Aramithea', 'Riverburn', 'Thenuille')
        if area not in areas:
            return await ctx.reply('Please select a valid area on the map:\n`Aramithea`, `Riverburn`, `Thenuille`')

        #Load guild info
        guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)

        #Check to see if this is first change and apply charge if necessary
        base_info = await AssetCreation.get_association_base(self.client.pg_con, guild['ID'])
        if base_info['base_set']:
            player_gold = await AssetCreation.getGold(self.client.pg_con, ctx.author.id)
            if player_gold < 1000000:
                return await ctx.reply(f'Changing your association\'s base costs `1,000,000` gold but you only have `{player_gold}` gold.')

            message = await ctx.reply('This operation will cost `1,000,000` gold. Continue?')
            await message.add_reaction('\u2705') #Check
            await message.add_reaction('\u274E') #X

            def check(reaction, user):
                return user == ctx.author and reaction.message.id == message.id

            reaction = None
            readReactions = True
            while readReactions: 
                if str(reaction) == '\u2705': #Then change base
                    await message.delete()
                    await AssetCreation.giveGold(self.client.pg_con, -1000000, ctx.author.id)
                    await AssetCreation.set_association_base(self.client.pg_con, guild['ID'], area)
                    await ctx.reply(f"{guild['Name']} is now based in {area}!")
                    break
                if str(reaction) == '\u274E':
                    await message.delete()
                    await ctx.reply('Cancelled base movement.')
                    break

                try:
                    reaction, user = await self.client.wait_for('reaction_add', check=check, timeout=15.0)
                    await message.remove_reaction(reaction, user)
                except asyncio.TimeoutError:
                    readReactions = not readReactions
                    await message.delete()
                    await ctx.send('Cancelled base movement.')

        else: #Change base for free
            await AssetCreation.set_association_base(self.client.pg_con, guild['ID'], area)
            await ctx.reply(f"{guild['Name']} is now based in {area}!\n`WARNING:` Changing your base again will cost `1,000,000` gold.")

    @guild.command(brief='<guild ID>', description='See info on another guild based on their ID')
    async def info(self, ctx, *, source : str):
        """`source`: the association you want to view. If you know its ID, you can do `bh info id:<ID>`. If you want to search by name, simply do `guild info <name>`
        
        View another association. Will also show brotherhoods and colleges if requested.
        """
        if source.lower().startswith("id:"):
            try:
                info = await AssetCreation.getGuildByID(self.client.pg_con, int(source[3:]))
                if info is None:
                    return await ctx.reply('There is no association with that ID.')
            except (ValueError, TypeError):
                return await ctx.reply('That is an invalid ID number.')
        else:
            try:
                info = await AssetCreation.getGuildByName(self.client.pg_con, source)
            except TypeError:
                return await ctx.reply('No association goes by that name.')

        leader = await self.client.fetch_user(info['Leader'])
        level, progress = await AssetCreation.getGuildLevel(self.client.pg_con, 
                                                            info['ID'], 
                                                            returnline=True)
        members = await AssetCreation.getGuildMemberCount(self.client.pg_con, 
                                                          info['ID'])
        capacity = await AssetCreation.getGuildCapacity(self.client.pg_con, info['ID'])

        embed = discord.Embed(title=f"{info['Name']}", color=self.client.ayesha_blue)
        embed.set_thumbnail(url=f"{info['Icon']}")
        embed.add_field(name='Leader', value=f"{leader.mention}")
        embed.add_field(name='Members', value=f"{members}/{capacity}")
        embed.add_field(name='Level', value=f"{level}")
        embed.add_field(name='EXP Progress', value=f'{progress}')
        embed.add_field(name='Base', value=f"{info['Base']}")
        embed.add_field(name=f"This {info['Type']} is {info['Join']} to new members.", 
                        value=f"{info['Desc']}",
                        inline=False)
        embed.set_footer(text=f"{info['Type']} ID: {info['ID']}")
        await ctx.reply(embed=embed)

    @guild.command(aliases=['desc'], brief='<desc>', description='Change your brotherhood\'s description. [GUILD OFFICER+ ONLY]')
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_guild_officer)
    async def description(self, ctx, *, desc : str):
        """`desc`: The description you want to be displayed.

        [OFFICER+] Change your guild's description.
        """
        if len(desc) > 256:
            await ctx.reply(f'Description max 256 characters. You gave {len(desc)}')
            return
        # Get guild and change description
        guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        await AssetCreation.setGuildDescription(self.client.pg_con, desc, guild['ID'])
        await ctx.reply('Description updated!')

    @guild.command(brief='<img url>', description='Set the icon for your guild.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_guild_officer)
    async def icon(self, ctx, *, url : str):
        """`url`: a valid image URL
        
        [OFFICER+] Change your guild's icon.
        """
        if len(url) > 256:
            await ctx.reply('Icon URL max 256 characters. Please upload your image to imgur or tinurl for an appropriate link.')
            return

        #Make sure the URL is valid
        file_types = ('image/jpeg', 'image/png', 'image/webp', 'image/gif')
        try:
            async with aiohttp.ClientSession() as client:
                resp = await client.get(url)
                img = resp.headers.get('content-type')
                if img in file_types:
                    pass
                else:
                    await ctx.reply('This is an invalid URL.')

        except aiohttp.InvalidURL:
            await ctx.reply('This is an invalid URL.')
            return
        
        #Get guild and change icon
        guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        await AssetCreation.setGuildIcon(self.client.pg_con, url, guild['ID'])
        await ctx.reply('Icon updated!')

    @guild.command(description='Lock/unlock your guild from letting anyone join without an invite.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_guild_leader)
    async def lock(self, ctx):
        """[LEADER] Lock/unlock your guild. If locked, people may only join by invite from the leader or officer."""
        guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        if guild['Join'] == 'open':
            await AssetCreation.lockGuild(self.client.pg_con, guild['ID'])
            await ctx.reply('Your guild is now closed to new members. Players can only join your guild via invite.')
        else:
            await AssetCreation.unlockGuild(self.client.pg_con, guild['ID'])
            await ctx.reply('Your guild is now open to members. Anyone may join with the `join` command!')

    @guild.command(brief='<guild id : int>', description='Join the target guild if its open!')
    @commands.check(Checks.is_player)
    @commands.check(Checks.not_in_guild)
    async def join(self, ctx, guild_id : int):
        """`guild_id`: the ID of the guild you want to join

        Join any guild that is listed as open. You must use their ID, which can be found on the bottom of its page from `bh info`
        """
        #See how recently they joined an association
        last_join = await AssetCreation.check_last_guild_join(self.client.pg_con, ctx.author.id)
        if last_join.total_seconds() < 86400:
            cd = 86400 - last_join.total_seconds()
            return await ctx.reply(f'Joining associations has a 24 hour cooldown. You can join another association in `{time.strftime("%H:%M:%S", time.gmtime(cd))}`.')

        #Make sure that guild exists, is open, and has an open slot
        try:
            guild = await AssetCreation.getGuildByID(self.client.pg_con, guild_id)
        except TypeError:
            await ctx.reply('That guild does not exist.')
            return

        if guild['Join'] != 'open':
            await ctx.reply('This guild is not accepting new members at this time.')
            return
        if not await Checks.target_guild_has_vacancy(self.client.pg_con, guild_id):
            await ctx.reply('This guild has no open spaces at the moment.')
            return

        #Otherwise they join the guild
        await AssetCreation.joinGuild(self.client.pg_con, guild_id, ctx.author.id)
        await ctx.reply(f"Welcome to {guild['Name']}! Use `brotherhood` or `guild` to see your new association.")

    @guild.command(brief='<player> <Officer/Adept>', description='Promote a member of your guild. Officers have limited administrative powers. Adepts have no powers. [LEADER ONLY]')
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_guild_leader)        
    async def promote(self, ctx, player : commands.MemberConverter = None, rank : str = None):
        """`player`: the player you want to promote
        `rank`: `Officer` or `Adept`

        [LEADER] Promote a member of your guild. Officers have limited administrative powers. Adepts have no powers.
        """
        #Tell players what officers and adepts do if no input is given
        if player is None or rank is None:
            embed = discord.Embed(title='Brotherhood Role Menu', color=self.client.ayesha_blue)
            embed.add_field(name='Guild leaders can promote their members to two other roles: Officer and Adept',
                value='**Officers** share in the administration of the association. They can invite and kick members, and change the guild\'s description.\n**Adepts** are a mark of seniority for members. They have no powers, but are stronger and more loyal than other members.')
            await ctx.reply(embed=embed, delete_after=30.0)
            return
        #Ensure the rank input is valid
        if rank != "Officer" and rank != "Adept":
            await ctx.reply('That is not a valid rank. Please input `Officer` or `Adept`.')
            return
        #Otherwise check if player is in guild -> also not the leader
        if ctx.author == player:
            await ctx.reply('I don\'t think so.')
            return
        if not await Checks.has_char(self.client.pg_con, player):
            await ctx.reply('This person does not have a character.')
            return
        if await Checks.target_not_in_guild(self.client.pg_con, player):
            await ctx.reply('This person is not in your brotherhood.')
            return
        leader_guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        target_guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, player.id)
        if leader_guild['ID'] != target_guild['ID']:
            await ctx.reply('This person is not in your brotherhood.')
            return
        #Then give them their role
        await AssetCreation.changeGuildRank(self.client.pg_con, rank, player.id)
        await ctx.reply(f'`{player.name}` is now an `{rank}`.')

    @guild.command(brief='<player>', description='Demote a member of your guild back to member.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_guild_leader)
    async def demote(self, ctx, player : commands.MemberConverter):
        """`player`: the player you are demoting
        
        [LEADER] Demote one of your officers or adepts back to regular member.
        """
        #Otherwise check if player is in guild -> also not the leader
        if ctx.author == player:
            await ctx.reply('I don\'t think so.')
            return
        if not await Checks.has_char(self.client.pg_con, player):
            await ctx.reply('This person does not have a character.')
            return
        if await Checks.target_not_in_guild(self.client.pg_con, player):
            await ctx.reply('This person is not in your brotherhood.')
            return
        leader_guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        target_guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, player.id)
        if leader_guild['ID'] != target_guild['ID']:
            await ctx.reply('This person is not in your brotherhood.')
            return
        #Then give them their role
        await AssetCreation.changeGuildRank(self.client.pg_con, "Member", player.id)
        await ctx.reply(f'`{player.name}` has been demoted to `Member`.')

    @guild.command(brief='<player>', description='Transfer guild ownership to another member.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_guild_leader)
    async def transfer(self, ctx, player : commands.MemberConverter):
        """`player`: the player you want to become new head of the guild
        
        [LEADER] Relinquish control of your brotherhood to someone else.
        """
        if ctx.author.id == player.id:
            await ctx.reply('?')
            return

        # Make sure target has a char, is in the same guild
        if not await Checks.has_char(self.client.pg_con, player):
            await ctx.reply('This person does not have a character.')
            return
        if await Checks.target_not_in_guild(self.client.pg_con, player):
            await ctx.reply('This person is not in your association.')
            return
        leader_guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        target_guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, player.id)
        if leader_guild['ID'] != target_guild['ID']:
            await ctx.reply('This person is not in your association.')
            return
        # Otherwise make them leader - make sure to update leader field in guilds table and remove former leader
        await AssetCreation.changeGuildRank(self.client.pg_con, "Leader", player.id)
        await AssetCreation.changeGuildRank(self.client.pg_con, "Officer", ctx.author.id)
        await ctx.reply(f"`{player.name}` has been demoted to `Leader` of `{leader_guild['Name']}`. You are now an `Officer`.")

    @guild.command(brief='<player>', description='Kick someone from your association.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_guild_officer)
    async def kick(self, ctx, player : commands.MemberConverter):
        """`player`: the person you are removing from the guild

        Kick someone from your guild, revoking their membership.
        """
        #Make sure target has a char, in same guild, isn't an officer or leader
        if not await Checks.has_char(self.client.pg_con, player):
            await ctx.reply('This person does not have a character.')
            return
        if await Checks.target_not_in_guild(self.client.pg_con, player):
            await ctx.reply('This person is not in your association.')
            return
        leader_guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        target_guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, player.id)
        if leader_guild['ID'] != target_guild['ID']:
            await ctx.reply('This person is not in your association.')
            return
        if await Checks.target_is_guild_officer(self.client.pg_con, player.id):
            await ctx.reply('You cannot kick your officer or leader.')
            return

        #Otherwise remove the targeted person from the association
        await AssetCreation.leaveGuild(self.client.pg_con, player.id)
        await ctx.reply(f'You kicked {player.display_name} from your association.')

    @guild.command(aliases=['disband'], description='Disband your association. You can only do this when no one else remains in your association.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_guild)
    @commands.check(Checks.is_guild_leader)
    async def delete(self, ctx):
        """[LEADER] Disband your brotherhood. You can only do this when no one else remains in your association."""
        #Make sure they're the only member remaining
        guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        if await AssetCreation.getGuildMemberCount(self.client.pg_con, guild['ID']) > 1:
            return await ctx.reply('Your association still has members counting on you! You can\'t disband.')

        #Ask for confirmation
        message = await ctx.reply('Are you sure you want to disband your association?')
        await message.add_reaction('\u2705') #Check
        await message.add_reaction('\u274E') #X

        def check(reaction, user):
            return user == ctx.author and reaction.message.id == message.id

        reaction = None
        readReactions = True
        while readReactions: 
            if str(reaction) == '\u2705': #Then proceed
                await message.delete()
                await AssetCreation.deleteGuild(self.client.pg_con, guild['ID'], guild['Leader'], guild['Type'])
                await ctx.reply(f"You have disbanded {guild['Name']}.")
                break
            if str(reaction) == '\u274E': #Cancel the guild disband
                await message.delete()
                await ctx.reply('Cancelled the operation.')
                break

            try:
                reaction, user = await self.client.wait_for('reaction_add', check=check, timeout=15.0)
                await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                readReactions = not readReactions
                await message.delete()
                await ctx.send('Cancelled the operation.')

    @guild.command(description='Shows this command.')
    async def help(self, ctx):
        """Get a list of all commands that guild members can use."""
        def write(ctx, start, entries):
            helpEmbed = discord.Embed(title=f'Ayesha Help: Guilds', description='Guilds are a financially-oriented association. Its members gain more money from selling items. They also gain access to the `invest` command.', color=self.client.ayesha_blue)
            helpEmbed.set_thumbnail(url=ctx.author.avatar_url)
            
            iteration = 0
            while start < len(entries) and iteration < 5: #Will loop until 5 entries are processed or there's nothing left in the queue
                if entries[start].parent.name == 'account': #Account subcommand needs to list 'account' parent as well
                    entries[start].name = f'account {entries[start].name}'
                
                if entries[start].brief and entries[start].aliases:
                    helpEmbed.add_field(name=f'{entries[start].name} `{entries[start].brief}`', 
                                        value=f'Aliases: `{entries[start].aliases}`\n{entries[start].description}', 
                                        inline=False)
                elif entries[start].brief and not entries[start].aliases:
                    helpEmbed.add_field(name=f'{entries[start].name} `{entries[start].brief}`', 
                                        value=f'{entries[start].description}', 
                                        inline=False)
                elif not entries[start].brief and entries[start].aliases:
                    helpEmbed.add_field(name=f'{entries[start].name}', 
                                        value=f'Aliases: `{entries[start].aliases}`\n{entries[start].description}', 
                                        inline=False)
                else:
                    helpEmbed.add_field(name=f'{entries[start].name}', 
                                        value=f'{entries[start].description}', 
                                        inline=False)
                iteration += 1
                start +=1 
                
            return helpEmbed

        cmds, embeds = [], []
        for command in self.client.get_command('guild').walk_commands():
            cmds.append(command)
        for i in range(0, len(cmds), 5):
            embeds.append(write(ctx, i, cmds))

        helper = menus.MenuPages(source=PageSourceMaker.PageMaker(embeds), 
                                 clear_reactions_after=True, 
                                 delete_message_after=True)
        await helper.start(ctx)

def setup(client):
    client.add_cog(Guilds(client))