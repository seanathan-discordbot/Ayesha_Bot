import discord
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

import json
import os


Token = 'Token'

def get_prefix(client, message):
    with open(r'<PATH>\prefixes.json>','r') as f:
        prefixes = json.load(f)
    return prefixes[str(message.guild.id)]

client = commands.Bot(command_prefix=get_prefix, help_command=None)

admins = [196465885148479489, 325080171591761921, 530760994289483790, 145339105239105537] #Aramy, Sean, Demi, Roberto
def is_admin(ctx):
        if ctx.author.id in admins:
            return True

# ----- PREFIX CHANGES ------
@client.event #the default prefix is %
async def on_guild_join(guild):
    with open(r'<PATH>\prefixes.json','r') as f:
        prefixes = json.load(f)
    prefixes[str(guild.id)] = '%'
    with open(r'<PATH>\prefixes.json','w') as f:
        json.dump(prefixes, f, indent=4)

@client.event #deletes the set prefix when a bot leaves the server
async def on_guild_remove(guild):
    with open(r'<PATH>\prefixes.json','r') as f:
        prefixes = json.load(f)
    prefixes.pop(str(guild.id))
    with open(r'<PATH>\prefixes.json','w') as f:
        json.dump(prefixes, f, indent=4)

@client.command()
@cooldown(1, 30, BucketType.guild)
async def changeprefix(ctx, prefix):
    with open(r'<PATH>\prefixes.json','r') as f:
        prefixes = json.load(f)
    prefixes[str(ctx.guild.id)] = prefix
    with open(r'<PATH>\prefixes.json','w') as f:
        json.dump(prefixes, f, indent=4)
    await ctx.send(f'Prefix changed to {prefix}') 


# ----- LOAD COGS -----
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
