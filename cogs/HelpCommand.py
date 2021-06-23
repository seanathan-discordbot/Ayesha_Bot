# -*- coding: utf-8 -*-
"""
Created on Mon Oct 21 19:10:23 2020

@author: sebas
"""

import discord
from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

# **Music:** Ayesha's own music player! (it sucks)

listCogs = """`Acolytes:` Commands involving your party members
`Guilds`/`Brotherhoods`/`Colleges` Join an association for bonuses!
`Classes` Customize your character!
`Gacha` Roll for weapons and acolytes!
`Items` View your inventory and other commands involving items
`Map` Special commands for the Mayor and Comptroller
`Misc` Other Ayesha-related commands
`Profile` Create a character and view your stats!
`PvE` Basic gameplay in AyeshaBot
`PvP` Challenge your friends to battle!
`Raid` Join a cooperative raid against a common enemy
`Reminders` Simple reminders for bot commands (low capacity)
`Travel` Explore the land of Rabidus and get items for your party members!"""

class HelpPaginator(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=1)
    
    async def format_page(self, menu, entries):
        return entries

class HelpCommand(commands.Cog):
    
    def __init__(self, client):
        self.client = client
        
    def write(self, ctx, start, entries, cog):
        helpEmbed = discord.Embed(title=f'Ayesha Help: {cog}', color=self.client.ayesha_blue)
        helpEmbed.set_thumbnail(url=ctx.author.avatar_url)
        
        iteration = 0
        while start < len(entries) and iteration < 5: #Will loop until 5 entries are processed or there's nothing left in the queue
            if entries[start].brief and entries[start].aliases:
                helpEmbed.add_field(name=f'{entries[start].name} `{entries[start].brief}`', 
                                    value=f'Aliases: `{entries[start].aliases}`\n{entries[start].description}', 
                                    inline=False)
            elif entries[start].brief and not entries[start].aliases:
                helpEmbed.add_field(name=f'{entries[start].name} `{entries[start].brief}`', 
                                    value=f'{entries[start].description}', 
                                    inline=False)
            elif not entries[start].brief and entries[start].aliases:
                helpEmbed.add_field(name=f'{entries[start].name}', 
                                    value=f'Aliases: `{entries[start].aliases}`\n{entries[start].description}', 
                                    inline=False)
            else:
                helpEmbed.add_field(name=f'{entries[start].name}', 
                                    value=f'{entries[start].description}', 
                                    inline=False)
            iteration += 1
            start +=1 
            
        return helpEmbed
    
    async def createHelp(self, ctx, cog):
        entries = []
        listCommands = self.client.get_cog(cog).get_commands()
        for i in range(len(listCommands)):
            if listCommands[i].hidden:
                listCommands.pop(i)
        for j in range(0, len(listCommands), 5): #For spacing reasons, only 5 entries will be displayed at a time
            entries.append(self.write(ctx, j, listCommands, cog)) #Write will create the embeds for us
            
        pages = menus.MenuPages(source=HelpPaginator(entries), 
                                clear_reactions_after=True, 
                                delete_message_after=True)
        await pages.start(ctx)
        
    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('HelpCommand is ready.')

    #COMMANDS
    @commands.group(invoke_without_command=True, case_insensitive=True)
    async def help(self, ctx, cog : str = None):
        if not cog:
            prefix = await self.client.get_prefix(ctx.message)
            helpEmbed = discord.Embed(title='Ayesha Help', 
                                      color=self.client.ayesha_blue)
            helpEmbed.set_thumbnail(url=ctx.author.avatar_url)
            # helpEmbed.set_author(name='Ayesha Help')
            helpEmbed.add_field(
                name = f'__Please enter `{prefix}help <Module>` for more info on that module__',
                value = listCogs, inline=False #LIST THE COGS
            )
            helpEmbed.set_footer(text=f'Use the {ctx.prefix}tutorial command to get started!')
            
            embed = discord.Embed(color=self.client.ayesha_blue)
            embed.set_thumbnail(url=ctx.author.avatar_url)
            embed.set_author(name='Ayesha Help: Logistics')
            embed.add_field(name='changeprefix', #CHANGEPREFIX
                value='`changeprefix <str>`\nChanges the server prefix to <str>', 
                inline=False)   
            embed.add_field(name='ping', #PING
                value='`ping`\nSee if the bot is online.', 
                inline=False)
            embed.add_field(name='servers', #SERVERS
                value='`servers`\nSee how many servers this bot is in!', 
                inline=False)
            embed.set_footer(text='Use the tutorial command to get started!')
            
            entries = [helpEmbed, embed]
                
            pages = menus.MenuPages(source=HelpPaginator(entries), 
                                    clear_reactions_after=True, 
                                    delete_message_after=True)
            await pages.start(ctx)
        else:
            try:
                cog = cog.title()
                if cog == 'Pve':
                    cog = 'PvE'
                if cog == 'Pvp':
                    cog = 'PvP'
                await self.createHelp(ctx, cog)
            except AttributeError:
                await ctx.send("That is not a valid module.")

def setup(client):
    client.add_cog(HelpCommand(client))