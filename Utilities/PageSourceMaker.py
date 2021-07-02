import discord
from discord.ext import commands, menus

class TooManyArgs(Exception):
    pass

class NoInputGiven(Exception):
    pass

class PageMaker(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=1)

    async def format_page(self, menu, entries):
        return entries

    @staticmethod
    def write_help_for_command(command : commands.Command):
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

    @staticmethod
    def write_help_embed(ctx, start : int, entries : list, help_for : str, description : str = None):
        """Return a help embed for up to 5 commands in the given list.
            
        Parameters
        ----------
        ctx: commands.Context
            the context of the command invocation
        start: int
            the index of the first value in entries being written
        entries: list
            a list of commands
        help_for: str
            the name of the command/command group/cog for which this embed is being made

        Returns
        -------
        helpEmbed: discord.Embed
            an embed to be displayed to the user
        """
        helpEmbed = discord.Embed(title=f'Ayesha Help: {help_for}',
                                  description=description,
                                  color=ctx.bot.ayesha_blue)
        helpEmbed.set_thumbnail(url=ctx.author.avatar_url)
        helpEmbed.set_footer(text=f'Page {int(start/5)+1}/{int((len(entries)-1)/5)+1}')
        
        iteration = 0
        while start < len(entries) and iteration < 5: #Will loop until 5 entries are processed or there's nothing left in the queue
            command_info = PageMaker.write_help_for_command(entries[start])
            helpEmbed.add_field(name=command_info['name'],
                                value=command_info['help'],
                                inline=False)

            iteration += 1
            start +=1 
            
        return helpEmbed

    @staticmethod
    def paginate_help(ctx : commands.Context, command : str, help_for : str, description : str = None):
        """Return a list of help embeds for use in a PageMaker.

        Parameters
        ----------
        ctx : commands.Context
            the context of the command invocation
        command : str
            the name of the command/command group that will be searched
        help_for : str
            the command name to be displayed in the embed title, usually similar to command

        Returns
        -------
        list : list
            A list of 'discord.Embed's that display the help information for the command passed
        """
        cmds = [cmd for cmd in ctx.bot.get_command(command).walk_commands()]

        return [PageMaker.write_help_embed(ctx, i, cmds, help_for, description) for i in range(0, len(cmds), 5)]

    @staticmethod
    def number_pages(entries : list, default : str = None):
        """Add page numbers to a list of 'discord.Embed's.
        (Optional) Since this overwrites the former footer, pass any default footer text as default.
        Not necessary to use on lists that were created by PageMaker.paginate_help()
        """
        for i, embed in enumerate(entries, 1):
            footer = f"Page {i}/{len(entries)}"
            if default is not None:
                footer += f" | {default}"
            embed.set_footer(text=footer)

        return entries


