import discord
import asyncio

from discord.ext import commands, tasks, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

from Utilities import Checks, AssetCreation, PageSourceMaker, Links

from dpymenus import Page, PaginatedMenu

import time

class Reminders(commands.Cog):

    def __init__(self, client):
        self.client = client

    @tasks.loop(seconds=10.0)
    async def checkForReminders(self):
        now = int(time.time())
        completed_reminders = await AssetCreation.get_all_reminders(self.client.pg_con, now)

        for reminder in completed_reminders:
            player = await self.client.fetch_user(reminder['user_id'])

            elapsed_time = time.strftime("%H:%M:%S", time.gmtime(int(now - reminder['starttime'])))

            await player.send(f"{elapsed_time} ago, you wanted to be reminded of:\n{reminder['content']}")

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        self.checkForReminders.start()
        print('Reminders is ready.')

    def cog_unload(self):
        self.checkForReminders.stop()

    def write(self, start, reminders, player):
        output = ''
        iteration = 0
        while start < len(reminders) and iteration < 5: #Loop til 5 entries or none left

            output += f"**ID: `{reminders[start]['id']}` | In `{time.strftime('%H:%M:%S', time.gmtime(int(reminders[start]['endtime'] - time.time())))}`:** {reminders[start]['content']}\n"
            
            iteration += 1
            start += 1

        embed = discord.Embed(title=f'{player}\'s Reminders',
            description = output,
            color = 0xBEDCF6
            )
        
        return embed

    #COMMANDS
    @commands.group(aliases=['r'], brief='<hours> <reminder>', description='Set a reminder for a few hours.', invoke_without_command=True, case_insensitive=True)
    async def remind(self, ctx, hours : float, *, content : str):
        #Make sure input is valid
        if len(content) > 100:
            await ctx.reply('Your reminder can only be up to 100 characters.')
            return
        
        if hours <= 60/3600:
            await asyncio.sleep(hours)
            await ctx.reply(f'Reminder: {content}')
            return

        #Otherwise calculate reminder length
        starttime = int(time.time())
        endtime = starttime + hours * 3600

        await AssetCreation.create_reminder(self.client.pg_con, starttime, endtime, ctx.author.id, content)

        await ctx.reply(f'Will remind you in {hours} hours.')

    @remind.command(name='list', description='See your active reminders.')
    async def _list(self, ctx):
        reminders = await AssetCreation.get_reminders_from_person(self.client.pg_con, ctx.author.id)
        
        if len(reminders) == 0:
            await ctx.reply('You have no reminders!')
            return

        remind_pages = []
        for i in range(0, len(reminders), 5): #list 5 entries at a time
            remind_pages.append(self.write(i, reminders, ctx.author.display_name)) # Write will create the embeds

        remind_list = menus.MenuPages(source=PageSourceMaker.PageMaker(remind_pages), clear_reactions_after=True, delete_message_after=True)
        await remind_list.start(ctx)

    @remind.command(aliases=['cancel', 'remove', 'stop'], brief='<id of reminder>', description='Cancel one of your reminders')
    async def delete(self, ctx, reminder_id : int):
        reminders = await AssetCreation.get_reminders_from_person(self.client.pg_con, ctx.author.id)

        for reminder in reminders:
            if reminder['id'] == reminder_id:
                await AssetCreation.delete_reminder(self.client.pg_con, reminder_id)
                await ctx.reply(f'Deleted reminder {reminder_id}.')
                return

        await ctx.reply('None of your reminders has this ID.')

    @remind.command(description='Show this command.')
    async def help(self, ctx):
        def write(ctx, entries):
            helpEmbed = discord.Embed(title=f'NguyenBot Help: Reminders', description='We created a simple reminder module to help you plan your expeditions, travels, voting, etc. We recommend using it only for these purposes, as this module is not perfect and other bots (and applications) probably have better systems for doing this. This cog however will fulfill any of your bot-related timer needs.', color=0xBEDCF6)
            helpEmbed.set_thumbnail(url=ctx.author.avatar_url)

            for cmd in entries:
                if cmd.brief and cmd.aliases:
                    helpEmbed.add_field(name=f'{cmd.name} `{cmd.brief}`', value=f'Aliases: `{cmd.aliases}`\n{cmd.description}', inline=False)
                elif cmd.brief and not cmd.aliases:
                    helpEmbed.add_field(name=f'{cmd.name} `{cmd.brief}`', value=f'{cmd.description}', inline=False)
                elif not cmd.brief and cmd.aliases:
                    helpEmbed.add_field(name=f'{cmd.name}', value=f'Aliases: `{cmd.aliases}`\n{cmd.description}', inline=False)
                else:
                    helpEmbed.add_field(name=f'{cmd.name}', value=f'{cmd.description}', inline=False)
                
            return helpEmbed

        cmds = []
        cmds.append(self.client.get_command('remind'))
        for command in self.client.get_command('remind').walk_commands():
            cmds.append(command)
        
        helpEmbed = write(ctx, cmds)

        await ctx.reply(embed=helpEmbed)




def setup(client):
    client.add_cog(Reminders(client))