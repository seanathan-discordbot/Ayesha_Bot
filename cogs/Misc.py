import discord
from discord.ext import commands

from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

from Utilities import Checks, AssetCreation, PageSourceMaker

import datetime
from datetime import date

import asyncio
import time
import random
import schedule

class Misc(commands.Cog):
    def __init__(self,client):
        self.client=client
        self.claimed_dailies = []

        def clearDailies():
            self.claimed_dailies.clear()

        async def checkTime():
            schedule.every().day.at("00:00").do(clearDailies)
            while True:
                schedule.run_pending()
                print(f'Checked time for reset: {date.today()}')
                await asyncio.sleep(schedule.idle_seconds())

        asyncio.ensure_future(checkTime())

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('Misc is ready.')

    #COMMANDS
    @commands.command(description='Invite Ayesha to your server!')
    async def invite(self, ctx):
        embed = discord.Embed(title='Click me to invite Ayesha to your server!',
            url = 'https://discord.com/api/oauth2/authorize?client_id=767234703161294858&permissions=70347841&scope=bot',
            color = 0xBEDCF6)
        # embed.set_image()

        await ctx.reply(embed=embed)

    @commands.command(description='Join the support server here!')
    async def support(self, ctx):
        await ctx.reply('https://discord.gg/FRTTARhN44')

    @commands.command(description='Vote for the bot to receive a rubidic!')
    async def vote(self, ctx):
        embed = discord.Embed(title='Receive 1 rubidic each time you vote for the bot, up to 4 rubidics a day!',
            description='Vote on [Top.gg!](https://top.gg/bot/767234703161294858) (12 hr cooldown)\nVote on [Discord Bot List!](https://discordbotlist.com/bots/ayesha) (12 hr cooldown)',
            color=0xBEDCF6)
        await ctx.reply(embed=embed)

    @commands.command(description='Get 2 rubidics daily!')
    @commands.check(Checks.is_player)
    # @cooldown(1, 86400, BucketType.user)
    async def daily(self, ctx):
        if ctx.author.id in self.claimed_dailies:
            await ctx.reply(f'You already claimed your daily. It will refresh in `{time.strftime("%H:%M:%S", time.gmtime(schedule.idle_seconds()))}`.')
            return
        else:
            await AssetCreation.giveRubidics(self.client.pg_con, 2, ctx.author.id)
            await ctx.reply('You received 2 rubidics!')
            self.claimed_dailies.append(ctx.author.id)
        
    @commands.command(description='Link to a place to report bugs in AyeshaBot.')
    async def report(self,ctx):
        embed=discord.Embed(title="bug reporter", url="https://github.com/seanathan-discordbot/seanathan/issues", description="If you encounter what you believe to be a bug while using our bot please report it here", color=discord.Color.red())
        await ctx.send(embed=embed)

    @commands.command(pass_context=True, aliases=['cd'], description='View any cooldowns your character has.')
    async def cooldowns(self, ctx):
        cooldowns = []
        output = ""
        for command in self.client.walk_commands():
            if command.is_on_cooldown(ctx):
                if command.get_cooldown_retry_after(ctx) >= 3600:
                    cooldowns.append((f'{command.name}', f'{time.strftime("%H:%M:%S", time.gmtime(command.get_cooldown_retry_after(ctx)))}'))
                else:
                    cooldowns.append((f'{command.name}', f'{time.strftime("%M:%S", time.gmtime(command.get_cooldown_retry_after(ctx)))}'))
        
        adv = await AssetCreation.getAdventure(self.client.pg_con, ctx.author.id)
        if adv['adventure'] is not None:
            if adv['adventure'] > int(time.time()):
                time_left = adv['adventure'] - int(time.time())
                output = f"You will arrive at `{adv['destination']}` in `{time.strftime('%H:%M:%S', time.gmtime(time_left))}`.\n"
            elif adv['destination'] == 'EXPEDITION':
                elapsed_time = int(time.time()) - adv['adventure']
                leftovers = elapsed_time % 86400
                duration = time.strftime("%H:%M:%S", time.gmtime(leftovers))
                output = f"You have been on an expedition for `{int(elapsed_time / 86400)}:{duration}`.\n"
            else:
                time_left = 0   
        else:
            time_left = 0  

        #Also see if daily has been used
        if ctx.author.id in self.claimed_dailies:
            output += f'`daily`: {time.strftime("%H:%M:%S", time.gmtime(schedule.idle_seconds()))}\n'

        #Create embed to send
        embed = discord.Embed(color=0xBEDCF6)
        if not cooldowns:
            # await ctx.reply('You have no cooldowns.')
            # return
            output += 'You have no cooldowns.'
        for cmd in cooldowns:
            output += f'`{cmd[0]}`: {cmd[1]}\n'
        embed.add_field(name=f'{ctx.author.display_name}\'s Cooldowns', value=output)
        await ctx.reply(embed=embed)

    @commands.group(aliases=['lb', 'board'], brief='<Sort: XP/PvE/PvP/Gold>', description='See the leaderboards. Do this command without any arguments for more help.', invoke_without_command=True, case_insensitive=True)
    async def leaderboard(self, ctx):
        embed = discord.Embed(title='Ayesha Help: Leaderboards', color=0xBEDCF6)
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.add_field(name = '```leaderboard xp/pve/pvp/gold```', 
            value='Invoke the leaderboard command followed by one of the options to see the top 5 players of those areas.')
        await ctx.reply(embed=embed)

    @leaderboard.command(aliases=['exp', 'xp'])
    async def experience(self, ctx):
        board = await AssetCreation.getTopXP(self.client.pg_con)
        embed = discord.Embed(title='AyeshaBot Leaderboards', color=0xBEDCF6)
        
        output = ''
        for entry in board:
            player = await self.client.fetch_user(entry[0])
            output = output + f'**{player.name}#{player.discriminator}\'s** `{entry[1]}`: Prestige `{entry[4]}`, Level `{entry[2]}`, `{entry[3]}` xp.\n'

        embed.add_field(name='Most Experienced Players', value=output)

        await ctx.reply(embed=embed)

    @leaderboard.command(aliases=['bosses', 'bounties'])
    async def pve(self, ctx):
        board = await AssetCreation.getTopBosses(self.client.pg_con)
        embed = discord.Embed(title='AyeshaBot Leaderboards', color=0xBEDCF6)
        
        output = ''
        for entry in board:
            player = await self.client.fetch_user(entry[0])
            output = output + f'**{player.name}#{player.discriminator}\'s** `{entry[1]}`: `{entry[2]}` bosses defeated.\n'

        embed.add_field(name='Most Bosses Defeated', value=output)

        await ctx.reply(embed=embed)

    @leaderboard.command(aliases=['richest', 'money'])
    async def gold(self, ctx):
        board = await AssetCreation.getTopGold(self.client.pg_con)
        embed = discord.Embed(title='AyeshaBot Leaderboards', color=0xBEDCF6)
        
        output = ''
        for entry in board:
            player = await self.client.fetch_user(entry[0])
            output = output + f'**{player.name}#{player.discriminator}\'s** `{entry[1]}`: `{entry[2]}` gold.\n'

        embed.add_field(name='Richest Players', value=output)

        await ctx.reply(embed=embed)

    @leaderboard.command()
    async def pvp(self, ctx):
        board = await AssetCreation.getTopPvP(self.client.pg_con)
        embed = discord.Embed(title='AyeshaBot Leaderboards', color=0xBEDCF6)
        
        output = ''
        for entry in board:
            player = await self.client.fetch_user(entry[0])
            output = output + f'**{player.name}#{player.discriminator}\'s** `{entry[1]}`: `{entry[2]}` battle wins.\n'

        embed.add_field(name='Greatest Combatants', value=output)

        await ctx.reply(embed=embed)

    @commands.command(description='Partake in a criminal activity. There is a chance you may become very rich. There is also the risk you get fined for lots of gold.')
    @commands.check(Checks.is_player)
    @cooldown(1, 7200, type=BucketType.user)
    async def crime(self, ctx):
        #Determine success or failure; 5% crit, 55% success, 40% failure
        result = random.choices(['critical success', 'success', 'failure'], [5, 55, 40])
        if result[0] == 'critical success':
            gain = random.randint(5, 8) / 100
        elif result[0] == 'success':
            gain = random.randint(2, 5) / 100
        else:
            gain = random.randint(10, 15) / 100 * -1

        #Calculate gold and add/withdraw a random percentage
        player_gold = await AssetCreation.getGold(self.client.pg_con, ctx.author.id)
        player_gain = int(player_gold * gain) + 1
        await AssetCreation.giveGold(self.client.pg_con, player_gain, ctx.author.id)

        #Send results
        place = ('bank', 'guild', 'blacksmith', 'quarry', 'farmer', 'merchant', 'store', 'passerby', 'prison', 'foreign trader', 'church')

        if result[0] == 'failure':
            await ctx.reply(f"Your attempt to rob a {random.choice(place)} was a {result[0]}! You were fined for `{player_gain * -1}` gold.")
        else:
            await ctx.reply(f"Your attempt to rob a {random.choice(place)} was a {result[0]}! You ran off with `{player_gain}` gold.")


def setup(client):
    client.add_cog(Misc(client))
