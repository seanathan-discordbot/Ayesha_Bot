import discord
from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

from Utilities import PageSourceMaker

class AyeshaEmbed(discord.Embed):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.color = 0xBEDCF6

class HelpCommand(commands.Cog):
    """Bot help command."""
    
    def __init__(self, client):
        self.client = client
        
    def write_help_embed(self, ctx, start, entries, cog):
        """Return a help embed for up to 5 commands in the given list.
        
        Parameters
        ----------
        ctx: commands.Context
            the context of the command invocation
        start: int
            the index of the first value in entries being written
        entries: list
            a list of commands
        cog: str
            the name of the cog for which help is being sought

        Returns
        -------
        helpEmbed: discord.Embed
            an embed to be displayed to the user
        """
        # helpEmbed = discord.Embed(title=f'Ayesha Help: {cog}', color=self.client.ayesha_blue)
        helpEmbed = AyeshaEmbed(title=f'Ayesha Help: {cog}')
        helpEmbed.set_thumbnail(url=ctx.author.avatar_url)
        
        iteration = 0
        while start < len(entries) and iteration < 5: #Will loop until 5 entries are processed or there's nothing left in the queue
            command_info = self.write_help_for_command(entries[start])
            helpEmbed.add_field(name=command_info['name'],
                                value=command_info['help'],
                                inline=False)

            iteration += 1
            start +=1 
            
        return helpEmbed

    def write_help_for_command(self, command : commands.Command):
        """Return a dict containing the help output of a command.
        Dict: 'name': str including parent, name, and parameters
              'help': str containing description and aliases
        """
        if command.parent is None:
            parent = ''
        else:
            parent = command.parent.name + ' '

        if len(command.aliases) == 0:
            aliases = ''
        else:
            aliases = '**Aliases: **'
            for alias in command.aliases:
                aliases += f'`{alias}` '

        if len(command.signature) == 0:
            params = ''
        else:
            params = f'`{command.signature}`'

        return {
            'name' : f'{parent}{command.name} {params}',
            'help' : f'{command.help}\n{aliases}'
        }
        
    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('HelpCommand is ready.')

    #COMMANDS
    @commands.command()
    async def help(self, ctx, *, helpquery : str = None):
        """The one-stop help command for Ayesha. Do `help` to view all the cog names, then `help <cog>` to get a list of commands for that module.
        You can also do `help <command>` to get help on a specific command.
        """
        # -- GIVE MENU OF COGS --
        if helpquery is None: 
            # Gives a basic menu listing every cog name a short description (the cog's docstring)
            # Therefore this command only works if everything is well documented (which it isn't)
            cog_info = {cog.qualified_name:(cog.qualified_name, cog.description) for cog in self.client.cogs.values()}

            for name in ['Admin', 'HelpCommand', 'Vote', 'Error_Handler']:
                cog_info.pop(name) #These cogs should remain hidden from users

            embed = discord.Embed(title='Ayesha Help: Cogs', 
                                  description=f'__**Please enter **__**`{ctx.prefix}help <Module>`**__** for more info on that module**__',
                                  color=self.client.ayesha_blue)
            embed.set_thumbnail(url=ctx.author.avatar_url)
            embed.set_footer(text=f'Use the {ctx.prefix}tutorial command to get started!')

            for cog in cog_info.values():
                embed.add_field(name=cog[0], value=f"{cog[1]}")

            return await ctx.reply(embed=embed)

        # -- GIVE HELP FOR A CERTAIN COG --
        helpquery = helpquery.lower()
        cogs = {name.lower():name for name in self.client.cogs} #Get all cog names in convenient way

        if helpquery in cogs:
            listCommands = self.client.get_cog(cogs[helpquery]).get_commands()
            entries = [self.write_help_embed(ctx, i, listCommands, cogs[helpquery]) for i in range(0, len(listCommands), 5)]
            #For spacing reasons, only 5 entries will be displayed at a time --> write_help_embed() will create the embeds
                
            pages = menus.MenuPages(source=PageSourceMaker.PageMaker(entries), 
                                    clear_reactions_after=True, 
                                    delete_message_after=True)
            return await pages.start(ctx) # Outputs the cog help, else searches for a command

        # -- GIVE HELP FOR A SPECIFIC COMMAND --
        command = self.client.get_command(helpquery) #All commands should be lowercase
        if command is None:
            return await ctx.reply('No command was found')

        command_info = self.write_help_for_command(command)
        embed = discord.Embed(title=command_info['name'],
                              description=command_info['help'],
                              color=self.client.ayesha_blue)
        embed.set_thumbnail(url=ctx.author.avatar_url)
        await ctx.reply(embed=embed)

def setup(client):
    client.add_cog(HelpCommand(client))