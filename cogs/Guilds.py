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
        await AssetCreation.leaveGuild(self.client.pg_con, ctx.author.id)
        await ctx.reply('You left your guild.')

    @guild.command(aliases=['inv'], brief='<url>', description='Invite a player to your guild.')
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_guild_officer)
    @commands.check(Checks.guild_has_vacancy)
    async def invite(self, ctx, player : commands.MemberConverter):
        #Ensure target player has a character and is not in a guild
        if not await Checks.has_char(self.client.pg_con, player):
            await ctx.reply('This person does not have a character.')
            return
        if not await Checks.target_not_in_guild(self.client.pg_con, player):
            await ctx.reply('This player is already in an association.')
            return

        #See how recently they joined an association
        last_join = await AssetCreation.check_last_guild_join(self.client.pg_con, player.id)
        if last_join < 86400:
            cd = 86400 - last_join
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
            return user == player

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
        # Get the list of members, theoretically sorted by rank
        guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        members = await AssetCreation.getGuildMembers(self.client.pg_con, guild['ID'])
        # Sort them into dpymenus pages
        member_list = []

        async def write(start, members):
            page = discord.Embed(title=f"{guild['Name']}: Members")
            iteration = 0

            while start < len(members) and iteration < 10:
                attack, crit = await AssetCreation.getAttack(self.client.pg_con, members[start][0])
                level = await AssetCreation.getLevel(self.client.pg_con, members[start][0])
                player = await self.client.fetch_user(members[start][0])
                page.add_field(name=f'{player.name}: {members[start][1]} [{members[start][2]}]', 
                    value=f'Level `{level}`, with `{attack}` attack and `{crit}` crit.', inline=False)
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
        capital_gain = math.floor(capital * multplier)

        #Class bonus
        role = await AssetCreation.getClass(self.client.pg_con, ctx.author.id)
        if role == 'Engineer':
            capital_gain = math.floor(capital_gain * 1.25)

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

    @guild.command(brief='<area>', description='Select an area to base your association in. The valid locations are:\n`Aramithea`, `Riverburn`, `Thenuille`')
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_guild_leader)
    async def base(self, ctx, *, area : str):
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
                return user == ctx.author

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
    async def info(self, ctx, guild_id : int):
        try:
            info = await AssetCreation.getGuildByID(self.client.pg_con, guild_id)
        except TypeError:
            await ctx.reply('No association has that ID.')
            return

        leader = await self.client.fetch_user(info['Leader'])
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
        embed.set_footer(text=f"{info['Type']} ID: {info['ID']}")
        await ctx.reply(embed=embed)

    @guild.command(aliases=['desc'], brief='<desc>', description='Change your brotherhood\'s description. [GUILD OFFICER+ ONLY]')
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_guild_officer)
    async def description(self, ctx, *, desc : str):
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
        #See how recently they joined an association
        last_join = await AssetCreation.check_last_guild_join(self.client.pg_con, ctx.author.id)
        if last_join < 86400:
            cd = 86400 - last_join
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

    @guild.command(description='Shows this command.')
    async def help(self, ctx):
        def write(ctx, start, entries):
            helpEmbed = discord.Embed(title=f'Ayesha Help: Brotherhoods', description='Guilds are a financially-oriented association. Its members gain more money from selling items. They also gain access to the `invest` command.', color=self.client.ayesha_blue)
            helpEmbed.set_thumbnail(url=ctx.author.avatar_url)
            
            iteration = 0
            while start < len(entries) and iteration < 5: #Will loop until 5 entries are processed or there's nothing left in the queue
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
        for command in self.client.get_command('brotherhood').walk_commands():
            cmds.append(command)
        for i in range(0, len(cmds), 5):
            embeds.append(write(ctx, i, cmds))

        helper = menus.MenuPages(source=PageSourceMaker.PageMaker(embeds), 
                                 clear_reactions_after=True, 
                                 delete_message_after=True)
        await helper.start(ctx)

def setup(client):
    client.add_cog(Guilds(client))