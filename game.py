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
        *taxa_parts, questions = args
        taxa = ' '.join(taxa_parts)

        questions = int(questions)

        results = [
            t for t in self.inat.get_taxons({'q': taxa})
            if t.get('rank_level', 0) > 20
        ][:10]

        self.sessions[ctx.author.id] = GameSession(results, questions)

        embed = discord.Embed(
            title="Choose a game mode",
            description="Multiple Choice or Free Answer?",
            color=0x7D56E8
        )

        view = View()

        for mode in self.game_types:
            btn = Button(label=mode, style=discord.ButtonStyle.primary)

            async def callback(interaction, mode=mode):
                session = self.sessions[ctx.author.id]
                session.type = mode

                self.init_game(session)

                await interaction.response.send_message(
                    f"Game mode set to {mode}",
                    ephemeral=True
                )

            btn.callback = callback
            view.add_item(btn)

        await ctx.send(embed=embed, view=view)

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

        async def button_callback(interaction):
            session.type = interaction.data['label']
            self.init_game(session)
            await interaction.response.send_message(
                f"You clicked {interaction.data['custom_id']}",
                ephemeral=True
            )

        # Add the buttons for question type selection
        view = View()
        buttons = [
            Button(label=self.game_types[i], style=discord.ButtonStyle.primary, custom_id='opt1') 
            for i in self.game_types
        ]
        for b in buttons:
            b.callback = button_callback
            view.add_item(b)
            
        await ctx.send(f'Taxa selected: {str(session.taxa)[:1000]}')

    @commands.command()
    async def play(self, ctx):
        session = self.sessions[ctx.author.id]

        q = session.questions[session.current_index]

        embed = discord.Embed(
            title='Question',
            description='Pick the correct answer',
            color=0x7D56E8
        )

        embed.set_image(url=q['img_url'])

        view = View()

        for choice in q['choices']:
            btn = Button(label=choice, style=discord.ButtonStyle.primary)

            async def callback(interaction, choice=choice):
                if choice == q['answer']:
                    session.score += 1

                session.current_index += 1
                await interaction.response.send_message(f"Selected {choice}", ephemeral=True)

            btn.callback = callback
            view.add_item(btn)

        await ctx.send(embed=embed, view=view)

    async def init_game(self, session):
        if session.type == 'multiple choice':
            for _ in range(session.question_num):
                session.questions.append({
                    'img_url': 'https://inaturalist-open-data.s3.amazonaws.com/photos/404683762/large.jpg',
                    'choices': ['blueberry', 'blackberry', 'blueberry', 'blueberry'],
                    'answer': 'blackberry'
                })

            
        
