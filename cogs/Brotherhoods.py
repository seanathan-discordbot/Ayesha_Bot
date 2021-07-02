import discord
import asyncio

from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

from Utilities import Checks, AssetCreation, PageSourceMaker
from Utilities.PageSourceMaker import PageMaker

import random
import aiohttp
import time
from datetime import datetime

# There will be brotherhoods, guilds, and later colleges for combat, economic, and political gain

class Brotherhoods(commands.Cog):
    """Association Type for Combat"""

    def __init__(self, client):
        self.client = client

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('Brotherhoods is ready.')

    #COMMANDS
    @commands.group(aliases=['bh'], 
                    invoke_without_command=True, 
                    case_insensitive=True, 
                    description=f'See your brotherhood.\nDo `brotherhood help` for more brotherhood commands.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_brotherhood)
    async def brotherhood(self, ctx):
        """View your brotherhood. Brotherhoods are a pvp-oriented association. Its members gain an ATK and CRIT bonus depending on its level. They also gain access to the `steal` command.
        `brotherhood help` will show all other commands related to this association type.
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
        embed.set_footer(text=f"Brotherhood ID: {info['ID']}")
        await ctx.reply(embed=embed)

    @brotherhood.command(aliases=['found', 'establish', 'form', 'make'], 
                         brief='<name>', 
                         description='Found a brotherhood. Costs 15,000 gold.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.not_in_guild)
    async def create(self, ctx, *, name : str):
        """`name`: the name of your brotherhood

        Found a brotherhood. This operation costs 15,000 gold.
        """
        if len(name) > 32:
            return await ctx.reply('Name max 32 characters')
        # Make sure they have the money and an open name
        if not await Checks.guild_can_be_created(ctx, name):
            return
        # Otherwise create the guild
        await AssetCreation.createGuild(self.client.pg_con, 
                                        name, 
                                        "Brotherhood", 
                                        ctx.author.id, 
                                        'https://cdn4.iconfinder.com/data/icons/ionicons/512/icon-ios7-contact-512.png')
        await ctx.reply('Brotherhood founded. Do `brotherhood` to see it or `brotherhood help` for more commands!')

    @brotherhood.command(aliases=['inv'], 
                         brief='<url>', 
                         description='Invite a player to your guild.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_guild_officer)
    @commands.check(Checks.guild_has_vacancy)
    async def invite(self, ctx, player : commands.MemberConverter):
        """`player`: the player you want to invite

        [OFFICER+] Invite a player to your brotherhood, provided that there is space available. 
        """
        #Ensure target player has a character and is not in a guild
        if not await Checks.has_char(self.client.pg_con, player):
            return await ctx.reply('This person does not have a character.')
        if not await Checks.target_not_in_guild(self.client.pg_con, player):
            return await ctx.reply('This player is already in an association.')

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

    @brotherhood.command(description='Leave your brotherhood.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_brotherhood)
    @commands.check(Checks.is_not_guild_leader)
    async def leave(self, ctx):
        """Leave your brotherhood."""
        await AssetCreation.leaveGuild(self.client.pg_con, ctx.author.id)
        await ctx.reply('You left your brotherhood.')

    @brotherhood.command(aliases=['donate'], 
                         brief='<money : int>', 
                         description='Donate to your association, increasing its xp!')
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_brotherhood)
    async def contribute(self, ctx, donation : int):
        """`donation`: the amount of money you want to give your brotherhood

        Contribute money to the strength of your brotherhood. Every 1,000,000 gold contributed will level it up, strengthening its bonuses, up to level 10.
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
        await ctx.reply(f'You contributed `{donation}` gold to your brotherhood. It will become level `{int(xp/1000000)+1}` at `{needed}` more xp.')

    @brotherhood.command(description='View the other members of your guild.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_brotherhood)
    async def members(self, ctx):
        """See a list of all your brotherhood's members, their rank, and some stats."""
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

        member_list = PageSourceMaker.PageMaker.number_pages(member_list)
        member_pages = menus.MenuPages(source=PageSourceMaker.PageMaker(member_list), 
                                       clear_reactions_after=True, 
                                       delete_message_after=True)
        await member_pages.start(ctx)

    @brotherhood.command(description='Steal 5% of a random player\'s cash. The probability of stealing is about your brotherhood\'s level * .05 + .2. 30 minute cooldown.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_brotherhood)
    @cooldown(1, 1800, BucketType.user)
    async def steal(self, ctx):
        """Steal up to 5% of a random player's gold. The probability of stealing is about your brotherhood's level * 5% + 20%."""
        guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        level = await AssetCreation.getGuildLevel(self.client.pg_con, guild['ID'])
        if random.randint(0,100) >= 20 + level*5: #Then failure
            return await ctx.reply('You were caught and had to flee.')

        # Otherwise get a random player and steal 5% of their money
        records = await AssetCreation.getPlayerCount(self.client.pg_con, )
        victim_num = random.randint(1, records - 1)

        try: #there might be deleted chars - just give them 100 gold lmao
            victim_gold, victim, victim_name = await AssetCreation.getPlayerByNum(self.client.pg_con, victim_num)
        except TypeError:
            await AssetCreation.giveGold(self.client.pg_con, 100, ctx.author.id)
            return await ctx.reply('You stole `100` gold from a random guy.')

        # Make sure they don't rob themself
        if ctx.author.id == victim:
            return await ctx.reply('You were caught and had to flee.')

        # 50 gold minimum steal. If they don't have 1000, just add 50 to the econ.
        if victim_gold < 1000:
            await AssetCreation.giveGold(self.client.pg_con, 50, ctx.author.id)
            stolen_amount = 50
        else:
            stolen_amount = int(victim_gold / 20)
            role = await AssetCreation.getClass(self.client.pg_con, ctx.author.id)
            if role == 'Engineer':
                stolen_amount = int(victim_gold / 10)
            await AssetCreation.giveGold(self.client.pg_con, stolen_amount, ctx.author.id)
            await AssetCreation.giveGold(self.client.pg_con, 0 - stolen_amount, victim)
        
        await ctx.reply(f'You stole `{stolen_amount}` gold from `{victim_name}`.')

    @brotherhood.command(brief='<area>', description='Select an area to base your association in. The valid locations are:\n`Mythic Forest`, `Fernheim`, `Sunset Prairie`, `Thanderlans`, `Glakelys`, `Russe`, `Croire`, `Crumidia`, `Kucre`')
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_brotherhood)
    @commands.check(Checks.is_guild_leader)
    async def base(self, ctx, *, area : str):
        """`area`: One of these locations: `Mythic Forest`, `Fernheim`, `Sunset Prairie`, `Thanderlans`, `Glakelys`, `Russe`, `Croire`, `Crumidia`, `Kucre`
        
        [LEADER] Designate an area of the map as your brotherhood's headquarters. You may contest this territory with rival brotherhoods with `bh attack`.
        """
        #Make sure input is valid.
        area = area.title()
        areas = ('Mythic Forest', 'Fernheim', 'Sunset Prairie', 'Thanderlans', 'Glakelys', 'Russe', 'Croire', 'Crumidia', 'Kucre')
        if area not in areas:
            return await ctx.reply('Please select a valid area on the map:\n`Mythic Forest`, `Fernheim`, `Sunset Prairie`, `Thanderlans`, `Glakelys`, `Russe`, `Croire`, `Crumidia`, `Kucre`')

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
                if str(reaction) == '\u2705': #Then change base; also relinquish territory control if applicable
                    await message.delete()
                    await AssetCreation.giveGold(self.client.pg_con, -1000000, ctx.author.id)
                    
                    #Relinquish territory control if applicable
                    if guild['ID'] == await AssetCreation.get_area_controller(self.client.pg_con, guild['Base']):
                        await AssetCreation.set_area_controller(self.client.pg_con, guild['Base'])

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

    @brotherhood.command(aliases=['guildinfo', 'bhinfo'], brief='<guild ID>', 
                         description='See info on another guild based on their ID')
    async def info(self, ctx, *, source : str):
        """`source`: the association you want to view. If you know its ID, you can do `bh info id:<ID>`. If you want to search by name, simply do `bh info <name>`
        
        View another association. Will also show guilds and colleges if requested.
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

    @brotherhood.command(aliases=['desc'], 
                         brief='<desc>', 
                         description='Change your brotherhood\'s description. [GUILD OFFICER+ ONLY]')
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_guild_officer)
    async def description(self, ctx, *, desc : str):
        """`desc`: The description you want to be displayed.

        [OFFICER+] Change your brotherhood's description.
        """
        if len(desc) > 256:
            return await ctx.reply(f'Description max 256 characters. You gave {len(desc)}')
        # Get guild and change description
        guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        await AssetCreation.setGuildDescription(self.client.pg_con, desc, guild['ID'])
        await ctx.reply('Description updated!')

    @brotherhood.command(brief='<img url>', 
                         description='Set the icon for your brotherhood.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_guild_officer)
    async def icon(self, ctx, *, url : str):
        """`url`: a valid image URL
        
        [OFFICER+] Change your brotherhood's icon.
        """
        if len(url) > 256:
            return await ctx.reply('Icon URL max 256 characters. Please upload your image to imgur or tinurl for an appropriate link.')

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

    @brotherhood.command(description='Lock/unlock your guild from letting anyone join without an invite.')
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

    @brotherhood.command(brief='<guild id : int>', description='Join the target guild if its open!')
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

    @brotherhood.command(brief='<player> <Officer/Adept>', 
                         description='Promote a member of your guild. Officers have limited administrative powers. Adepts have no powers. [LEADER ONLY]')
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

    @brotherhood.command(brief='<player>', description='Demote a member of your guild back to member.')
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

    @brotherhood.command(brief='<player>', description='Transfer guild ownership to another member.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_guild_leader)
    async def transfer(self, ctx, player : commands.MemberConverter):
        """`player`: the player you want to become new head of the brotherhood
        
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

    @brotherhood.command(brief='<player>', description='Kick someone from your association.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_guild_officer)
    async def kick(self, ctx, player : commands.MemberConverter):
        """`player`: the person you are removing from the brotherhood

        Kick someone from your brotherhood, revoking their membership.
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

    @brotherhood.command(aliases=['champs', 'c'],
                         description='View your brotherhood\'s champions!')
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_brotherhood)
    async def champions(self, ctx):
        """View your brotherhood's champions. 
        Your brotherhood can have up to 3 champions. These strong players battle for territory control with `bh attack`.
        """
        guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        champions = await AssetCreation.get_brotherhood_champions(self.client.pg_con, guild['ID'])

        for i in range(0,3):
            if champions[i] is not None:
                name = await AssetCreation.getPlayerName(self.client.pg_con, champions[i])
                # attack, crit = await AssetCreation.getAttack(self.client.pg_con, champions[i])
                battle_stats = await AssetCreation.get_attack_crit_hp(self.client.pg_con, champions[i])
                
                champions[i] = {
                    'Name' : name,
                    'ATK' : battle_stats['Attack'],
                    'Crit' : battle_stats['Crit']
                }

        embed = discord.Embed(title=f"{guild['Name']}'s Champions",
                              color=self.client.ayesha_blue)
        for i, champion in enumerate(champions):
            try:
                embed.add_field(name=f'Champion {i+1}',
                                value=f"Name: {champion['Name']}\nATK: {champion['ATK']}\nCrit: {champion['Crit']}")
            except TypeError:
                embed.add_field(name=f'Champion {i+1}',
                                value='None')

            embed.set_footer(text="If a champion is 'None', ask your officer to add one with the 'champion' command!")

        await ctx.reply(embed=embed)

    @brotherhood.command(brief = '<champion> <slot : 1-3>',
                         description='Elevate one of your brotherhood members to the role of champion. Champions fight for and defend the area you control or want to take over. [OFFICER+ ONLY]')
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_brotherhood)
    @commands.check(Checks.is_guild_officer)
    async def champion(self, ctx, player : commands.MemberConverter, slot : int):
        """`player`: the player you are declaring champion
        `slot`: 1-3, the slot in battle they are occupying
        
        [OFFICER+] Assign someone to be a champion of your brotherhood
        Your brotherhood can have up to 3 champions. These strong players battle for territory control with `bh attack`.
        """
        #Make sure this person has a char, is in the guild, and isn't already a champion
        if slot < 1 or slot > 3:
            return await ctx.reply('Please insert your champion into slots 1, 2, or 3.')

        if not await Checks.has_char(self.client.pg_con, player):
            return await ctx.reply('This person does not have a character.')
        if await Checks.target_not_in_guild(self.client.pg_con, player):
            return await ctx.reply('This person is not in your association.')

        leader_guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        target_guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, player.id)
        if leader_guild['ID'] != target_guild['ID']:
            return await ctx.reply('This person is not in your association.')
        
        if player.id in await AssetCreation.get_brotherhood_champions(self.client.pg_con, leader_guild['ID']):
            #Technically since this is here I don't have to do an UPSERT for existing brotherhoods
            return await ctx.reply('This person is already one of your brotherhood\'s champions.')

        #Otherwise update their champions to include them
        await AssetCreation.update_brotherhood_champion(self.client.pg_con, leader_guild['ID'], player.id, slot)
        await ctx.reply(f'`{player.display_name}` is now one of your champions. Do `{ctx.prefix}bh champions` to view your brotherhood\'s champions.')

    @brotherhood.command(brief='<slot 1-3>', description='Unassign a champion from a specific slot. [OFFICER+ ONLY]')
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_brotherhood)
    @commands.check(Checks.is_guild_officer)
    async def unchampion(self, ctx, slot : int):
        """`slot`: the slot that you want to empty

        [OFFICER+] Remove someone as champion
        """
        if slot < 1 or slot > 3:
            return await ctx.reply('Slots are limited to 1, 2, and 3.')
        
        guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        await AssetCreation.remove_brotherhood_champion(self.client.pg_con, guild['ID'], slot)

        await ctx.reply(f'Removed the champion in slot {slot}. Use `{ctx.prefix}bh champion` to add another!')

    @brotherhood.command(description='Attempt to seize control over the area your brotherhood is located in. A small tournament will begin between the champions of your brotherhood and the current rulers. The winner will take control over the area.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_brotherhood)
    @commands.check(Checks.is_guild_officer)
    async def attack(self, ctx):
        """[OFFICER+] Challenge the current owner's of your brotherhood's territory to a battle.
        Your brotherhood's champions (`bh champions`) will fight the champions of the incumbent brotherhood. The victor will become the new controller of the region.
        The controller of a territory will give its members bonuses from `mine`, `forage`, and `hunt`. Only one attack per territory is allowed every few hours.
        """
        def simulate_battle(player1, player2):
            """Simulate a battle between two players based solely off ATK and Crit.
            Each side has a small chance to land a "crit" (based off crit) and win.
            Otherwise it will base the victor off the proportions of the attack.
            Return the winner and loser in that order."""
            #See if one side lands a critical hit - Highest crit possible is theoretically ~70%.
            p1vict = player1['Crit']
            p2vict = p1vict + player2['Crit'] #This should theoretically be <=140
            random_crit = random.randint(0,500)
            if random_crit < p1vict:
                return player1, player2 #player1 wins; Winner is returned first
            elif random_crit < p2vict:
                return player2, player1
            
            #If no victory occurs, then base it off proportion of ATK
            victory_number = random.randint(0, player1['ATK'] + player2['ATK'])
            if victory_number < player1['ATK']:
                return player1, player2
            else:
                return player2, player1

        #Only one attack per area every 3 hours. Check to see if attacking is available
        guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        last_attack = await AssetCreation.get_most_recent_area_attack(self.client.pg_con, guild['Base'])

        if last_attack is not None:
            if (datetime.now() - last_attack).total_seconds() < 10800:
                return await ctx.reply(f'This area has already suffered a recent attack. Please try again in `{time.strftime("%H:%M:%S", time.gmtime(10800 - (datetime.now() - last_attack).total_seconds()))}`.')

        #If available, load the champions for both brotherhoods
        #If <3 champions, recycle the first with nerfed stats
        #If defender has no champions, attacker automatically wins
        attacker = await AssetCreation.get_brotherhood_champions(self.client.pg_con, guild['ID'])
        defending_guild_id = await AssetCreation.get_area_controller(self.client.pg_con, guild['Base'])

        if defending_guild_id is None: #No one currently holds the area, so attacker assumes control
            await AssetCreation.set_area_controller(self.client.pg_con, guild['Base'], guild['ID'])
            await self.client.announcement_channel.send(f"**{guild['Name']} (ID: `{guild['ID']}`)** has seized control over {guild['Base']}.")
            return await ctx.reply(f"{guild['Name']} has seized control over {guild['Base']}.")

        defending_guild = await AssetCreation.getGuildByID(self.client.pg_con, defending_guild_id)

        if defending_guild['Base'] != guild['Base']: #then the defending guild has since moved. Give freely
            await AssetCreation.set_area_controller(self.client.pg_con, guild['Base'], guild['ID'])
            await self.client.announcement_channel.send(f"**{guild['Name']} (ID: `{guild['ID']}`)** has seized control over {guild['Base']}.")
            return await ctx.reply(f"{guild['Name']} has seized control over {guild['Base']}.")

        if guild['ID'] == defending_guild_id:
            return await ctx.reply(f"Your brotherhood is already in control of {guild['Base']}")

        defender = await AssetCreation.get_brotherhood_champions(self.client.pg_con, defending_guild_id)

        if attacker[0] is None and attacker[1] is None and attacker[2] is None:
            return await ctx.reply(f'Your brotherhood has no champions. Set some with `{ctx.prefix}bh champion`!')
        
        if defender[0] is None and defender[1] is None and defender[2] is None: #If defender has no champs, give it up
            await AssetCreation.set_area_controller(self.client.pg_con, guild['Base'], guild['ID'])
            await self.client.announcement_channel.send(f"**{guild['Name']} (ID: `{guild['ID']}`)** has seized control over {guild['Base']}.")
            return await ctx.reply(f"{guild['Name']} has seized control over {guild['Base']}.")

        for i in range(0,3): #Replace their IDs with a dict containing battle info
            if attacker[i] is not None:
                name = await AssetCreation.getPlayerName(self.client.pg_con, attacker[i])
                # attack, crit = await AssetCreation.getAttack(self.client.pg_con, attacker[i])
                battle_stats = await AssetCreation.get_attack_crit_hp(self.client.pg_con, attacker[i])
                
                attacker[i] = {
                    'ID' : attacker[i],
                    'Name' : name,
                    'ATK' : battle_stats['Attack'],
                    'Crit' : battle_stats['Crit']
                }
            if defender[i] is not None:
                name = await AssetCreation.getPlayerName(self.client.pg_con, defender[i])
                # attack, crit = await AssetCreation.getAttack(self.client.pg_con, defender[i])
                battle_stats = await AssetCreation.get_attack_crit_hp(self.client.pg_con, defender[i])
                
                defender[i] = {
                    'ID' : defender[i],
                    'Name' : name,
                    'ATK' : battle_stats['Attack'],
                    'Crit' : battle_stats['Crit']
                }

        for i in range(1,3): #Sort the teams so that the first slot is always a person (and not empty)
            if attacker[0] is None and attacker[i] is not None:
                attacker[0] = attacker[i]
            if defender[0] is None and defender[i] is not None:
                defender[0] = defender[i]

        for i in range(1,3): #Now fill "None"s with the first champion. The above operation made sure the first is always a person
            if attacker[i] is None:
                attacker[i] = attacker[0]
            if defender[i] is None:
                defender[i] = defender[0]

        #Now check for repeats, nerfing stats for the second or third appearance. This can probably be optimized.
        if attacker[0]['ID'] == attacker[1]['ID']:
            attacker[1]['ATK'] = int(attacker[1]['ATK'] * .9)
            attacker[1]['Crit'] = int(attacker[1]['Crit'] * .9)

        if attacker[0]['ID'] == attacker[2]['ID']:
            attacker[2]['ATK'] = int(attacker[2]['ATK'] * .9)
            attacker[2]['Crit'] = int(attacker[2]['Crit'] * .9)

        if attacker[1]['ID'] == attacker[2]['ID']:
            attacker[2]['ATK'] = int(attacker[2]['ATK'] * .9)
            attacker[2]['Crit'] = int(attacker[2]['Crit'] * .9)

        if defender[0]['ID'] == defender[1]['ID']:
            defender[1]['ATK'] = int(defender[1]['ATK'] * .9)
            defender[1]['Crit'] = int(defender[1]['Crit'] * .9)

        if defender[0]['ID'] == defender[2]['ID']:
            defender[2]['ATK'] = int(defender[2]['ATK'] * .9)
            defender[2]['Crit'] = int(defender[2]['Crit'] * .9)

        if defender[1]['ID'] == defender[2]['ID']:
            defender[2]['ATK'] = int(defender[2]['ATK'] * .9)
            defender[2]['Crit'] = int(defender[2]['Crit'] * .9)

        #Conduct PvP operations between the brotherhoods to determine the winner
        attacker_wins = 0
        defender_wins = 0
        battle_info = ''

        for i in range(0,3):
            winner, loser = simulate_battle(attacker[i], defender[i]) #Same from PvP.tournament
            if attacker[i]['ID'] == winner['ID']:
                attacker_wins += 1
                battle_info += f"{guild['Name']}'s {attacker[i]['Name']} defeated {defending_guild['Name']}'s {defender[i]['Name']}.\n"
            else:
                defender_wins += 1
                battle_info += f"{defending_guild['Name']}'s {defender[i]['Name']} defeated {guild['Name']}'s {attacker[i]['Name']}.\n"

        #Log battle, change controller if applicable, return output
        if attacker_wins > defender_wins:
            await AssetCreation.set_area_controller(self.client.pg_con, guild['Base'], guild['ID'])
            await AssetCreation.log_area_attack(self.client.pg_con, guild['Base'], guild['ID'], defending_guild['ID'], guild['ID'])
            await self.client.announcement_channel.send(f"**{guild['Name']} (ID: `{guild['ID']}`)** has defeated **{defending_guild['Name']}**, seizing control over {guild['Base']}.")
            await ctx.reply(f"{battle_info}{guild['Name']} has seized control over {guild['Base']}!")
        else:
            await AssetCreation.log_area_attack(self.client.pg_con, guild['Base'], defending_guild['ID'], guild['ID'], defending_guild['ID'])
            await ctx.reply(f"{battle_info}Your attack on {guild['Base']} was put down by the champions of {defending_guild['Name']}.")

    @brotherhood.command(aliases=['disband'], description='Disband your association. You can only do this when no one else remains in your association.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.in_brotherhood)
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

    @brotherhood.command(description='Shows this command.')
    async def help(self, ctx):
        """Get a list of all commands that brotherhood members can use."""
        desc = 'Brotherhoods are a pvp-oriented association. Its members gain an ATK and CRIT bonus depending on its level. They also gain access to the `steal` command.'
        helper = menus.MenuPages(source=PageMaker(PageMaker.paginate_help(ctx=ctx,
                                                                          command='brotherhood',
                                                                          help_for='Brotherhoods',
                                                                          description=desc)), 
                                 clear_reactions_after=True, 
                                 delete_message_after=True)
        await helper.start(ctx)

def setup(client):
    client.add_cog(Brotherhoods(client))