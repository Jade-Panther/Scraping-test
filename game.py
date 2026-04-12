from discord.ext import commands
from suggestion import *
from game_session import *
import random

class NatGame(commands.Cog):
    def __init__(self, bot, inat):
        self.bot = bot
        self.inat = inat
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
        
        results = self.inat.get_taxons({'q': 'hawks'})[:10]

        self.sessions[ctx.author.id] = GameSession({
            'taxa': taxa,
            'type': 'multiple choice',
            'questions': questions
        })

        for taxon in results:
            await ctx.send(f'Match: {taxon.get("matched_term")}')

        await ctx.send(f'Taxa: {taxa}, Questions: {questions}')

    @commands.command()
    async def pick(self, ctx, num):
        try: 
            num = int(num)
        except ValueError:
            await ctx.send('Usage: !pick <number>')