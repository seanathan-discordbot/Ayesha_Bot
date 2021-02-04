import discord
import asyncio

from discord.ext import commands
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown
from dpymenus import Page, PaginatedMenu

from Utilities import Checks, AssetCreation, PageSourceMaker

import random
import math

# There will be brotherhoods, guilds, and later colleges for combat, economic, and political gain

class Brotherhoods(commands.Cog):

    def __init__(self, client):
        self.client = client

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('Brotherhoods is ready.')

    #COMMANDS
    @commands.group(aliases=['bh'], invoke_without_command=True, case_insensitive=True, description='See your brotherhood')
    @commands.check(Checks.in_brotherhood)
    async def brotherhood(self, ctx):
        info = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        getLeader = commands.UserConverter()
        leader = await getLeader.convert(ctx, str(info['Leader']))
        level, progress = await AssetCreation.getGuildLevel(self.client.pg_con, info['ID'], returnline=True)
        members = await AssetCreation.getGuildMemberCount(self.client.pg_con, info['ID'])
        capacity = await AssetCreation.getGuildCapacity(self.client.pg_con, info['ID'])

        embed = discord.Embed(title=f"{info['Name']}", color=0xBEDCF6)
        embed.set_thumbnail(url=f"{info['Icon']}")
        embed.add_field(name='Leader', value=f"{leader.mention}")
        embed.add_field(name='Members', value=f"{members}/{capacity}")
        embed.add_field(name='Level', value=f"{level}")
        embed.add_field(name='EXP Progress', value=f'{progress}')
        embed.add_field(name=f"This {info['Type']} is {info['Join']} to new members.", value=f"{info['Desc']}", inline=False)
        embed.set_footer(text=f"Brotherhood ID: {info['ID']}")
        await ctx.reply(embed=embed)

    @brotherhood.command(aliases=['found', 'establish', 'form', 'make'], brief='<name>', description='Found a brotherhood. Costs 15,000 gold.')
    @commands.check(Checks.not_in_guild)
    async def create(self, ctx, *, name : str):
        if len(name) > 32:
            await ctx.reply('Name max 32 characters')
            return
        # Make sure they have the money and an open name
        if not await Checks.guild_can_be_created(ctx, name):
            return
        # Otherwise create the guild
        await AssetCreation.createGuild(self.client.pg_con, name, "Brotherhood", ctx.author.id, 'https://cdn4.iconfinder.com/data/icons/ionicons/512/icon-ios7-contact-512.png')
        await ctx.reply('Brotherhood founded. Do `brotherhood` to see it or `brotherhood help` for more commands!')

    @brotherhood.command(aliases=['inv'], brief='<url>', description='Invite a player to your guild.')
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
        #Otherwise invite the player
        #Load the guild
        guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        #Create and send embed invitation
        embed = discord.Embed(color=0xBEDCF6)
        embed.add_field(name=f"Invitation to {guild['Name']}", value=f"{player.mention}, {ctx.author.mention} is inviting you to join their {guild['Type']}.")

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

    @brotherhood.command(description='Leave your brotherhood.')
    @commands.check(Checks.in_brotherhood)
    @commands.check(Checks.is_not_guild_leader)
    async def leave(self, ctx):
        await AssetCreation.leaveGuild(self.client.pg_con, ctx.author.id)
        await ctx.reply('You left your brotherhood.')

    @brotherhood.command(aliases=['donate'], brief='<money : int>', description='Donate to your association, increasing its xp!')
    @commands.check(Checks.in_brotherhood)
    async def contribute(self, ctx, donation : int):
        #Make sure they have the money they're paying and that the guild is <lvl 10
        guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        level = await AssetCreation.getGuildLevel(self.client.pg_con, guild['ID'])
        if level >= 10:
            await ctx.reply('Your guild is already at its maximum level')
            return

        if donation > await AssetCreation.getGold(self.client.pg_con, ctx.author.id):
            await ctx.reply('You don\'t have that much money to donate.')
            return

        #Remove money from account and add xp to guild
        await AssetCreation.giveGold(self.client.pg_con, 0 - donation, ctx.author.id)
        await AssetCreation.giveGuildXP(self.client.pg_con, donation, guild['ID'])

        #Also calculate how much more xp is needed for a level up
        xp = await AssetCreation.getGuildXP(self.client.pg_con, guild['ID'])
        needed = 1000000 - (xp % 1000000)
        await ctx.reply(f'You contributed `{donation}` gold to your brotherhood. It will become level `{int(xp/1000000)+1}` at `{needed}` more xp.')

    @brotherhood.command(description='View the other members of your guild.')
    @commands.check(Checks.in_brotherhood)
    async def members(self, ctx):
        # Get the list of members, theoretically sorted by rank
        guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        members = await AssetCreation.getGuildMembers(self.client.pg_con, guild['ID'])
        # Sort them into dpymenus pages
        member_list = []

        async def write(start, members):
            page = Page(title=f"{guild['Name']}: Members")
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

        menu = PaginatedMenu(ctx)
        menu.add_pages(member_list)
        menu.set_timeout(30)
        menu.show_command_message()
        await menu.open()

    @brotherhood.command(description='Steal 5% of a random player\'s cash. The probability of stealing is about your brotherhood\'s level * .05 + .2. 30 minute cooldown.')
    @commands.check(Checks.in_brotherhood)
    @cooldown(1, 1800, BucketType.user)
    async def steal(self, ctx):
        guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        level = await AssetCreation.getGuildLevel(self.client.pg_con, guild['ID'])
        if random.randint(0,100) >= 20 + level*5: #Then failure
            await ctx.reply('You were caught and had to flee.')
            return

        # Otherwise get a random player and steal 5% of their money
        records = await AssetCreation.getPlayerCount(self.client.pg_con, )
        victim_num = random.randint(1, records - 1)

        try: #there might be deleted chars - just give them 100 gold lmao
            victim_gold, victim, victim_name = await AssetCreation.getPlayerByNum(self.client.pg_con, victim_num)
        except TypeError:
            await AssetCreation.giveGold(self.client.pg_con, 100, ctx.author.id)
            await ctx.reply('You stole `100` gold from a random guy.')
            return

        # Make sure they don't rob themself
        if ctx.author.id == victim:
            await ctx.reply('You were caught and had to flee.')
            return

        # 50 gold minimum steal. If they don't have 1000, just add 50 to the econ.
        if victim_gold < 1000:
            await AssetCreation.giveGold(self.client.pg_con, 50, ctx.author.id)
            stolen_amount = 50
        else:
            stolen_amount = math.floor(victim_gold / 20)
            role = await AssetCreation.getClass(self.client.pg_con, ctx.author.id)
            if role == 'Engineer':
                stolen_amount = math.floor(victim_gold / 12)
            await AssetCreation.giveGold(self.client.pg_con, stolen_amount, ctx.author.id)
            await AssetCreation.giveGold(self.client.pg_con, 0 - stolen_amount, victim)
        
        await ctx.reply(f'You stole `{stolen_amount}` gold from `{victim_name}`.')

    @brotherhood.command(aliases=['guildinfo', 'bhinfo'], brief='<guild ID>', description='See info on another guild based on their ID')
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

        embed = discord.Embed(title=f"{info['Name']}", color=0xBEDCF6)
        embed.set_thumbnail(url=f"{info['Icon']}")
        embed.add_field(name='Leader', value=f"{leader.mention}")
        embed.add_field(name='Members', value=f"{members}/{capacity}")
        embed.add_field(name='Level', value=f"{level}")
        embed.add_field(name='EXP Progress', value=f'{progress}')
        embed.add_field(name=f"This {info['Type']} is {info['Join']} to new members.", value=f"{info['Desc']}", inline=False)
        embed.set_footer(text=f"{info['Type']} ID: {info['ID']}")
        await ctx.reply(embed=embed)

    @brotherhood.command(aliases=['desc'], brief='<desc>', description='Change your brotherhood\'s description. [GUILD OFFICER+ ONLY]')
    @commands.check(Checks.is_guild_officer)
    async def description(self, ctx, *, desc : str):
        if len(desc) > 256:
            await ctx.reply(f'Description max 256 characters. You gave {len(desc)}')
            return
        # Get guild and change description
        guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        await AssetCreation.setGuildDescription(self.client.pg_con, desc, guild['ID'])
        await ctx.reply('Description updated!')

    @brotherhood.command(description='Lock/unlock your guild from letting anyone join without an invite.')
    @commands.check(Checks.is_guild_leader)
    async def lock(self, ctx):
        guild = await AssetCreation.getGuildFromPlayer(self.client.pg_con, ctx.author.id)
        if guild['Join'] == 'open':
            await AssetCreation.lockGuild(self.client.pg_con, guild['ID'])
            await ctx.reply('Your guild is now closed to new members. Players can only join your guild via invite.')
        else:
            await AssetCreation.unlockGuild(self.client.pg_con, guild['ID'])
            await ctx.reply('Your guild is now open to members. Anyone may join with the `join` command!')

    @brotherhood.command(brief='<guild id : int>', description='Join the target guild if its open!')
    @commands.check(Checks.not_in_guild)
    async def join(self, ctx, guild_id : int):
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

    @brotherhood.command(brief='<player> <Officer/Adept>', description='Promote a member of your guild. Officers have limited administrative powers. Adepts have no powers. [LEADER ONLY]')
    @commands.check(Checks.is_guild_leader)        
    async def promote(self, ctx, player : commands.MemberConverter = None, rank : str = None):
        #Tell players what officers and adepts do if no input is given
        if player is None or rank is None:
            embed = discord.Embed(title='Brotherhood Role Menu', color=0xBEDCF6)
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

    @brotherhood.command(brief='<player>', description='Transfer guild ownership to another member.')
    @commands.check(Checks.is_guild_leader)
    async def transfer(self, ctx, player : commands.MemberConverter):
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

    @brotherhood.command(description='Shows this command.')
    async def help(self, ctx):
        def write(ctx, start, entries):
            helpEmbed = Page(title=f'NguyenBot Help: Brotherhoods', description='Brotherhoods are a pvp-oriented association. Its members gain an ATK and CRIT bonus depending on its level. They also gain access to the `steal` command.', color=0xBEDCF6)
            helpEmbed.set_thumbnail(url=ctx.author.avatar_url)
            
            iteration = 0
            while start < len(entries) and iteration < 5: #Will loop until 5 entries are processed or there's nothing left in the queue
                if entries[start].brief and entries[start].aliases:
                    helpEmbed.add_field(name=f'{entries[start].name} `{entries[start].brief}`', value=f'Aliases: `{entries[start].aliases}`\n{entries[start].description}', inline=False)
                elif entries[start].brief and not entries[start].aliases:
                    helpEmbed.add_field(name=f'{entries[start].name} `{entries[start].brief}`', value=f'{entries[start].description}', inline=False)
                elif not entries[start].brief and entries[start].aliases:
                    helpEmbed.add_field(name=f'{entries[start].name}', value=f'Aliases: `{entries[start].aliases}`\n{entries[start].description}', inline=False)
                else:
                    helpEmbed.add_field(name=f'{entries[start].name}', value=f'{entries[start].description}', inline=False)
                iteration += 1
                start +=1 
                
            return helpEmbed

        cmds, embeds = [], []
        for command in self.client.get_command('brotherhood').walk_commands():
            cmds.append(command)
        for i in range(0, len(cmds), 5):
            embeds.append(write(ctx, i, cmds))

        menu = PaginatedMenu(ctx)
        menu.add_pages(embeds)
        await menu.open()

def setup(client):
    client.add_cog(Brotherhoods(client))