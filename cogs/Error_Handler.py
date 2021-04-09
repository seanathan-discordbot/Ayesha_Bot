import discord
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

import os
import time
import traceback
import logging

import asyncpg

from Utilities import Links, Checks
from Utilities.Checks import NoChar

class Error_Handler(commands.Cog):
    def __init__(self,client):
        self.client = client

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('Error Handler is ready.')

    #----- ERROR HANDLER -----
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, NoChar):
            await ctx.reply('You don\'t have a character yet. Do `start` to make one!')

        if isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.BadArgument):
            ctx.command.reset_cooldown(ctx)
            embed = discord.Embed(title=f'You forgot an argument', color=0xBEDCF6)
            if ctx.command.brief and ctx.command.aliases:
                embed.add_field(name=f'{ctx.command.name} `{ctx.command.brief}`', value=f'Aliases: `{ctx.command.aliases}`\n{ctx.command.description}', inline=False)
            elif ctx.command.brief and not ctx.command.aliases:
                embed.add_field(name=f'{ctx.command.name} `{ctx.command.brief}`', value=f'{ctx.command.description}', inline=False)
            elif not ctx.command.brief and ctx.command.aliases:
                embed.add_field(name=f'{ctx.command.name}', value=f'Aliases: `{ctx.command.aliases}`\n{ctx.command.description}', inline=False)
            else:
                embed.add_field(name=f'{ctx.command.name}', value=f'{ctx.command.description}', inline=False)
            await ctx.reply(embed=embed)
        if isinstance(error, commands.CheckFailure):
            await ctx.reply('You are ineligible to use this command.')
        if isinstance(error, commands.MaxConcurrencyReached):
            await ctx.reply('Max concurrency reached. Please wait until this command ends.')
        if isinstance(error, commands.MemberNotFound):
            await ctx.reply('Could not find a player with that name.')
        if isinstance(error, CommandOnCooldown): #Please stop printing this
            if error.retry_after >= 3600:
                await ctx.reply(f'You are on cooldown for `{time.strftime("%H:%M:%S", time.gmtime(error.retry_after))}`.')
            elif error.retry_after >= 60:
                await ctx.reply(f'You are on cooldown for `{time.strftime("%M:%S", time.gmtime(error.retry_after))}`.')
            else:
                await ctx.reply(f'You are on cooldown for another `{error.retry_after:.2f}` seconds.')
        if isinstance(error, commands.BotMissingPermissions):
            await ctx.reply('sssss')

        print(error)

def setup(client):
    client.add_cog(Error_Handler(client))