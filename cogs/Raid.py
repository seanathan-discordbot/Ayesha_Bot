import discord
import asyncio

from discord.ext import commands
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

from Utilities import Checks, AssetCreation, Links

import random

raid_bosses = (
    'Maritimialan Raiders',
    'Teh Epik Duck',
    'Crumidian Invasion',
    'Riverburn Revolt',
    'Glakelyctic Brigands',
    'Sean'
)

class Raid(commands.Cog):
    """Join a cooperative raid against a powerful enemy"""

    def __init__(self, client):
        self.client = client
        self.raid_info = {
            'Active' : False,
            'Enemy' : None,
            'HP' : None,
            'Message' : None
        }

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        #This is  the #test-channel in the Support Server (ID: 762118688567984151)
        self.client.announcement_channel = await self.client.fetch_channel(Links.announcement_channel)
        self.client.raider_role = self.client.announcement_channel.guild.get_role(Links.raider_role)
        print('Raid is ready.')

    #COMMANDS
    @commands.group(invoke_without_command=True, 
                    case_insensitive=True, 
                    description='See the current raid info. Do `raid attack` to join any active raid.')
    @commands.check(Checks.is_player)
    async def raid(self, ctx):
        """See the current raid info. Do `raid attack` to join any active raid."""
        if self.raid_info['Active']:
            await ctx.reply(f"A raid is currently being fought against {self.raid_info['Enemy']}. Do `{ctx.prefix}raid attack` to join the campaign!\n{self.raid_info['Message'].jump_url}")

        else:
            await ctx.reply(f'No raid is currently being fought. Wait for one to start in {self.client.announcement_channel.mention}!')

    @raid.command(brief='<hp>', description='Spawn a raid.')
    @commands.check(Checks.is_admin)
    async def spawn(self, ctx, hp : int):
        """`hp`: the hp of the raid you are spawning
        
        [ADMIN] Spawn a raid."""   
        #See if a raid can be spawned
        if self.raid_info['Active']:
            return await ctx.reply('A raid is currently running.', delete_after=5.0)
        if hp < 0:
            return await ctx.reply('Higher HP please.', delete_after=5.0)
        await ctx.message.delete()   

        #Set the raid info
        self.raid_info['Active'] = True
        self.raid_info['Enemy'] = random.choices(raid_bosses)[0]
        self.raid_info['HP'] = hp

        embed = discord.Embed(title = f"{self.raid_info['Enemy']} has appeared in Aramythia!",
                              description = "Only a coordinated assault from the strongest Aramythians will push them back. Use the `raid attack` command to assault it!\nEach participant will receive a cash prize when the boss is defeated, with the one who deals the final blow receiving a Legendary Weapon!",
                              color = self.client.ayesha_blue)

        self.raid_info['Message'] = await self.client.announcement_channel.send(content=f"{self.client.raider_role.mention}",
                                                                                embed=embed)

    @raid.command(description='Attack the current raid boss. The more damage you deal, the more you will be rewarded when the boss is defeated. The slayer of the boss gains a larger reward.')
    @commands.check(Checks.is_player)
    @cooldown(1, 900, BucketType.user) #15 minute cooldown
    async def attack(self, ctx):
        """Attack the current raid boss."""
        if not self.raid_info['Active']:
            ctx.command.reset_cooldown(ctx)
            return await ctx.reply(f'No raid is currently being fought. Wait for one to start in {self.client.announcement_channel.mention}!')

        # attack, crit = await AssetCreation.getAttack(self.client.pg_con, ctx.author.id)
        combat_info = await AssetCreation.get_attack_crit_hp(self.client.pg_con, ctx.author.id)

        if random.randint(1,100) > combat_info['Crit']:
            combat_info['Attack'] *= 2

        # Calculate damage and give 50% bonus for soldiers
        damage = random.randint(int(combat_info['Attack'] / 2), int(combat_info['Attack'] * 1.25))
        if await AssetCreation.getClass(self.client.pg_con, ctx.author.id) == 'Soldier':
            damage = int(damage * 1.5)

        self.raid_info['HP'] -= damage
        await AssetCreation.log_raid_attack(self.client.pg_con, ctx.author.id, damage)
        total_damage = await AssetCreation.get_player_raid_damage(self.client.pg_con, ctx.author.id)
        await ctx.reply(f"Your attack dealt {damage} damage to the {self.raid_info['Enemy']}.")
        await self.client.announcement_channel.send(f"{ctx.author.name}#{ctx.author.discriminator} dealt **{damage}** damage to the **{self.raid_info['Enemy']}**, for a total of **{total_damage}** this campaign!")

        #Do end of raid if applicable
        if self.raid_info['HP'] < 0:
            self.raid_info['HP'] = 999999 #Just in case of concurrency issues
            item_info = await AssetCreation.createItem(self.client.pg_con, 
                                                       ctx.author.id, 
                                                       attack=random.randint(90,140),
                                                       rarity='Legendary',
                                                       crit=random.randint(5,20),
                                                       returnstats=True)
            await self.raid_info['Message'].reply(f"{ctx.author.name}#{ctx.author.discriminator} dealt the finishing blow against {self.raid_info['Enemy']}. As the enemy fled, they received *{item_info['Name']}*, a legendary {item_info['Type']} (ATK: {item_info['Attack']} CRIT: {item_info['Crit']})\nEvery other participant received a small gold payment proportional to their damage dealt.")
            self.raid_info = {
                'Active' : False,
                'Enemy' : None,
                'HP' : None,
                'Message' : None
            }
            await AssetCreation.clear_raid_attacks(self.client.pg_con)

    @raid.command(description='Secret admin raid powers!')
    @commands.check(Checks.is_admin)
    async def secret(self, ctx):
        """A secret ;)"""
        await ctx.reply(self.raid_info)

def setup(client):
    client.add_cog(Raid(client)) 