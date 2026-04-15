import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
import random
from helpers.naturalist import *
from cogs.game import *
from database.manager import *

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
USER_ID = int(os.getenv("USER_ID"))

inat = INatClient()
lat, lng = 39.1928853, -76.7241371
radius = 100

intents = discord.Intents.default()
intents.message_content = True


class DiscordBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
        )
        self.db = DataManager(f"{os.path.realpath(os.path.dirname(__file__))}/database/data.db")

    async def setup_hook(self):
        """
        This runs before the bot connects
        """
        await self.db.connect()
        await self.db.setup()

        for file in os.listdir("./cogs"):
            if file.endswith(".py"):
                await self.load_extension(f"cogs.{file[:-3]}")
                print(f"Loaded cog: {file}")

        self.database = DataManager(
            connection=await aiosqlite.connect(
                f"{os.path.realpath(os.path.dirname(__file__))}/database/data.db"
            )
        )

        await self.tree.sync()

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.lower() == 'ping':
            await message.author.send('Pong! (DM)')

        await self.process_commands(message)

    async def on_ready(self):
        print(f"Logged in as {self.user}")

bot = DiscordBot()
bot.run(TOKEN)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")