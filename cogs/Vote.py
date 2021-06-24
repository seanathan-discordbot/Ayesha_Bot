import discord
from discord import Webhook, AsyncWebhookAdapter
from discord.ext import commands, tasks

from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

from Utilities import Checks, AssetCreation, Links

import time
import random
import asyncio

import aiohttp
from aiohttp import web

import dbl

#WEBSOCKET        
class Vote_Handler:
    def __init__(self, bot : discord.Client):
        self.bot = bot
        self.session = aiohttp.ClientSession()

        async def webserver():
            self.app = web.Application(loop = self.bot.loop)
            self.app.router.add_get('/', self.get_handler)
            self.app.router.add_post('/vote', self.post_handler)
            runner = web.AppRunner(self.app)
            await runner.setup()
            self.site = web.TCPSite(runner, '0.0.0.0', 8081)
            await self.bot.wait_until_ready()
            await self.site.start()

        asyncio.ensure_future(webserver())

        self.bot.vote_wbhook = Webhook.from_url(Links.Pipedream_Webhook,
            adapter = AsyncWebhookAdapter(self.session))

    async def bot_list_stats(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            async with aiohttp.ClientSession() as client:
                resp = await client.post(url = f"https://discordbotlist.com/api/v1/bots/{self.bot.user.id}/stats",
                    data = {
                        "guilds" : len(self.bot.guilds),
                        "users" : await AssetCreation.getPlayerCount(self.bot.pg_con)
                    },
                    headers = {"Authorization" : Links.DBL_Token}
                    )
                print(resp.status)

            await asyncio.sleep(3600 * 24)

    async def get_handler(self, request):
        return web.Response(text='Idk what I\'m doing\n-Aramythia')

    async def post_handler(self, request):
        auth = request.headers.get('Authorization')
        print(auth)
        if f"dbl_{Links.Webhook_Secret}" == auth:
            pass
        else:
            return
        
        data = await request.json()
        self.bot.dispatch('vote', data)
        return web.Response(status=200) 

    async def on_shutdown(self):
        asyncio.ensure_future(self.site.stop())
        self.app.shutdown()
        self.app.cleanup()
        self.session.close()

class Vote(commands.Cog):
    """Small module to reward votes"""
    def __init__(self,client):
        self.client = client

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        vote_handling = Vote_Handler(self.client)
        self.update_stats = self.client.loop.create_task(vote_handling.bot_list_stats())
        print('Vote is ready.')

    @commands.Cog.listener()
    async def on_vote(self, data):
        user_id = int(data['id'])
        player = await self.client.fetch_user(user_id)

        if not await Checks.has_char(self.client.pg_con, player):
            await player.send('Thank you for voting for the bot! Create a character with `start` to receive rewards the next time you vote!')
            return

        await AssetCreation.giveRubidics(self.client.pg_con, 1, user_id)
        await player.send('Thank you for supporting me! You received a rubidic.')

    @commands.Cog.listener() #If you have an alternative DM me at Aramythia#9006
    async def on_message(self, message):
        if message.channel.id != Links.Vote_Channel:
            return

        if message.author.id != self.client.vote_wbhook.id:
            return

        player = await self.client.fetch_user(int(message.content[5:23]))

        data = {'id' : player.id}
        self.client.dispatch('vote', data)

    def cog_unload(self):
        self.update_stats.cancel()

def setup(client):
    client.dbl = dbl.DBLClient(client, Links.TOPGG_Token, autopost=True)

    client.add_cog(Vote(client))