import discord
def commands(TOKEN):


    client = discord.Client()




TOKEN
    client = discord.Client()

client = discord.Client()

    @client.event
    async def on_ready():
        print('We have logged in as {0.user}'.format(client))

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')
    elif message.content.startswith('$sean'):
        await message.channel.send('Sean is short for Seanathan')
client.run(TOKEN)

        if message.content.startswith('$hello'):
            await message.channel.send('Hello!')
        elif message.content.startswith('$sean'):
            await message.channel.send('Sean is short for Seanathan')
     @client.command(aliases=['bs','bull'])
        async def bullshit(ctx):
        await ctx.send('https://i.imgur.com/yk3hiuc.png') 
    client.run(TOKEN)

 
if __name__ == "__main__":
    TOKEN
    commands(TOKEN)



