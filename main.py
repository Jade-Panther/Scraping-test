import discord
import os

print(os.getenv("DISCORD_TOKEN"))
TOKEN = os.getenv("DISCORD_TOKEN")
USER_ID = int(os.getenv("USER_ID"))  

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

        # Fetch the user object by ID
        user = await self.fetch_user(USER_ID)
        if user:
            try:
                await user.send("Hello! This is a DM from your bot.")  # Sends DM
                print(f"Sent a DM to {user.name}")
            except Exception as e:
                print(f"Failed to send DM: {e}")
        else:
            print("User not found.")

    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')
        # Example: reply to a user in DM
        if message.content.lower() == "ping":
            await message.author.send("Pong! (DM)")

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(TOKEN)