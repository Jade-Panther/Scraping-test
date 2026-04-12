from discord.ext import commands
from discord.ui import Button, View
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
            description='',
            color=0x7D56E8
        )

        for i, taxon in enumerate(results):
            embed.description += f"{i+1}. {taxon.get('matched_term', 'No term found')} [Link](https://www.inaturalist.org/taxa/{taxon.get('id')})\n"

        embed.description += 'Use !pick to choose which taxon to quiz'
        await ctx.send(embed=embed)

        await ctx.send(f'Taxa: {taxa}, Questions: {questions}')

    @commands.command()
    async def pick(self, ctx, num):
        try: 
            num = int(num)
        except ValueError:
            await ctx.send('Usage: !pick <number>')
            return

        session = self.sessions[ctx.author.id]

        if isinstance(session.taxa, list):
            session.taxa = session.taxa[num]['id']
            
        await ctx.send(f'Taxa selected: {str(session.taxa)[:1000]}')

    @commands.command()
    async def play(self, ctx):
        session = self.sessions[ctx.author.id]

        embeds = []

        if(session.type == 'multiple choice'):
            embed = discord.Embed(
                title='Multiple Choice',
                description='Pick the correct answer!',
                color=0x7D56E8
            )

            button1 = Button(label='', style=discord.ButtonStyle.primary)
            button2 = Button(label="Option 2", style=discord.ButtonStyle.primary)
            button3 = Button(label="Option 3", style=discord.ButtonStyle.primary)
            button4 = Button(label="Option 4", style=discord.ButtonStyle.primary)

            
            embeds.append(embed)

        await ctx.send(embeds=embeds)

    def init_game(self, session):
        if session.type == 'multiple choice':
            for i in range(session.question_num):
                session.questions.append({
                    'img_url': 'https://inaturalist-open-data.s3.amazonaws.com/photos/404683762/large.jpg',
                    'choices': ['blueberry', 'blueberry', 'blueberry', 'blueberry']
                })
        
