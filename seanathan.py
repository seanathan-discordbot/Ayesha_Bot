import discord
from discord.ext import commands
import os
import asyncio

Token
client = commands.Bot(command_prefix = '$')
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.command()
async def hello(ctx):
    await ctx.message.channel.send('Hello!')
@client.command()
async def sean(ctx):
    await ctx.message.channel.send('Sean is short for Seanathan')

@client.command()
async def delay(ctx):
    await asyncio.sleep(60)
    await ctx.message.channel.send('Delay')

@client.command()
async def echo(ctx, *, returnStatement):
    await ctx.send(returnStatement)
@client.command()
async def is_num(ctx,*,returnStatement):
    if returnStatement.isdigit()==False:
        await ctx.send('Please enter a number')
    else:
        await ctx.send(returnStatement)
        

@client.command()
async def ping(ctx):
    await ctx.send(ctx.author.mention)

@client.command() #work on this tommorow 
async def remind(ctx,*,returnStatement):
    if returnStatement.isdigit()==False:
        await ctx.send('Please enter a number')
    else:
        await ctx.send("I'll remind you in "+returnStatement)
        pause=int(returnStatement)
        await asyncio.sleep(pause)
        await ctx.send(ctx.author.mention+" your reminder")
"""
def is_owner(idNum):
    return idNum == 325080171591761921 #Sean

admins = [196465885148479489, 530760994289483790, 465388103792590878] #Ara, Demi, Bort
def is_admin(idNum):
    for i in range(len(admins)):
        if idNum == admins[i]:
            return True
"""

client.run(Token)



