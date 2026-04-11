import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
from suggestion import *

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
USER_ID = int(os.getenv("USER_ID"))

inat = INatClient()
lat, lng = 39.1928853, -76.7241371
radius = 300

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
    rare_sightings = inat.filter_rare(inat.get_observations(lat, lng, radius))

    embeds = []
    for obs in rare_sightings:
        embed = discord.Embed(
            title='Naturalist Alert',
            description='A rare species was discovered nearby!',
            color=0x00ff00  
        )
        
        embed.set_image(url=obs.get('photos')[0].get('url'))
        embed.add_field(name=obs.species_guess, value="Some text", inline=True)
        #embed.set_footer(text="Footer text here")

        embeds.append(embed)
    
    await ctx.send(embed=embeds[:5])


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.lower() == "ping":
        await message.author.send("Pong! (DM)")

    await bot.process_commands(message)

bot.run(TOKEN)