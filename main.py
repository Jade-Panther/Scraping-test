import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
from suggestion import *

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
USER_ID = int(os.getenv("USER_ID"))


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")
    user = await bot.fetch_user(USER_ID)
    await user.send("Hello! This is a DM from your bot.")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

@bot.command()
async def hi(ctx):
    await ctx.send(f"Hello {ctx.author.name}!")

@bot.command()
async def info(ctx):
    embed = discord.Embed(
        title="🌟 Bot Info",
        description="This is a stylized bot message!",
        color=0x00ff00  
    )
    
    embed.set_image(url="https://static.inaturalist.org/photos/635379170/large.jpg")
    embed.add_field(name="Field 1", value="Some text", inline=True)
    embed.add_field(name="Field 2", value="More text", inline=True)
    embed.set_footer(text="Footer text here")
    
    await ctx.send(embed=embed)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.lower() == "ping":
        await message.author.send("Pong! (DM)")

    await bot.process_commands(message)

bot.run(TOKEN)