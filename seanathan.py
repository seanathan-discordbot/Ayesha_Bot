import discord
from discord.ext import commands
import os

client = commands.Bot(command_prefix = '$')

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message): #sean what is this
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')
    elif message.content.startswith('$sean'):
        await message.channel.send('Sean is short for Seanathan')

def is_owner(idNum):
    return idNum == 325080171591761921 #Sean

admins = [196465885148479489, 530760994289483790, 465388103792590878] #Ara, Demi, Bort
def is_admin(idNum):
    for i in range(len(admins)):
        if idNum == admins[i]:
            return True
