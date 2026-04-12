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
            session.taxon = session.taxa_results[num]

        # Add buttons for game types
        await ctx.send('Pick a Game Mode')
        view = View()
        for mode in self.game_types:
            btn = Button(label=mode, style=discord.ButtonStyle.primary)

            async def callback(interaction, mode=mode):
                session = self.sessions[interaction.user.id]
                session.type = mode

                await self.init_game(session)
                await interaction.response.send_message(
                    f"Use !play to begin!",
                    ephemeral=True
                )

            btn.callback = callback
            view.add_item(btn)

        await ctx.send(view=view)

    @commands.command()
    async def play(self, ctx):
        session = self.sessions[ctx.author.id]
        session.message = None

        await self.render_question(ctx, session)

    async def render_question(self, ctx, session):
        q = session.questions[session.current_index]

        embed = discord.Embed(
            title=f"Question #{session.current_index+1}",
            description="Pick the correct answer",
            color=0x7D56E8
        )

        embed.set_image(url=q['img_url'])

        view = View()

        for choice in q['choices']:
            btn = Button(label=choice, style=discord.ButtonStyle.primary)

            async def callback(interaction, choice=choice, q=q):
                if getattr(session, 'answered', False):
                    return await interaction.response.send_message("Already answered!", ephemeral=True)

                session.answered = True

                if choice == q['choices'][q['answer']]:
                    session.score += 1
                #     await self.send_correct(interaction, q)
                # else:
                #     await self.send_wrong(interaction, q)

                await interaction.response.send_message(
                    "Correct!" if choice == q['choices'][q['answer']] else "Wrong!",
                    ephemeral=True
                )

                # Disable buttons
                for item in view.children:
                    item.disabled = True

                await interaction.message.edit(view=view)

                # Go to next question
                await self.next_question(ctx, session)

            btn.callback = callback
            view.add_item(btn)

        # Send or edit message
        if session.message is None:
            session.message = await ctx.send(embed=embed, view=view)
        else:
            await session.message.edit(embed=embed, view=view)

        session.answered = False

    async def init_game(self, session):
        if session.type == 'multiple choice':
            for _ in range(session.question_num):
                choices = []
                obs = self.inat.get_observations({
                    'taxon_id': session.taxon.get('id'),
                    'quality_grade': 'research',
                    'photos': True
                })

                # Get the species observations' taxon 
                species = {}
                for o in obs:
                    tax = o['taxon']
                    if tax['rank'] == 'species':
                        species[tax['id']] = tax

                # Add to choices and randomize
                while len(choices) < 4:
                    c = random.choice(list(species.values()))
                    if c not in choices:
                        choices.append(c)

                random.shuffle(choices)

                # Add the question
                answer = random.randint(0, 3)
                session.questions.append({
                    'img_url': f"https://inaturalist-open-data.s3.amazonaws.com/photos/{choices[answer].get('default_photo').get('id')}/original.jpg",
                    'choices': [f"{choice['preferred_common_name'] or '-'} ({choice['name']})" for choice in choices],
                    'answer': answer,
                    'answer_url': f"https://www.inaturalist.org/taxa/{choices[answer]['id']}"
                })

    async def next_question(self, ctx, session):
        session.current_index += 1

        if session.current_index >= len(session.questions):
            return await self.end_game(ctx, session)

        await self.render_question(ctx, session)
    
    async def send_correct(self, interaction, question):
        embed = discord.Embed(
            title='Correct!',
            description=f"[{question['choices'][question['answer']]}]({question['answer_url']})",
            color=0x579E36
        )
        await interaction.response.send_message(embed=embed)

    async def send_wrong(self, interaction, question):
        embed = discord.Embed(
            title='Incorrect.',
            description=f"That was a {question['choices'][question['answer']]} [Link]({question['answer_url']})",
            color=0xE86756
        )
        await interaction.response.send_message(embed=embed)

    async def end_game(self, ctx, session):
        embed = discord.Embed(
            title=f"You got {session.score}/{session.question_num} Correct! ",
            description='Use the !play command to play again or !game to play a different one',
            color=0x566CE8
        )
        session.reset()
        await ctx.send(embed=embed)

            
        
