"""
A remind command for a discord bot and some commands that build up to it
"""
import discord
from discord.ext import commands
import asyncio

def seconds(a):
    first = ''
    seconds=0
    for char in a:
        if char.isdigit():
            first += char
        if char.isalpha():
            first = int(first)
            if char=='h':
                seconds+=(first*60)*60
                first=''
            elif char=='m':
                seconds+=first*60
                first=''
            elif char=='s':
                seconds+=first
                first=''
    return seconds

class Remind(commands.Cog):
    def __init__(self,client):
        self.client=client

    @commands.command()
    async def delay(self,ctx):
        await asyncio.sleep(60)
        await ctx.message.channel.send('Delay')


    @commands.command()
    async def is_num(self,ctx,*,returnStatement):
        if returnStatement.isdigit()==False:
            await ctx.send('Please enter a number')
        else:
                await ctx.send(returnStatement)

    @commands.command()
    async def mention(self,ctx):
        await ctx.send(ctx.author.mention)

    @commands.command() #work on this tommorow
    async def remind(self,ctx,*,returnStatement):
            await ctx.send("I'll remind you in "+returnStatement)
            pause=seconds(returnStatement)
            await asyncio.sleep(pause)
            await ctx.send(ctx.author.mention+" your reminder")

def setup(client):
    client.add_cog(Remind(client))
