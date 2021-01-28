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
            reward = ['acolyte']
            name=random.choice(star_data[5])
            pity = 0

        else: 
            winner=random.randint(1,101)

            #Determine if reward will be a weapon
            reward = random.choices(['weapon', 'acolyte'], [75, 25])

            #Select a random weapon or acolyte
            if winner in five_star: #If its a five star reset the pity
                if reward[0] == 'weapon':
                    item_info = await AssetCreation.createItem(self.client.pg_con, ctx.author.id, random.randint(100, 150), 'Legendary', returnstats=True)
                else:
                    name=random.choice(star_data[5])
                pity = 0
            else: #Add one to the pitycounter
                if winner in two_star:
                    if reward[0] == 'weapon':
                        item_info = await AssetCreation.createItem(self.client.pg_con, ctx.author.id, random.randint(30,60), 'Uncommon', returnstats=True)
                    else:
                        name=random.choice(star_data[2])

                elif winner in three_star:
                    if reward[0] == 'weapon':
                        item_info = await AssetCreation.createItem(self.client.pg_con, ctx.author.id, random.randint(45,90), 'Rare', returnstats=True)
                    else:
                        name=random.choice(star_data[3])

                elif winner in four_star:
                    if reward[0] == 'weapon':
                        item_info = await AssetCreation.createItem(self.client.pg_con, ctx.author.id, random.randint(75,120), 'Epic', returnstats=True)
                    else:
                        name=random.choice(star_data[4])

                elif winner in one_star:
                    if reward[0] == 'weapon': #Minimum 2 star weapons from gacha
                        item_info = await AssetCreation.createItem(self.client.pg_con, ctx.author.id, random.randint(30,60), 'Uncommon', returnstats=True)
                    else:
                        name=random.choice(star_data[1])

                pity = info['pitycounter'] + 1

        #With acolyte chosen, update rubidics and pity counter
        await AssetCreation.setPityCounter(self.client.pg_con, ctx.author.id, pity)
        rubidics = info['rubidic'] - 1
        await AssetCreation.setRubidics(self.client.pg_con, ctx.author.id, rubidics)

        #Add acolyte to inventory or add as a duplicate
        if reward[0] == 'acolyte':
            is_duplicate = await AssetCreation.checkDuplicate(self.client.pg_con, ctx.author.id, name)

            if is_duplicate is not None: #then its a dupe - add 1 to duplicate
                await AssetCreation.addAcolyteDuplicate(self.client.pg_con, is_duplicate['instance_id'])
            else: #Create a new one and add it to tavern
                await AssetCreation.createAcolyte(self.client.pg_con, ctx.author.id, name)

        #Send embed
        if reward[0] == 'acolyte':
            embed = discord.Embed(title=f"{name} ({acolyte_list[name]['Rarity']}⭐) has entered the tavern!", color=0xBEDCF6)
            if acolyte_list[name]['Image'] is not None:
                embed.set_thumbnail(url=f"{acolyte_list[name]['Image']}")
            embed.add_field(name='Attack', value=f"{acolyte_list[name]['Attack']} + {acolyte_list[name]['Scale']}/lvl")
            embed.add_field(name='Crit', value=f"{acolyte_list[name]['Crit']}")
            embed.add_field(name='HP', value=f"{acolyte_list[name]['HP']}")
            if acolyte_list[name]['Effect'] is None:
                embed.add_field(name='Effect', value=f" No effect.\n{name} uses {acolyte_list[name]['Mat']} to level up.")
            else:
                embed.add_field(name='Effect', value=f"{acolyte_list[name]['Effect']}\n{name} uses `{acolyte_list[name]['Mat']}` to level up.", inline=False)
            embed.set_footer(text=f"You have {rubidics} rubidics. You will receive a 5-star in {80-pity} summons.")
        else:
            embed = discord.Embed(title=f"You received {item_info['Name']} ({item_info['Rarity']})!", color=0xBEDCF6)
            embed.add_field(name='Type', value=f"{item_info['Type']}")
            embed.add_field(name='Attack', value=f"{item_info['Attack']}")
            embed.add_field(name='Crit', value=f"{item_info['Crit']}")
            embed.set_footer(text=f"You have {rubidics} rubidics. You will receive a 5-star in {80-pity} summons.")

        await ctx.reply(embed=embed)

    @commands.command(aliases=['rolls', 'summons'], description='See how many rubidics you have and how many more summons are needed until receiving guaranteed 5*')
    @commands.check(Checks.is_player)
    async def rubidics(self, ctx):
        info = await AssetCreation.getRubidics(self.client.pg_con, ctx.author.id)
        await ctx.reply(f"You have **{info['rubidic']}** rubidics.\nYou will get a 5⭐ weapon or acolyte in **{80-info['pitycounter']}** summons.")

def setup(client):
    client.add_cog(Gacha(client))