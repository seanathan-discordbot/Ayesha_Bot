# -*- coding: utf-8 -*-
"""
Created on Fri Dec 19 2020

@author: sebas
"""

import discord
import asyncio
from async_timeout import timeout
from discord.ext import commands
from discord.ext import menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown
import youtube_dl
import time

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

dashes = []
for i in range(0,20):
    dashes.append("".join(["▬"]*i))

class YTDLSource(discord.PCMVolumeTransformer): #taken from examples
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        try:
            if 'entries' in data:
                # take first item from a playlist
                data = data['entries'][0]
        except IndexError:
            return "Nothing found"

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
    
class MusicQueue:
    def __init__(self, ctx):
        self.serverBot = ctx.bot
        self.server = ctx.guild
        self.queue = asyncio.Queue()
        self.next = asyncio.Event()
        self.vc = ctx.voice_client
        self._cog = ctx.cog
        self.reqchannel = ctx.channel
        
        self.queueInput = None
        self.source = None
        
        self.pQueue = [] # This stores all the same stuff as queue but in a way I am familiar with accessing

        ctx.bot.loop.create_task(self.player_loop(self.server))
        
    async def player_loop(self, guild):
        """This stores the AudioSources and plays them when needed.
        This is the queue. It will loop infinitely and play the audiosources in order."""
        await self.serverBot.wait_until_ready()

        while not self.serverBot.is_closed():
            self.next.clear()

            try:
                async with timeout(30):  # Waits 30 secs for song before leaving
                    self.queueInput = await self.queue.get()
                    self.source = self.queueInput.audioSource
            except asyncio.TimeoutError:
                #Remove the server queue and disconnect from vc
                return self.destroy(self.server)

            self.server.voice_client.play(self.source, after=lambda _: self.serverBot.loop.call_soon_threadsafe(self.next.set))
            self.queueInput.timer = time.time()
            self.pQueue.pop(0)
            
            await self.reqchannel.send(embed=self.nextplay(self.source))
            await self.next.wait() #Wait for song to finish before going to next
            
    def nextplay(self, audioSource):
        embed = discord.Embed(color=0xBEDCF6)
        embed.set_thumbnail(url=f"{audioSource.data['thumbnail']}")
        embed.add_field(name="Now Playing", value=f"""
                        [{audioSource.title}]({audioSource.data['webpage_url']})
                        From {audioSource.data['uploader']}""", 
                        inline=False)
        embed.set_footer(text=f"Requested by {self.queueInput.requester}")
        return embed               
    
    def destroy(self, guild):
        return self.serverBot.loop.create_task(self._cog.cleanup(guild))
    
    def getQueue(self):
        return self.queueInput

class QueueInput: #holds the audiosource and requester for future use
    def __init__(self, ctx, audioSource, requester):
        self.audioSource = audioSource
        self.requester = requester
        self.timer = None

class Music(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.serverqueues = {}

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('Music is ready.')
        
    #INVISIBLE STUFF
    
    def timerString(self, ctx, elapsed, duration):
        fraction = int(elapsed * 20 / duration)
        timerStr = dashes[fraction]+"X"+dashes[19-fraction]
        return timerStr
    
    def npEmbed(self, ctx, player):
        sean = time.time() - player.timer
        elapsed = time.strftime("%M:%S", time.gmtime(sean))
        length = time.strftime("%M:%S", time.gmtime(player.audioSource.data['duration']))
        timerStr = self.timerString(ctx, sean, player.audioSource.data['duration'])
        
        embed = discord.Embed(color=0xBEDCF6)
        embed.set_thumbnail(url=f"{player.audioSource.data['thumbnail']}")
        embed.add_field(name="Now Playing", value=f"""
                        [{player.audioSource.title}]({player.audioSource.data['webpage_url']})
                        From {player.audioSource.data['uploader']}
                        
                        `{timerStr}`
                        Duration: `{elapsed} / {length}`""", 
                        inline=False)
        embed.set_footer(text=f"Requested by {player.requester}")
        return embed
        
    def queueEmbed(self, ctx, player):
        length = time.strftime("%M:%S", time.gmtime(player.audioSource.data['duration']))
        embed = discord.Embed(color=0xBEDCF6)
        embed.set_thumbnail(url=f"{player.audioSource.data['thumbnail']}")
        embed.add_field(name="Added to Queue", value=f"""
                        [{player.audioSource.title}]({player.audioSource.data['webpage_url']})
                        From {player.audioSource.data['uploader']}
                        
                        Duration: `{length}`""", 
                        inline=False)
        embed.set_footer(text=f"Requested by {player.requester}")
        return embed
    
    def write(self, ctx, start, player):
        embed = discord.Embed(color=0xBEDCF6)
        embed.set_thumbnail(url=f"{player[start].audioSource.data['thumbnail']}")
        
        iteration = 0
        duration = 0
        while start < len(player) and iteration < 5: #Will loop until 5 entries are processed or there's nothing left in the queue
            length = time.strftime("%M:%S", time.gmtime(player[start].audioSource.data['duration']))
            duration += player[start].audioSource.data['duration']
            embed.add_field(
                name = f"{player[start].audioSource.title}",
                value = f"By `{player[start].audioSource.data['uploader']}`\nLength: `{length}`\nAdded by `{player[start].requester}`",
                inline = False
                )
            iteration += 1
            start +=1 
        if duration < 3600:
            duration = time.strftime("%M:%S", time.gmtime(duration))
        else:
            duration = time.strftime("%H:%M:%S", time.gmtime(duration))
        if len(player) > 1:
            embed.set_footer(text=f"Total length of this queue is {len(player)} songs, {duration}")
        else:
            embed.set_footer(text=f"Total length of this queue is {len(player)} song, {duration}")
        return embed
    
#    def listQueueEmbed(self, ctx, pQueue):
#        lengths = []
#        for i in range(len(pQueue)):
#            lengths.append(time.strftime("%M:%S", time.gmtime(pQueue[i].audioSource.data['duration'])))
#
#        embed = discord.Embed(color=0xBEDCF6)
#        embed.set_thumbnail(url=f"{pQueue[0].audioSource.data['thumbnail']}")
#        embed.set_footer(text=f"Queue only displays up to 10 entries.")
#        for i in range(10 if len(pQueue)>10 else len(pQueue)):
#            embed.add_field(name=f"{i+1}: {pQueue[i].audioSource.title}", value=f"""
#                            By `{pQueue[i].audioSource.data['uploader']}`
#                            Length: `{lengths[i]}`
#                            Added by `{pQueue[i].requester}`""", 
#                            inline=False)
#        return embed
        
    def getServerQueue(self, ctx):
        #Get the player for the server
        try:
            squeue = self.serverqueues[ctx.guild.id]
        except KeyError: #If there is no source, make one
            squeue = MusicQueue(ctx)
            self.serverqueues[ctx.guild.id] = squeue
        return squeue
    
    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.serverqueues[guild.id]
        except KeyError:
            pass

    #COMMANDS
    @commands.command(pass_context=True)
    async def play(self, ctx, *, url):
        #Will join vc from joinVoice function
        #await ctx.send("Joined vc")
        if not ctx.author.voice: #Don't let them query even if they're not in vc
            return
        
        serverQueue = self.getServerQueue(ctx)
        #await ctx.send("queue loaded")
        
        audioSource = await YTDLSource.from_url(url, loop=self.client.loop, stream=False)
        #await ctx.send("created audiosource")
        
        if isinstance(audioSource, str):
            await ctx.send("Nothing found. Please try again.")
        else:
        
            player = QueueInput(ctx, audioSource, ctx.message.author)
        
            await serverQueue.queue.put(player)
            serverQueue.pQueue.append(player)
            await ctx.send(embed = self.queueEmbed(ctx, player))
        
    @commands.command(name='leave', aliases = ["stop"], description='leave')
    async def leave(self, ctx):
        if ctx.voice_client:
#            await ctx.voice_client.disconnect() # I realize now that I am an idiot
            await self.cleanup(ctx.guild)
        else:
            await ctx.send("wyd")
            
    @commands.command()
    async def pause(self, ctx):
        if  ctx.voice_client.is_playing():
            ctx.voice_client.pause()
        elif ctx.voice_client.is_paused():
            ctx.voice_client.resume()       
        else:
            await ctx.send("yeet")

    @commands.command()
    async def resume(self, ctx):
        if ctx.voice_client.is_paused():
            ctx.voice_client.resume()
        else:
            await ctx.send("Nothing to unpause")
            
    @commands.command()
    async def skip(self, ctx):
        if not ctx.voice_client:
            await ctx.send("I refuse.")
        elif ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            ctx.voice_client.stop()
            await ctx.send("Skipped.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("Skipped.")
        else:
            await ctx.send("I am confused.")
        
    @commands.command(aliases = ['np','nowplaying'])
    async def now_playing(self, ctx):
        if not ctx.voice_client:
            await ctx.send("Not in a vc")
        else:
            player = self.getServerQueue(ctx)
            await ctx.send(embed=self.npEmbed(ctx, player.queueInput))
            
#    @commands.command()
#    async def queue(self,ctx):
#        if not ctx.voice_client:
#            await ctx.send("Not in a vc")
#        else:    
#            serverQueue = self.getServerQueue(ctx)
#            if serverQueue.queue.empty():
#                await ctx.send("No q")
#            else:
#                embed = self.listQueueEmbed(ctx, serverQueue.pQueue) 
#                await ctx.send(embed=embed)
#                
#
#        return embed           
                
    @commands.command(aliases=['q','songs'])
    async def queue(self, ctx):
        if not ctx.voice_client:
            await ctx.send("I am not in a voice channel.")
        else:
            serverQueue = self.getServerQueue(ctx)
            if serverQueue.queue.empty():
                await ctx.send("No songs queued. Use `play` to add one!")
            else:
                queue = []
                for i in range(0, len(serverQueue.pQueue), 5): #For spacing reasons, only 5 entries will be displayed at a time
                    queue.append(self.write(ctx, i, serverQueue.pQueue)) #Write will create the embeds for us
    
                pages = menus.MenuPages(source=QueuePager(queue), clear_reactions_after=True, delete_message_after=True)
                await pages.start(ctx)
        
    @play.before_invoke
    async def joinVoice(self, ctx):
        if not ctx.author.voice: #If the author is not in a vc tell him to join
            await ctx.send("Join a voice channel that I have access to.")
        else: 
            if ctx.voice_client is None: #Join the vc the author is in
                await ctx.author.voice.channel.connect()
            else: #Move to the vc that the author is in
                await ctx.voice_client.move_to(ctx.author.voice.channel)
                
class QueuePager(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=1)

    async def format_page(self, menu, entries): #Guys I still don't understand this module
        return entries


def setup(client):
    client.add_cog(Music(client))  