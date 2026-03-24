import discord
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
USER_ID = int(os.getenv("USER_ID"))

print("TOKEN:", TOKEN)
print("USER_ID:", USER_ID)

intents = discord.Intents.default()
intents.message_content = True

class MyClient(discord.Client):
    async def on_ready(self):
        print(f"Logged in as {self.user}!")
        user = await self.fetch_user(USER_ID)
        await user.send("Hello! This is a DM from your bot.")

    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.content.lower() == "hi":
            await message.channel.send(f"Hello {message.author.name}!")
        if message.content.lower() == "ping":
            await message.author.send("Pong! (DM)")

client = MyClient(intents=intents)
client.run(TOKEN)