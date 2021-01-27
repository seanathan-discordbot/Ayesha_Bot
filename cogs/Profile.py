import discord
import asyncio

from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

from dpymenus import Page, PaginatedMenu

from Utilities import Checks, AssetCreation

import math

class YesNo(menus.Menu):
    def __init__(self, ctx, embed):
        super().__init__(timeout=15.0, delete_message_after=True)
        self.embed = embed
        self.result = None
        
    async def send_initial_message(self, ctx, channel):
        return await channel.send(embed=self.embed)
    
    async def prompt(self, ctx):
        await self.start(ctx, wait=True)
        return self.result
    
    @menus.button('\u2705') # Check mark
    async def on_yes(self, payload):
        self.result = True
        self.stop()
        
    @menus.button('\u274E') # X
    async def on_no(self, payload):
        self.result = False
        self.stop() 

class Profile(commands.Cog):

    def __init__(self, client):
        self.client = client

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('Profile is ready.')

    #COMMANDS
    @commands.command(aliases=['begin','create'], brief='<name : str>', description='Start the game of AyeshaBot.')
    @commands.check(Checks.not_player)
    async def start(self, ctx, *, name : str = None):
        if not name:
            name = ctx.author.display_name
        if len(name) > 32:
                await ctx.send("Name can only be up to 32 characters")
        else:
            prefix = await self.client.get_prefix(ctx.message)
            embed = discord.Embed(title='Start the game of AyeshaBot?', color=0xBEDCF6)
            embed.add_field(name=f'Your Name: {name}', value=f'You can customize your name by doing `{prefix}start <name>`')
            start = await YesNo(ctx, embed).prompt(ctx)
            if start:
                await ctx.send(f'Your Name: {name}')
                await AssetCreation.createCharacter(self.client.pg_con, ctx.author.id, name)
                await ctx.reply("Success! Use the `tutorial` command to get started!")  

    @commands.command(aliases=['p'], description='View your profile')
    async def profile(self, ctx, player : commands.MemberConverter = None):
        # Make sure targeted person is a player
        if player is None: #return author profile
            if not await Checks.has_char(self.client.pg_con, ctx.author):
                await ctx.reply('You don\'t have a character. Do `start` to make one!')
                return
            else:
                player = ctx.author
        else:
            if not await Checks.has_char(self.client.pg_con, player):
                await ctx.reply('This person does not have a character')
                return
        # Otherwise target is a player and we can access their profile
        attack, crit = await AssetCreation.getAttack(self.client.pg_con, player.id)
        character = await AssetCreation.getPlayerByID(self.client.pg_con, player.id)

        #Calc pvp and boss wins. If 0, hardcode to 0 to prevent div 0
        if character['pvpfights'] == 0: 
            pvpwinrate = 0
        else:
            pvpwinrate = character['pvpwins']/character['pvpfights']*100
        if character['bossfights'] == 0:
            bosswinrate = 0
        else:
            bosswinrate = character['bosswins']/character['bossfights']*100

        try:
            item = await AssetCreation.getEquippedItem(self.client.pg_con, player.id)
            item = await AssetCreation.getItem(self.client.pg_con, item)
        except TypeError:
            item = None

        if character['Guild'] is not None:
            guild = await AssetCreation.getGuildByID(self.client.pg_con, character['Guild'])
        else:
            guild = {'Name' : 'None'}

        #Create the strings for acolytes
        if character['Acolyte1'] is not None:
            acolyte1 = await AssetCreation.getAcolyteByID(self.client.pg_con, character['Acolyte1'])
            acolyte1 = f"{acolyte1['Name']} ({acolyte1['Rarity']}⭐)"
        else:
            acolyte1 = None

        if character['Acolyte2'] is not None:   
            acolyte2 = await AssetCreation.getAcolyteByID(self.client.pg_con, character['Acolyte2'])
            acolyte2 = f"{acolyte2['Name']} ({acolyte2['Rarity']}⭐)"
        else:
            acolyte2 = None

        #Create Embed
        embed = discord.Embed(title=f"{player.display_name}\'s Profile: {character['Name']}", color=0xBEDCF6)
        embed.set_thumbnail(url=f'{player.avatar_url}')
        embed.add_field(
            name='Character Info',
            value=f"Gold: `{character['Gold']}`\nClass: `{character['Class']}`\nOrigin: `{character['Origin']}`\nLocation: `{character['Location']}`\nAssociation: `{guild['Name']}`",
            inline=True)
        embed.add_field(
            name='Character Stats',
            value=f"Level: `{character['Level']}`\nAttack: `{attack}`\nCrit: `{crit}%`\nPvP Winrate: `{pvpwinrate:.0f}%`\nBoss Winrate: `{bosswinrate:.0f}%`",
            inline=True)
        if item is not None:
            embed.add_field(
                name='Party',
                value=f"Item: `{item['Name']} ({item['Rarity']})`\nAcolyte: `{acolyte1}`\nAcolyte: `{acolyte2}`",
                inline=True)
        else:
            embed.add_field(
                name='Party',
                value=f"Item: `None`\nAcolyte: `{acolyte1}`\nAcolyte: `{acolyte2}`",
                inline=True)
        
        await ctx.reply(embed=embed)

    @commands.command(aliases=['xp'], description='Check your xp and level.')
    @commands.check(Checks.is_player)
    async def level(self, ctx):
        level, xp = await AssetCreation.getPlayerXP(self.client.pg_con, ctx.author.id)
        tonext = math.floor(6000000 * math.cos(((level+1)/64)+3.14) + 6000000) - xp

        embed = discord.Embed(color=0xBEDCF6)
        embed.add_field(name='Level', value=f'{level}')
        embed.add_field(name='EXP', value=f'{xp}')
        embed.add_field(name=f'EXP until Level {level+1}', value=f'{tonext}')
        await ctx.reply(embed=embed)

    @commands.command(brief='<name>', description='Change your character name.')
    @commands.check(Checks.is_player)
    async def rename(self, ctx, *, name):
        if len(name) > 32:
            await ctx.reply('Name max 32 characters.')
            return
        await AssetCreation.setPlayerName(self.client.pg_con, ctx.author.id, name)
        await ctx.reply(f'Name changed to `{name}`.')

    #Add a tutorial command at the end of alpha
    @commands.group(description='Learn the game.', case_insensitive=True, invoke_without_command=True)
    async def tutorial(self, ctx):
        with open(r"F:\OneDrive\Ayesha\Assets\Tutorial.txt", "r") as f:
            tutorial = f.readlines()

        embed1 = Page(title='Ayesha Tutorial', color=0xBEDCF6)
        embed1.add_field(name='Welcome to Ayesha Alpha!', value=f"{tutorial[2]}\n{tutorial[3]}\n{tutorial[4]}")

        embed2 = Page(title='Ayesha Tutorial', color=0xBEDCF6)
        embed2.add_field(name='Intro to PvE', value=f'{tutorial[7]}\n{tutorial[8]}\n{tutorial[9]}\n{tutorial[10]}')

        embed3 = Page(title='Ayesha Tutorial', color=0xBEDCF6)
        embed3.add_field(name='Intro to Gacha', value=f'{tutorial[13]}\n{tutorial[14]}')

        menu = PaginatedMenu(ctx)
        menu.add_pages([embed1, embed2, embed3])
        menu.set_timeout(60)
        menu.show_command_message()

        await menu.open()

    @tutorial.command(aliases=['acolyte'], description='Learn more about Acolytes!')
    async def Acolytes(self, ctx):
        with open(r"F:\OneDrive\Ayesha\Assets\Tutorial.txt", "r") as f:
            tutorial = f.readlines()

        embed1 = Page(title='Ayesha Tutorial: Acolytes', color=0xBEDCF6)
        embed1.add_field(name='Welcome to Ayesha Alpha!', value=f"{tutorial[17]}\n{tutorial[18]}\n{tutorial[19]}")

        embed2 = Page(title='Ayesha Tutorial: Acolytes', color=0xBEDCF6)
        embed2.add_field(name='The Tavern and Effects', value=f'{tutorial[22]}\n{tutorial[23]}')

        embed3 = Page(title='Ayesha Tutorial: Acolytes', color=0xBEDCF6)
        embed3.add_field(name='Strengthening your Acolytes', value=f'{tutorial[27]}\n{tutorial[28]}\n{tutorial[29]}\n{tutorial[30]}')

        menu = PaginatedMenu(ctx)
        menu.add_pages([embed1, embed2, embed3])
        menu.set_timeout(60)
        menu.show_command_message()

        await menu.open()

    @tutorial.command(aliases=['item', 'weapon', 'weapons'], description='Learn more about Items!')
    async def Items(self, ctx):
        with open(r"F:\OneDrive\Ayesha\Assets\Tutorial.txt", "r") as f:
            tutorial = f.readlines()

        embed1 = discord.Embed(title='Ayesha Tutorial: Items', color=0xBEDCF6)
        embed1.add_field(name='Everything on Items', value=f"{tutorial[33]}\n{tutorial[34]}\n{tutorial[35]}\n{tutorial[36]}")

        await ctx.reply(embed=embed1)

    @tutorial.command(description='Learn more about PvE!')
    async def pve(self, ctx):
        with open(r"F:\OneDrive\Ayesha\Assets\Tutorial.txt", "r") as f:
            tutorial = f.readlines()

        embed1 = discord.Embed(title='Ayesha Tutorial: PvE', color=0xBEDCF6)
        embed1.add_field(name='Everything on PvE', value=f"{tutorial[39]}\n{tutorial[40]}\n{tutorial[41]}\n{tutorial[42]}\n{tutorial[43]}")

        await ctx.reply(embed=embed1)

    @tutorial.command(description='Learn more about Travel!')
    async def Travel(self, ctx):
        with open(r"F:\OneDrive\Ayesha\Assets\Tutorial.txt", "r") as f:
            tutorial = f.readlines()

        embed1 = discord.Embed(title='Ayesha Tutorial: Travel', color=0xBEDCF6)
        embed1.add_field(name='Everything on Travel', value=f"{tutorial[46]}\n{tutorial[47]}\n{tutorial[48]}")

        await ctx.reply(embed=embed1)

def setup(client):
    client.add_cog(Profile(client))