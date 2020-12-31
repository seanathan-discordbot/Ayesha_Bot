"""
A bunch of Misclaneous commands for testing purposes
"""
import discord
from discord.ext import commands

class Misc(commands.Cog):
    def __init__(self,client):
        self.client=client

    @commands.command()
    async def hello(self,ctx):
        await ctx.message.channel.send('Hello!')

    @commands.command()
    async def sean(self,ctx):
        await ctx.message.channel.send('Sean is short for Seanathan')

    @commands.command()
    async def echo(self,ctx, *, returnStatement):
        await ctx.send(returnStatement)

def setup(client):
    client.add_cog(Misc(client))
