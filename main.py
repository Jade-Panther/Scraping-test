import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
import random
from suggestion import *

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
USER_ID = int(os.getenv("USER_ID"))

inat = INatClient()
lat, lng = 39.1928853, -76.7241371
radius = 100

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
async def info(ctx, radius=100):
    rare_sightings = inat.filter_rare(inat.get_observations(lat, lng, radius))[:6]

    print(rare_sightings)

    embeds = []
    for obs in rare_sightings:
        print('INSIDE FOR OBS')
        embed = discord.Embed(
            title='Naturalist Alert',
            description='A rare species was discovered nearby!',
            color=0x00ff00  
        )
        
        photos = obs.get('photos')
        if photos and len(photos) > 0:
            embed.set_image(url=photos[0].get('url').replace('large', 'original'))

        embed.add_field(name=obs.get('species_guess'), value='www.inaturalist.org/observations/'+str(obs.get('id')), inline=True)
        #embed.set_footer(text="Footer text here")

        embeds.append(embed)
    
    if len(embeds) == 0:
       await ctx.send('No rare species discovered')
    
    for embed in embeds[:5]:
        await ctx.send(embed=embed)

@bot.command()
async def randomSpecies(ctx):
    page = random.randint(0, 200)

    results = inat.get_taxons({
        "rank": "species",
        "page": page,
        "per_page": 30
    })

    if not results:
        await ctx.send("Couldn't find any species.")
        return
    
    species = random.choice(results)

    name = species.get('preferred_common_name', 'Unknown')
    scientific = species.get('name', 'Unknown')
    summary = species.get('wikipedia_summary', 'No description available.')

    photo = species.get('default_photo', {})
    image_url = photo.get('url')

    if image_url:
        image_url = image_url.replace('square', 'large')

    embed = discord.Embed(
        title=name,
        description=summary[:2000],  
        color=0x7D56E8
    )

    embed.add_field(name=scientific, value='www.inaturalist.org/taxa/'+species.get('id'), inline=False)

    if image_url:
        embed.set_image(url=image_url)

    await ctx.send(embed=embed)

@bot.command()
async def game(ctx, *args):
    if len(args) < 2:
        await ctx.send('Usage: !game <taxa> <questions>')
        return

    *taxa_parts, questions = args
    taxa = ' '.join(taxa_parts)

    try:
        questions = int(questions)
    except ValueError:
        await ctx.send('Questions must be a number.')
        return
    
    results = inat.get_taxons({'q': 'hawks'})

    await ctx.send(f'Results: {results}')
    await ctx.send(f'Taxa: {taxa}, Questions: {questions}')
    

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.lower() == "ping":
        await message.author.send("Pong! (DM)")

    await bot.process_commands(message)

bot.run(TOKEN)