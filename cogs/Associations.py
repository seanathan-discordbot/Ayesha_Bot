import discord
import asyncio

from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

import aiosqlite
from Utilities import Checks, AssetCreation, PageSourceMaker

import random

PATH = 'PATH'

# There will be brotherhoods, guilds, and later colleges for combat, economic, and political gain

class Associations(commands.Cog):

    def __init__(self, client):
        self.client = client

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('Associations is ready.')

    #COMMANDS
    @commands.group(aliases=['bh'], invoke_without_command=True, case_insensitive=True, description='See your brotherhood')
    @commands.check(Checks.in_brotherhood)
    async def brotherhood(self, ctx):
        info = await AssetCreation.getGuildFromPlayer(ctx.author.id)
        getLeader = commands.UserConverter()
        leader = await getLeader.convert(ctx, str(info['Leader']))
        level, progress = await AssetCreation.getGuildLevel(info['ID'], returnline=True)
        embed = discord.Embed(title=f"{info['Name']}", color=0xBEDCF6)
        embed.set_thumbnail(url=f"{info['Icon']}")
        embed.add_field(name='Leader', value=f"{leader.mention}")
        embed.add_field(name='Level', value=f"{level}")
        embed.add_field(name='EXP Progress', value=f'{progress}')
        embed.add_field(name=f"This is a {info['Type']}", value=f"{info['Desc']}", inline=False)
        await ctx.reply(embed=embed)

    @brotherhood.command(brief='<name>', description='Found a brotherhood. Costs 15,000 gold.')
    @commands.check(Checks.not_in_guild)
    async def create(self, ctx, *, name : str):
        if len(name) > 32:
            await ctx.reply('Name max 32 characters')
            return
        # Make sure they have the money and an open name
        if not await Checks.guild_can_be_created(ctx, name):
            return
        # Otherwise create the guild
        async with aiosqlite.connect(PATH) as conn:
            await conn.execute('INSERT INTO guilds (guild_name, guild_type, leader_id, guild_icon) VALUES (?, ?, ?, ?)', (name, 'Brotherhood', ctx.author.id, 'https://cdn4.iconfinder.com/data/icons/ionicons/512/icon-ios7-contact-512.png'))
            c = await conn.execute('SELECT guild_id FROM guilds WHERE leader_id = ?', (ctx.author.id,))
            guild_id = await c.fetchone()
            await conn.execute('UPDATE players SET guild = ?, gold = gold - 15000 WHERE user_id = ?', (guild_id[0], ctx.author.id,))
            await conn.commit()
        await ctx.reply('Brotherhood founded. Do `brotherhood` to see it or `brotherhood help` for more commands!')

    @brotherhood.command(brief='<desc', description='Change your brotherhood\'s description [GUILD LEADER ONLY]')
    @commands.check(Checks.is_guild_leader)
    async def description(self, ctx, *, desc : str):
        if len(desc) > 256:
            await ctx.reply(f'Description max 256 characters. You gave {len(desc)}')
            return
        # Get guild and change description
        async with aiosqlite.connect(PATH) as conn:
            c = await conn.execute('SELECT guild FROM players WHERE user_id = ?', (ctx.author.id,)) 
            guild_id = await c.fetchone()
            await conn.execute('UPDATE guilds SET guild_desc = ? WHERE guild_id = ?', (desc, guild_id[0]))
            await conn.commit()
        await ctx.reply('Description updated!')

    @brotherhood.command(brief='<url>', description='Invite a player to your guild')
    @commands.check(Checks.is_guild_leader)
    async def invite(self, ctx, player : commands.MemberConverter):
        #Ensure target player has a character and is not in a guild
        if not await Checks.has_char(player):
            await ctx.reply('This person does not have a character.')
            return
        if not await Checks.target_not_in_guild(player):
            await ctx.reply('This player is already in an association.')
            return
        #Otherwise invite the player
        #Load the guild
        guild = await AssetCreation.getGuildFromPlayer(ctx.author.id)
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
                async with aiosqlite.connect(PATH) as conn:
                    await conn.execute('UPDATE Players SET guild = ? WHERE user_id = ?', (guild['ID'], player.id))
                    await conn.commit()
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

def setup(client):
    client.add_cog(Associations(client))