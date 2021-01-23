import discord
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

import json
import os

import time
import traceback

Token = 'TOKEN'

def get_prefix(client, message):
    with open(r'F:\OneDrive\Ayesha\prefixes.json','r') as f:
        prefixes = json.load(f)
    return prefixes[str(message.guild.id)]

client = commands.Bot(command_prefix=get_prefix, help_command=None)

admins = [196465885148479489, 325080171591761921, 530760994289483790, 465388103792590878] #Seb, Sean, Demi, Bort
def is_admin(ctx):
        if ctx.author.id in admins:
            return True
        
#Create bot cooldown
_cd = commands.CooldownMapping.from_cooldown(1, 2.5, commands.BucketType.user) 

@client.check
async def cooldown_check(ctx):
    bucket = _cd.get_bucket(ctx.message)
    retry_after = bucket.update_rate_limit()
    if retry_after:
        raise commands.CommandOnCooldown(bucket, retry_after)
    return True

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game('Say %tutorial to get started!'))
    print('Hi my name is Ayesha.')        

# ----- PREFIX CHANGES ------
@client.event #the default prefix is %
async def on_guild_join(guild):
    with open(r'F:\OneDrive\Ayesha\prefixes.json','r') as f:
        prefixes = json.load(f)
    prefixes[str(guild.id)] = '%'
    with open(r'F:\OneDrive\Ayesha\prefixes.json','w') as f:
        json.dump(prefixes, f, indent=4)

@client.event #deletes the set prefix when a bot leaves the server
async def on_guild_remove(guild):
    with open(r'F:\OneDrive\Ayesha\prefixes.json','r') as f:
        prefixes = json.load(f)
    prefixes.pop(str(guild.id))
    with open(r'F:\OneDrive\Ayesha\prefixes.json','w') as f:
        json.dump(prefixes, f, indent=4)

@client.command()
@commands.has_guild_permissions(manage_permissions=True)
@cooldown(1, 30, BucketType.guild)
async def changeprefix(ctx, prefix):
    with open(r'F:\OneDrive\Ayesha\prefixes.json','r') as f:
        prefixes = json.load(f)
    prefixes[str(ctx.guild.id)] = prefix
    with open(r'F:\OneDrive\Ayesha\prefixes.json','w') as f:
        json.dump(prefixes, f, indent=4)
    await ctx.send(f'Prefix changed to {prefix}') 

# ----- ERROR HANDLER -----
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
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
        return
    if isinstance(error, commands.CheckFailure):
        await ctx.reply('You are ineligible to use this command.')
        return
    if isinstance(error, CommandOnCooldown):
        if error.retry_after >= 3600:
            await ctx.send(f'You are on cooldown for `{time.strftime("%H:%M:%S", time.gmtime(error.retry_after))}`.')
        elif error.retry_after >= 60:
            await ctx.send(f'You are on cooldown for `{time.strftime("%M:%S", time.gmtime(error.retry_after))}`.')
        else:
            await ctx.send(f'You are on cooldown for another `{error.retry_after:.2f}` seconds.')
        return
    if isinstance(error, commands.MaxConcurrencyReached):
        await ctx.send('Max concurrency reached. Please wait until this command ends.')
    if isinstance(error, commands.MemberNotFound):
        await ctx.reply('Could not find a player with that name.')
    
    print('Ignoring exception in command {}:'.format(ctx.command))
    traceback.print_exception(type(error), error, error.__traceback__)

# ----- OTHER COMMANDS -----
@client.command(brief=None, description='Ping to see if bot is working')
async def ping(ctx):
    embed = discord.Embed(title="Pong!", description=f"Latency is {client.latency * 1000:.2f} ms", color=0xBEDCF6)
    await ctx.send(embed=embed)


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
for filename in os.listdir(r'F:\OneDrive\Ayesha\cogs'):
    if filename.endswith('.py'): # see if the file is a python file
        client.load_extension(f'cogs.{filename[:-3]}')

#Also delete the music files downloaded
for filename in os.listdir(r'F:\OneDrive\NguyenBot\Music Files'):
    os.remove(f'F:/OneDrive/Ayesha/Music Files/{filename}')

client.run(Token)