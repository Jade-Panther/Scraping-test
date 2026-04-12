from discord.ext import commands
from suggestion import *
from game_session import *
import random
import discord

class NatGame(commands.Cog):
    def __init__(self, bot, inat):
        self.bot = bot
        self.inat = inat
        self.game_types = ['multiple choice', 'free answer']
        self.sessions = {}
        
    @commands.command()
    async def game(self, ctx, *args):
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
        
        # Get all the taxons that match the search query
        results = self.inat.get_taxons({'q': 'hawks'})[:10]

        # Initalize a game session
        self.sessions[ctx.author.id] = GameSession({
            'taxa': results,
            'type': 'multiple choice',
            'questions': questions
        })

        # Send embed with taxon choices
        embed = discord.Embed(
            title='Search results',
            color=0x7D56E8
        )

        for i, taxon in enumerate(results):
            embed.description += f"{i+1}. {taxon['matched_term']} [Link]({taxon['url']})"

        embed.description += 'Use !pick to choose which taxon to quiz'

        await ctx.send(f'Taxa: {taxa}, Questions: {questions}')

    @commands.command()
    async def pick(self, ctx, num):
        try: 
            num = int(num)
        except ValueError:
            await ctx.send('Usage: !pick <number>')

        session = self.sessions[ctx.author.id]

        if type(session.taxa) == list:
            session.taxa == session.taxa[num]['id']

        await ctx.send(f'Taxa: {session.taxa[:1000]}')
        
