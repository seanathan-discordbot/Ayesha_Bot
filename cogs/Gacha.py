import discord
import random
import json
from Utilities  import AssetCreation
from discord.ext import commands
import aiosqlite


class Gacha(commands.Cog):
    def __init__(self,client):
        self.client=client
    @commands.command()
    async def add(self,ctx,returnStatement):
        id=ctx.author.id
        acolyte=returnStatement
        await AssetCreation.createAcolyte(id,acolyte)

    @commands.command()
    async def roll(self,ctx):
        with open(r'ACOLYTE_PATH') as f:
            data=json.load(f)
            star_data=dict()
            for key in data:
                if data[key]["Rarity"] not in star_data:
                    star_data[data[key]['Rarity']]=[key]
                else:
                    star_data[data[key]['Rarity']].append(key)
        l=list(range(1,101))
        random.shuffle(l)

        two_star=l[0:60]

        three_star=l[60:95]

        four_star=l[95:98]

        one_star=[l[98]]

        five_star=[l[99]]

        winner=random.randint(1,101)

        if winner in two_star:
            name=star_data[2][0]

        elif winner in three_star:
            name=star_data[3][random.randint(0,1)]

        elif winner in four_star:
            name=star_data[4][random.randint(0,3)]

        elif winner in five_star:
            name=star_data[5][random.randint(0,2)]

        elif winner in one_star:
            name=star_data[1][0]

        id=ctx.author.id
        await AssetCreation.createAcolyte(id,name)
        await ctx.message.channel.send(name)

def setup(client):
    client.add_cog(Gacha(client))
