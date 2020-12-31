
import discord 
import os 
from discord.ext import commands
Token
client=commands.Bot(command_prefix="!")

#allows us to load cogs that we have revised while the bot is online
@client.command()
async def load(ctx,extension):
    await ctx.message.channel.send('loaded')
    client.load_extension(f'cogs.{extension}')
 
#allows us to unload cogs that we have revised while the bot is online
@client.command()
async def unload(ctx,extension):
    await.ctx.message.send('unloaded')
    client.unload_extension(f'cogs.{extension}')

# Runs at bot startup to load all cogs
for filename in os.listdir(r'C:\Users\rowlas2\Documents\Seanathan\cogs'): #replace with your path
    if filename.endswith('.py'): 
        client.load_extension(f'cogs.{filename[:-3]}')
client.run(Token)