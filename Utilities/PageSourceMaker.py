import discord
from discord.ext import menus

class PageMaker(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=1)

    async def format_page(self, menu, entries): #Guys I still don't understand this module
        return entries