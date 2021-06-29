import discord
from discord.ext import commands
from discord.ext.commands import CommandOnCooldown

import time
from datetime import datetime

from Utilities import Checks

class Error_Handler(commands.Cog):
    """Quick error handler that needs improvement"""
    def __init__(self,client):
        self.client = client

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('Error Handler is ready.')

    #----- ERROR HANDLER -----
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.BadArgument):
            ctx.command.reset_cooldown(ctx)
            embed = discord.Embed(title=f'You forgot an argument', 
                                  color=self.client.ayesha_blue)
            if ctx.command.brief and ctx.command.aliases:
                embed.add_field(name=f'{ctx.command.name} `{ctx.command.brief}`', 
                                value=f'Aliases: `{ctx.command.aliases}`\n{ctx.command.description}', 
                                inline=False)
            elif ctx.command.brief and not ctx.command.aliases:
                embed.add_field(name=f'{ctx.command.name} `{ctx.command.brief}`', 
                                value=f'{ctx.command.description}', 
                                inline=False)
            elif not ctx.command.brief and ctx.command.aliases:
                embed.add_field(name=f'{ctx.command.name}', 
                                value=f'Aliases: `{ctx.command.aliases}`\n{ctx.command.description}', 
                                inline=False)
            else:
                embed.add_field(name=f'{ctx.command.name}', 
                                value=f'{ctx.command.description}', 
                                inline=False)
            await ctx.reply(embed=embed)

        # --- ALL commands.CheckFailure MANMADE SUBCLASSES COVERED HERE
        if isinstance(error, Checks.HasChar):
            await ctx.reply(f'You already have a character.\nFor help, read the `{ctx.prefix}tutorial` or go to the `{ctx.prefix}support` server.')
        if isinstance(error, Checks.NoChar):
            await ctx.reply(f'You do not have a character yet. Do `{ctx.prefix}start` to make one!')

        if isinstance(error, Checks.NotBrotherhoodMember):
            await ctx.reply('You are not in a brotherhood.')
        if isinstance(error, Checks.NotGuildMember):
            await ctx.reply('You are not in a guild.')
        if isinstance(error, Checks.NotCollegeMember):
            await ctx.reply('You are not in a college.')

        if isinstance(error, Checks.IsNotAssociationLeader):
            await ctx.reply('Only the leader of your association can use this command!')
        if isinstance(error, Checks.IsNotAssociationOfficer):
            await ctx.reply('Only an officer or leader of your association can use this command!')
        if isinstance(error, Checks.IsAssociationLeader):
            await ctx.reply('You can\'t use this command as the leader of your association!')

        if isinstance(error, Checks.AssociationFull):
            await ctx.reply('Your association has no vacancies.')
        
        if isinstance(error, Checks.NotAdmin):
            await ctx.reply('You woulda thought.')
        if isinstance(error, Checks.NotMayor):
            await ctx.reply('This command is reserved for the mayor. Become the mayor by joining a college and gaining a lot of gravitas!')
        if isinstance(error, Checks.NotComptroller):
            await ctx.reply('This command is reserved for the comptroller. Become the comptroller by joining a guild and becoming the richest player in Aramythia!')

        if isinstance(error, Checks.HasNoBankAccount):
            await ctx.reply(f'You don\'t have a guild bank account. Do `{ctx.prefix}guild account open` to get one!')
        if isinstance(error, Checks.HasBankAccount):
            await ctx.reply(f'You already have a guild bank account! Do `{ctx.prefix}guild account` to view it!')

        # --- OTHER ---

        if isinstance(error, commands.MaxConcurrencyReached):
            await ctx.reply('Max concurrency reached. Please wait until this command ends.')
        if isinstance(error, commands.MemberNotFound):
            await ctx.reply('Could not find a player with that name.')
        if isinstance(error, CommandOnCooldown): #Please stop printing this
            if error.retry_after >= 3600:
                cd_length = time.strftime("%H:%M:%S", time.gmtime(error.retry_after))
                await ctx.reply(f'You are on cooldown for `{cd_length}`.')
            elif error.retry_after >= 60:
                cd_length = time.strftime("%M:%S", time.gmtime(error.retry_after))
                await ctx.reply(f'You are on cooldown for `{cd_length}`.')
            else:
                await ctx.reply(f'You are on cooldown for another `{error.retry_after:.2f}` seconds.')

        try:
            print(f'{datetime.now()}: {error}\nUser: {ctx.author.id}   | Command: {ctx.command.name}\n\n')
        except AttributeError:
            print(f'{datetime.now()}: {error}\nUser: {ctx.author.id}   | Command: {ctx.message.content}\n\n')

def setup(client):
    client.add_cog(Error_Handler(client))