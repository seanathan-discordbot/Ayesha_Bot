import discord 
import os 
from discord.ext import commands
Token
client=commands.Bot(command_prefix="!")

@client.command()
async def load(ctx,extension):
    client.load_extension(f'cogs.{extension}')

@client.command()
async def unload(ctx,extension):
    client.unload_extension(f'cogs.{extension}')

# Runs at bot startup to load all cogs
for filename in os.listdir(r'C:\Users\rowlas2\Documents\Seanathan\cogs'): # go into cog folder and search all files
    if filename.endswith('.py'): # see if the file is a python file
        client.load_extension(f'cogs.{filename[:-3]}') # cuts off last 3 chars
client.run(Token)



