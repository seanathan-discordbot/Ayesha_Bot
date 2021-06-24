import discord

from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

from Utilities import Checks, AssetCreation

class Admin(commands.Cog):
    """Admin commands for bot administrators.
    Each command in this module must have the is_admin check.
    """

    def __init__(self, client):
        self.client = client

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('Admin is ready.')

    #COMMANDS
    @commands.command(description='None')
    @commands.check(Checks.is_admin)
    async def agold(self, ctx, gold : int, player : commands.MemberConverter):
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.reply('Not here.')
            return
        #Make sure second player is also a player
        if not await Checks.has_char(self.client.pg_con, player):
            await ctx.reply('This person does not have a character.')
            return

        await AssetCreation.giveGold(self.client.pg_con, gold, player.id)
        await ctx.reply('Gold given.')

    @commands.command(description='None')
    @commands.check(Checks.is_admin)
    async def arubidic(self, ctx, amount : int, player : commands.MemberConverter):
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.reply('Not here.')
            return
        #Make sure second player is also a player
        if not await Checks.has_char(self.client.pg_con, player):
            await ctx.reply('This person does not have a character.')
            return

        await AssetCreation.giveRubidics(self.client.pg_con, amount, player.id)
        await ctx.reply('Rubidics given.')

    @commands.command(description='None')
    @commands.check(Checks.is_admin)
    async def rcd(self, ctx):
        for cmd in self.client.walk_commands():
            cmd.reset_cooldown(ctx)
        await ctx.reply('Reset your cooldowns.')

    # @commands.command(description='None')
    # @commands.check(Ayesha.is_admin)
    # async def aacolyte(self, ctx, acolyte_name, player : commands.MemberConverter):
    #     if isinstance(ctx.channel, discord.DMChannel):
    #         await ctx.reply('Not here.')
    #         return
    #     #Make sure second player is also a player
    #     if not await Checks.has_char(self.client.pg_con, player):
    #         await ctx.reply('This person does not have a character.')
    #         return

    #     with open(r'F:\OneDrive\Ayesha\Assets\Acolyte_List.json') as f:
    #         names = f.read()

    #     try:
    #         acolyte = names[acolyte_name]['Name']
    #         await AssetCreation.createAcolyte(self.client.pg_con, player.id, acolyte)
    #     except KeyError:
    #         await ctx.reply('No acolyte by that name.')
    #         return

def setup(client):
    client.add_cog(Admin(client))