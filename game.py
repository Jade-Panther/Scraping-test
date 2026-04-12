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

        embed = discord.Embed(
            title='Choose a taxon',
            description='Use the !pick command to select',
            color=0x7D56E8
        )

        for i, taxon in enumerate(results):
            embed.description += f"{i+1}. {taxon.get('matched_term', 'No term found')} ([{taxon.get('preferred_common_name')}](https://www.inaturalist.org/taxa/{taxon.get('id')}))\n"

        self.sessions[ctx.author.id] = GameSession(results, questions)

        
        await ctx.send(embed=embed)

    @commands.command()
    async def pick(self, ctx, num):
        try: 
            num = int(num)
        except ValueError:
            await ctx.send('Usage: !pick <number>')
            return

        session = self.sessions[ctx.author.id]

        if session.taxon is None:
            session.taxon = session.taxa_results[num]['id']


        # Add the buttons for question type selection
        embed = discord.Embed(
            title='Choose a game mode',
            description='Multiple Choice or Free Answer?',
            color=0x7D56E8
        )

        # Add buttons for game types
        view = View()
        for mode in self.game_types:
            btn = Button(label=mode, style=discord.ButtonStyle.primary)

            async def callback(interaction, mode=mode):
                session = self.sessions[interaction.user.id]
                session.type = mode

                await self.init_game(session)

                await interaction.response.send_message(
                    f"Game mode set to {mode}",
                    ephemeral=True
                )

            btn.callback = callback
            view.add_item(btn)

        await ctx.send(view=view)
        await ctx.send(f'Taxa selected: {str(session.taxa)[:1000]}')

    @commands.command()
    async def play(self, ctx):
        session = self.sessions[ctx.author.id]

        q = session.questions[session.current_index]

        embed = discord.Embed(
            title=f"Question #{session.current_index+1}",
            description='Pick the correct answer',
            color=0x7D56E8
        )

        embed.set_image(url=q['img_url'])

        view = View()

        for choice in q['choices']:
            btn = Button(label=choice, style=discord.ButtonStyle.primary)

            async def callback(interaction, choice=choice):
                if q['choices'].index(choice) == q['answer']:
                    session.score += 1
                    await self.send_correct(ctx, q)
                else:
                    await self.send_wrong(ctx, q)

                if session.current_index < session.question_num-1:
                    session.current_index += 1
                else:
                    await self.end_game(ctx, session)
                await interaction.response.send_message(f"Selected {choice}", ephemeral=True)

            btn.callback = callback
            view.add_item(btn)

        await ctx.send(embed=embed, view=view)

    async def init_game(self, session):
        if session.type == 'multiple choice':
            for _ in range(session.question_num):
                session.questions.append({
                    'img_url': 'https://inaturalist-open-data.s3.amazonaws.com/photos/404683762/large.jpg',
                    'choices': ['blueberry (scientific)', 'blackberry', 'blueberry', 'blueberry'],
                    'answer': 2,
                    'answer_url': 'https://www.inaturalist.org/taxa/71261-Accipitriformes'
                })
    
    async def send_correct(self, ctx, question):
        embed = discord.Embed(
            title='Correct!',
            description=f"[Link]({question['answer_url']})",
            color=0x7D56E8
        )
        await ctx.send(embed=embed)

    async def send_wrong(self, ctx, question):
        embed = discord.Embed(
            title='Incorrect.',
            description=f"That was a {question['choices'][question['answer']]} [Link]({question['answer_url']})",
            color=0xE86756
        )
        await ctx.send(embed=embed)

    async def end_game(self, ctx, session):
        embed = discord.Embed(
            title=f"You got {session.score}/{session.question_num} Correct! ",
            description='Use the !play command to play again or !game to play a different one',
            color=0x566CE8
        )
        session.reset()
        await ctx.send(embed=embed)

            
        
