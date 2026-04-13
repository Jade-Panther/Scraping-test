from discord.ext import commands
from discord.ui import Button, View
from suggestion import *
from game_session import *
from rapidfuzz import fuzz

import random
import discord
import asyncio

class NatGame(commands.Cog):
    def __init__(self, bot, inat):
        self.bot = bot
        self.inat = inat
        self.game_types = ['multiple choice', 'free answer']
        self.sessions = {}
        
    @commands.command()
    async def game(self, ctx, *args):
        if len(args) < 2:
            return await ctx.send('Usage: !game <search query> <number of questions>')
        
        if len(args) >= 3:
            *taxa_parts, questions, diff = args
        else:
            *taxa_parts, questions = args
            diff = 'easy'

        taxa = ' '.join(taxa_parts)
        questions = int(questions)

        results = [
            t for t in self.inat.get_taxons({'q': taxa})
            if t.get('rank_level', 0) > 20
        ][:10]

        embed = discord.Embed(
            title='Choose a taxon',
            description='Use the !pick command to select\n',
            color=0x7D56E8
        )

        for i, taxon in enumerate(results):
            embed.description += f"{i+1}. {taxon.get('matched_term', 'No term found')} ([{taxon.get('preferred_common_name')}](https://www.inaturalist.org/taxa/{taxon.get('id')}))\n"

        self.sessions[ctx.author.id] = GameSession(results, questions, diff)

        
        await ctx.send(embed=embed)

    @commands.command()
    async def pick(self, ctx, num):
        if not num:
            return await ctx.send('Usage: !pick <number>')

        try: 
            num = int(num)
        except ValueError:
            await ctx.send('Usage: !pick <number>')
            return

        session = self.sessions[ctx.author.id]

        if session.taxon is None:
            session.taxon = session.taxa_results[num - 1]

        # Add buttons for game types
        await ctx.send('Pick a Game Mode')
        view = View(timeout=60)
        for mode in self.game_types:
            btn = Button(label=mode, style=discord.ButtonStyle.primary)

            async def callback(interaction, mode=mode):
                await interaction.response.defer(ephemeral=True)

                session = self.sessions[interaction.user.id]
                session.type = mode

                session.result_embed = discord.Embed(color=0x579E36)
                
                await self.init_game(session)
                await interaction.followup.send(f"Use !play to begin!")

            btn.callback = callback
            view.add_item(btn)

        await ctx.send(view=view)

    @commands.command()
    async def play(self, ctx):
        session = self.sessions[ctx.author.id]
        session.message = None

        await self.render_question(ctx, session)

    @commands.command()
    async def exit(self, ctx):
        if ctx.author.id in self.sessions:
            del self.sessions[ctx.author.id]
            
            await ctx.send('Game exited')

    @commands.command()
    async def ans(self, ctx, answer):
        session = self.sessions.get(ctx.author.id)
        if not session:
            return await ctx.send('Start a game first with !game')

        
        # Exit out on multiple choice
        if session.type == 'multiple choice':
            return
        
        q = session.questions[session.current_index]
        await ctx.send(fuzz.ratio(answer, q['ans']))
        await self.send_response(session, fuzz.ratio(answer, q['ans']) > 80, q)

    async def render_question(self, ctx, session):
        q = session.questions[session.current_index]

        if session.type == 'multiple choice':
            embed = discord.Embed(
                title=f"Question #{session.current_index+1}",
                description="Pick the correct answer",
                color=0x7D56E8
            )

            embed.set_image(url=q['img_url'])
            embed.description += q['img_url']

            view = View(timeout=60)
            for choice in q['choices']:
                btn = Button(label=choice, style=discord.ButtonStyle.primary)

                async def callback(interaction, choice=choice, q=q):
                    print('Inside callback')
            
                    session.answered = True
                
                    await interaction.response.defer(ephemeral=True)
                    
                    await self.send_response(session, (choice == q['choices'][q['answer']]), q)
                    
                    # Disable buttons
                    for item in view.children:
                        item.disabled = True
                    
                    await interaction.message.edit(view=view)
                    await asyncio.sleep(1.5)
                    await self.next_question(ctx, session)

                btn.callback = callback
                view.add_item(btn)

            # Send or edit message
            if session.message is None:
                session.message = await ctx.send(embed=embed, view=view)
            else:
                try:
                    await session.message.edit(embed=embed, view=view)
                except discord.errors.DiscordServerError:
                    await ctx.send('Discord is having issues, retrying...')
                    await asyncio.sleep(1)
                    await session.message.edit(embed=embed, view=view)

            session.answered = False
        elif session.type == 'free answer':
            embed = discord.Embed(
                title=f"Question #{session.current_index+1}",
                description='Use the !ans command to answer',
                color=0x7D56E8
            )

            embed.set_image(url=q['img_url'])
            embed.description += q['img_url']

            session.message = await ctx.send(embed=embed)


    async def init_game(self, session):
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
            if c not in choices and c.get('preferred_common_name'):
                choices.append(c)

        random.shuffle(choices)
                
        if session.type == 'multiple choice':
            for i in range(session.question_num):
                # Add the question
                answer = random.randint(0, len(choices)-1)
                session.questions.append({
                    'img_url': f"{choices[answer].get('default_photo').get('medium_url')}",
                    'choices': [f"{choice.get('preferred_common_name', '-')} ({choice['name']})" if session.diff == 'easy' else f"{choice['name']}" for choice in choices],
                    'answer': answer,
                    'answer_url': f"https://www.inaturalist.org/taxa/{choices[answer]['id']}"
                })
        elif session.type == 'free answer':
            for i in range(session.question_num):
                answer = random.randint(0, len(choices)-1)
                session.questions.append({
                    'img_url': f"{choices[answer].get('default_photo').get('medium_url')}",
                    'answer': answer,
                    'answer_url': f"https://www.inaturalist.org/taxa/{choices[answer]['id']}"
                })

    async def send_response(self, session, correct, q=None):
        if correct:
            session.score += 1

        session.result_embed.title = "Correct!" if correct else "Wrong"
        session.result_embed.description = f"[{q['choices'][q['answer']]}]({q['answer_url']})"
        session.result_embed.color = 0x579E36 if correct else 0xE86756
                        
        await session.message.edit(embed=session.result_embed)

    async def next_question(self, ctx, session):
        session.current_index += 1

        if session.current_index >= len(session.questions):
            return await self.end_game(ctx, session)

        await self.render_question(ctx, session)

    async def end_game(self, ctx, session):
        embed = discord.Embed(
            title=f"You got {session.score}/{session.question_num} Correct! ",
            description='Use the !play command to play again or !game to play a different one',
            color=0x566CE8
        )
        session.reset()
        await ctx.send(embed=embed)

            
        
