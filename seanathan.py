import discord
def commands(TOKEN):
    

    client = discord.Client()

    @client.event
    async def on_ready():
        print('We have logged in as {0.user}'.format(client))

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        if message.content.startswith('$hello'):
            await message.channel.send('Hello!')
        elif message.content.startswith('$sean'):
            await message.channel.send('Sean is short for Seanathan')
            
    client.run(TOKEN)
 
if __name__ == "__main__":
    TOKEN="NzY3MjM0NzAzMTYxMjk0ODU4.X4u8_w.NFBGhog1Mwkqf0fu-Q9FMZA1TJI"
    commands(TOKEN)
