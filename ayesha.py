import discord
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

import os
import logging

import asyncpg

from Utilities import Links, Checks

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename=Links.log_file, 
                              encoding='utf-8', 
                              mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

async def get_prefix(client, message):
    """Return the prefix of a server. If the channel is a DM, then it is %."""
    if isinstance(message.channel, discord.DMChannel):
        return '%'

    conn = await asyncpg.connect(database=Links.database_name, 
                                 user=Links.database_user, 
                                 password=Links.database_password)
    psql = """SELECT prefix FROM prefixes WHERE server = $1"""
    prefix = await conn.fetchval(psql, message.guild.id)
    if prefix is None: #bot joined server while offline
        psql = """INSERT INTO prefixes (server, prefix) VALUES ($1, '%')"""
        await conn.execute(psql, message.guild.id)
        prefix = '%'
    await conn.close()
    return prefix

client = commands.Bot(
                      command_prefix=get_prefix, 
                      help_command=None, 
                      case_insensitive=True)
client.ayesha_blue = 0xBEDCF6
client.recent_voters = []

client.admins = [
    196465885148479489, # Ara
    325080171591761921, # Sean
    530760994289483790, # Demi
    465388103792590878  # Bort
]
def is_admin(ctx):
    if ctx.author.id in client.admins:
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
    game_presence = 'Read the %tutorial to get started!'
    await client.change_presence(activity=discord.Game(game_presence))
    print('Hi my name is Ayesha.')   

# ----- PREFIX CHANGING STUFF -----

@client.event #the default prefix is %
async def on_guild_join(guild):
    async with client.pg_con.acquire() as conn:
        psql = """INSERT INTO prefixes (server, prefix) VALUES ($1, '%')"""
        await conn.execute(psql, guild.id) 

@client.event #deletes the set prefix when a bot leaves the server
async def on_guild_remove(guild):
    async with client.pg_con.acquire() as conn:
        await conn.execute("DELETE FROM prefixes WHERE server = $1", guild.id) 

@client.command()
@cooldown(1, 30, BucketType.default)
@commands.has_guild_permissions(manage_permissions=True)
async def changeprefix(ctx, prefix):
    if isinstance(ctx.message.channel, discord.DMChannel):
        await ctx.reply('You can\'t do that here.')
        return

    if len(prefix) > 10:
        await ctx.reply('Your prefix can only be a maximum of 10 characters.')
        return
    async with client.pg_con.acquire() as conn:
        psql = """UPDATE prefixes SET prefix = $1 WHERE server = $2"""
        await conn.execute(psql, prefix, ctx.guild.id)
        await ctx.send(f'Prefix changed to `{prefix}`.')

# ----- OTHER COMMANDS -----
@client.command(brief=None, description='Ping to see if bot is working')
async def ping(ctx):
    fmt = f"Latency is {client.latency * 1000:.2f} ms"
    embed = discord.Embed(title="Pong!", 
                          description=fmt, 
                          color=client.ayesha_blue)
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

# Create connections to the database
async def create_db_pool():
    client.pg_con = await asyncpg.create_pool(database=Links.database_name, 
                                              user=Links.database_user, 
                                              password=Links.database_password)
    client.en_dict = await asyncpg.create_pool(database="dictionary", 
                                              user=Links.database_user, 
                                              password=Links.database_password)

client.loop.run_until_complete(create_db_pool())

# Runs at bot startup to load all cogs
for filename in os.listdir(Links.cog_path):
    if filename.endswith('.py'): # see if the file is a python file
        client.load_extension(f'cogs.{filename[:-3]}')

client.run(Links.Token)