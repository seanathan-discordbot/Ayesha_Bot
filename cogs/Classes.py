import discord
import asyncio

from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

from Utilities import Checks, AssetCreation, PageSourceMaker

occupations = {
    'Soldier' : 'You are a retainer of a local lord, trained in the discipline of swordsmanship.\nYour base character ATK is boosted by 20% and you get a bonus 10 ATK.',
    'Blacksmith' : 'You\'ve spent years as the apprentice of a hardy blacksmith, and now a master in the art of forging.\nYour weapon ATK is boosted by 10% and you get a bonus 10 ATK.',
    'Farmer' : 'You are a lowly farmer, but farming is no easy job.\nYou gain extra gravitas every day.',
    'Hunter' : 'The wild is your domain; no game unconquerable.\nYou gain double rewards from hunting.',
    'Merchant' : 'Screw you, exploiter of others\' labor.\nYou gain 50% increased income from selling items.',
    'Traveler' : 'The wild forests up north await, as do the raging seas to the south. What will you discover?\nYou gain triple gold from travel and double rewards from foraging.',
    'Leatherworker' : 'The finest protective gear, saddles, and equipment have your name on it.\nYou have 200 increased HP.',
    'Butcher' : 'Meat. What would one do without it?\nYou have double healing effectiveness.',
    'Engineer' : 'Your lord praises the seemingly impossible design of his new manor.\nYou will gain increased rewards from exclusive association commands.',
    'Scribe' : 'Despite the might of your lord, you\'ve learned a little bit about everything too.\nYou have an additional 10% crit rate.'
}

origins = {
    'Aramithea' : 'You\'re a metropolitan. Aramithea, the largest city on Rabidus, must have at least a million people, and a niche for everybody',
    'Riverburn' : 'The great rival of Aramithea; Will you bring your town to victory?',
    'Thenuille' : 'You love the sea; you love exploration; you love trade. From here one can go anywhere, and be anything',
    'Mythic Forest' : 'You come from the lands down south, covered in forest. You could probably hit a deer square between the eyes blindfolded.',
    'Sunset' : 'Nothing is more peaceful than an autumn afternoon in the prairie.',
    'Lunaris' : 'The crossroads of civilization; the battleground of those from the north, west, and east. Your times here have hardened you.',
    'Crumidia' : 'The foothills have turned you into a strong warrior. Perhaps you will seek domination over your adversaries?',
    'Maritimiala' : 'North of the mountains, the Maritimialan tribes look lustfully upon the fertile plains below. Will you seek integration, or domination?',
    'Glakelys' : 'The small towns beyond Riverburn disregard the Aramithean elite. The first line of defense from invasions from Lunaris, the Glakelys are as tribal as they were 300 years ago.'
}

occ = enumerate(occupations)
occ = list(occ)

# 8. Engineer - buff steal/invest slightly - implemented

ori = enumerate(origins)
ori = list(ori)

class Classes(commands.Cog):
    """Customize your character!"""

    def __init__(self, client):
        self.client = client
        self.client.classes = ('Soldier', # 20% bonus to character ATK; 1 gravitas daily
                                    # Command: 50% more damage from raid attack
                                    # Weapon Bonus: Spear, Sword [CODE FOUND IN AssetCreation.get_attack_crit_hp()]
                               'Blacksmith', # Double gold and materials from mine; Half cost from upgrading weapons
                                    # Command: smith - passively gain gold and weapons
                                    # Weapon Bonus: Greatsword, Gauntlets
                               'Farmer', # 4 gravitas daily
                                    # Command: farm - passively gain gold and gravitas
                                    # Weapon Bonus: Sling, Falx
                               'Hunter', # Double gold and materials from hunt
                                    # Command: raise - have a pet that gets you other things
                                    # Weapon Bonus: Bow, Javelin
                               'Merchant', # 50% increase gold from selling
                                    # Command: sail - passively gain gold and gravitas
                                    # Weapon Bonus: Dagger, Mace
                               'Traveler', # Triple gold from traveling, double materials from forage
                                    # Command: wander - passively gain any attainable item
                                    # Weapon Bonus: Staff, Javelin
                               'Leatherworker', # 250 more hp
                                    # Command: weave - passively gain gold and gravitas
                                    # Weapon Bonus: Mace, Axe
                               'Butcher', # heal double (pve and pvp)
                                    # Command: 
                                    # Weapon Bonus: Axe, Dagger
                               'Engineer', # Associations: Steal 10% of gold instead of 5, 25% buff to guild invest, gain 5 gravitas from cl usurp
                                    # Command:
                                    # Weapon Bonus: Trebuchet, Falx
                               'Scribe') # 10 Crit; 1 gravitas daily
                                    # Command: 
                                    # Weapon Bonus: Sword, Dagger

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('Classes is ready.')

    #COMMANDS
    @cooldown(1, 3600, BucketType.user)
    @commands.command(name='class', 
                      description='Choose your player class. This can be changed.')
    async def change_class(self, ctx, player_job : str = None):
        """`player_job`: the class you want to switch to. To see the list of valid classes, just do `class`.

        Choose your player class. This can be changed in the future.
        """
        if player_job is None:
            ctx.command.reset_cooldown(ctx)

            entries = []
            for job in occupations:
                embed = discord.Embed(title='Class Selection Menu', 
                                      color=self.client.ayesha_blue)
                embed.add_field(name=f'{job}: Say `{ctx.prefix}class {job}` to take this class!', 
                                value=f'{occupations[job]}')
                entries.append(embed)

            tavern = menus.MenuPages(source=PageSourceMaker.PageMaker(entries), 
                                     clear_reactions_after=True, 
                                     delete_message_after=True)
            await tavern.start(ctx)

        else:
            player_job = player_job.title()

            if player_job not in (occupations):
                return await ctx.reply(f'This is not a valid class. Please do `{ctx.prefix}class` with no arguments to see the list of classes.')

            else:
                await AssetCreation.setPlayerClass(self.client.pg_con, player_job, ctx.author.id)
                await ctx.reply(f'You are now a {player_job}!')
        
    @cooldown(1, 3600, BucketType.user)
    @commands.command(aliases=['background','birthplace'], description='Choose your birthplace.')
    async def origin(self, ctx, *, player_origin : str = None):
        """`player_origin`: Your birthplace. To see the valid areas, just do `origin`

        Choose your homeland.
        """
        if player_origin is None:
            ctx.command.reset_cooldown(ctx)

            entries = []
            for place in origins:
                embed = discord.Embed(title='Background Selection Menu', color=self.client.ayesha_blue)
                embed.add_field(name=f'{place}: Say `{ctx.prefix}origin {place}` if you like this place!', 
                                value=f'{origins[place]}')
                entries.append(embed)   

            tavern = menus.MenuPages(source=PageSourceMaker.PageMaker(entries), 
                                     clear_reactions_after=True, 
                                     delete_message_after=True)
            await tavern.start(ctx)

        else:
            player_origin = player_origin.title()

            if player_origin not in (origins):
                await ctx.reply(f'This is not a valid place. Please do `{ctx.prefix}origin` with no arguments to see the list of backgrounds.')
                return

            else:
                await AssetCreation.setPlayerOrigin(self.client.pg_con, player_origin, ctx.author.id)
                await ctx.send(f'{ctx.author.mention}, you are from {player_origin}!')

def setup(client):
    client.add_cog(Classes(client))