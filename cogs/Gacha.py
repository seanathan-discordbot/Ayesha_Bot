import discord

import json

from Utilities import Checks, AssetCreation, Links
from discord.ext import commands

import asyncpg

import random
import ayesha

#Randomize at bot startup
l=list(range(1,101))
random.shuffle(l)
two_star=l[0:60]
three_star=l[60:95]
four_star=l[95:98]
one_star=[l[98]]
five_star=[l[99]]

class Gacha(commands.Cog):
    def __init__(self,client):
        self.client=client

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('Gacha is ready.')

    #COMMANDS
    # @commands.command()
    # @commands.check(ayesha.is_admin)
    # async def add(self, ctx, returnStatement):
    #     acolyte=returnStatement
    #     await AssetCreation.createAcolyte(self.client.pg_con, ctx.author.id, acolyte)

    @commands.command(aliases=['summon'], description='Spend 1 rubidic to get a random acolyte or weapon!')
    @commands.check(Checks.is_player)
    async def roll(self,ctx):
        #Make sure they have rubidics
        info = await AssetCreation.getRubidics(self.client.pg_con, ctx.author.id)
        if info['rubidic'] < 1:
            await ctx.reply(f"You don\'t have any rubidics to summon. Do `daily` or level up to get some!")
            return
        #Load the list of acolytes
        with open(Links.acolyte_list) as f:
            acolyte_list=json.load(f) #This stores all the acolytes' info
            star_data=dict() #This sorts all the acolytes by their rarity
            for key in acolyte_list:
                if acolyte_list[key]["Rarity"] not in star_data:
                    star_data[acolyte_list[key]['Rarity']]=[key]
                else:
                    star_data[acolyte_list[key]['Rarity']].append(key)

        #Check to see if player has reached pity
        if info['pitycounter'] >= 80:
            name=random.choice(star_data[5])
            pity = 0

        else: 
            winner=random.randint(1,101)

            #Otherwise select a random acolyte
            if winner in five_star: #If its a five star reset the pity
                name=random.choice(star_data[5])
                pity = 0

            else: #Add one to the pitycounter

                if winner in two_star:
                    name=random.choice(star_data[2])

                elif winner in three_star:
                    name=random.choice(star_data[3])

                elif winner in four_star:
                    name=random.choice(star_data[4])

                elif winner in one_star:
                    name=random.choice(star_data[1])

                pity = info['pitycounter'] + 1

        #With acolyte chosen, update rubidics and pity counter
        await AssetCreation.setPityCounter(self.client.pg_con, ctx.author.id, pity)
        rubidics = info['rubidic'] - 1
        await AssetCreation.setRubidics(self.client.pg_con, ctx.author.id, rubidics)

        #Add acolyte to inventory or add as a duplicate
        is_duplicate = await AssetCreation.checkDuplicate(self.client.pg_con, ctx.author.id, name)

        if is_duplicate is not None: #then its a dupe - add 1 to duplicate
            await AssetCreation.addAcolyteDuplicate(self.client.pg_con, is_duplicate['instance_id'])
        else: #Create a new one and add it to tavern
            await AssetCreation.createAcolyte(self.client.pg_con, ctx.author.id, name)

        #Send embed
        embed = discord.Embed(title=f"{name} ({acolyte_list[name]['Rarity']}⭐) has entered the tavern!", color=0xBEDCF6)
        embed.set_thumbnail(url='https://i.imgur.com/doAL3RB.jpg')
        embed.add_field(name='Attack', value=f"{acolyte_list[name]['Attack']} + {acolyte_list[name]['Scale']}/lvl")
        embed.add_field(name='Crit', value=f"{acolyte_list[name]['Crit']}")
        embed.add_field(name='HP', value=f"{acolyte_list[name]['HP']}")
        if acolyte_list[name]['Effect'] is None:
            embed.add_field(name='Effect', value=f" No effect.\n{name} uses {acolyte_list[name]['Mat']} to level up.")
        else:
            embed.add_field(name='Effect', value=f"{acolyte_list[name]['Effect']}\n{name} uses `{acolyte_list[name]['Mat']}` to level up.", inline=False)
        embed.set_footer(text=f"You have {rubidics} rubidics. You will receive a 5-star in {80-pity} summons.")

        await ctx.reply(embed=embed)

    @commands.command(aliases=['rolls', 'summons'], description='See how many rubidics you have and how many more summons are needed until receiving guaranteed 5*')
    @commands.check(Checks.is_player)
    async def rubidics(self, ctx):
        info = await AssetCreation.getRubidics(self.client.pg_con, ctx.author.id)
        await ctx.reply(f"You have **{info['rubidic']}** rubidics.\nYou will get a 5⭐ weapon or acolyte in **{80-info['pitycounter']}** summons.")

def setup(client):
    client.add_cog(Gacha(client))