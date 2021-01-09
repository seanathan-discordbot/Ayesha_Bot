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
        
    @commands.command(brief=None, description='Ping to see if bot is working')
    async def ping(self, ctx):
        embed = discord.Embed(title="Pong!", description=f"Latency is {self.client.latency * 1000:.2f} ms", color=0xBEDCF6)
        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(Misc(client))
