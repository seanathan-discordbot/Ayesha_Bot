import discord
import os
from discord.ext import commands
Token
client=commands.Bot(command_prefix="!")
admins = [196465885148479489, 325080171591761921, 530760994289483790, 145339105239105537] #Aramy, Sean, Demi, Roberto

def is_admin(ctx):
        if ctx.author.id in admins:
            return True

@client.command()
@commands.check(is_admin)
async def load(ctx, extension):
    client.load_extension(f'cogs.{extension}')
    await ctx.channel.send('Loaded.')

@client.command()
@commands.check(is_admin)
async def unload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    await ctx.channel.send('Unloaded.')

@client.command()
@commands.check(is_admin)
async def reload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    client.load_extension(f'cogs.{extension}')
    await ctx.channel.send('Reloaded.')

# Runs at bot startup to load all cogs
for filename in os.listdir(r'C:\Users\rowlas2\Documents\Seanathan\cogs'):
        client.load_extension(f'cogs.{filename[:-3]}')
client.run(Token)
