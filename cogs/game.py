from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View
from helpers.inatclient import *
from helpers.game_session import *
from rapidfuzz import fuzz

import random
import discord
import asyncio
import string

# jwepo41695@minitts.net
class NatGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.inat = self.bot.inat
        self.game_types = ['multiple choice', 'free answer']
        self.diff_mult = {
            'easy': 1,
            'medium': 2,
            'hard': 4
        }
        self.players = []
        self.sessions = {}
        self.user_sessions = {}

    def gen_code(self, len=6):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=len))
    
    def get_sess(self, user_id):
        sess_id = self.user_sessions.get(user_id)
        if not sess_id:
            return None

        return self.sessions.get(sess_id)
    
    async def load_session(self, session_id):
        cursor = await self.bot.db.db.execute("""
            SELECT session_id, host_id, multi, current_index, type, taxon_id
            FROM game_sessions
            WHERE session_id = ?
        """, (session_id,))

        row = await cursor.fetchone()
        if not row:
            return None

        session = GameSession(
            row[0], [], 0, None, row[4], bool(row[2])
        )

        session.host_id = row[1]
        session.current_index = row[3]
        session.type = row[4]

        if row[5]:
            session.taxon = {"id": row[5]}

        self.sessions[session_id] = session
        return session
   
    @app_commands.command(name="game", description="Start a new NatGame session")
    async def game(self, interaction: discord.Interaction, taxa: str, questions: int, location: str = None, diff: str = "easy", multiplayer: bool = True):
        # Make sure questions is valid
        if questions <= 0:
            return await interaction.response.send_message("Questions must be > 0", ephemeral=True)

        # Get the search query for what the user entered
        results = [
            t for t in self.inat.get_taxons({'q': taxa})
            if t.get('rank_level', 0) > 20
        ][:10]

        # Send the instruction embed
        embed = discord.Embed(
            title='Choose a taxon',
            description='Use the /pick command to select\n',
            color=0x7D56E8
        )
        embed.set_author(
            name=f"{interaction.user}",
            icon_url=interaction.user.display_avatar.url
        )

        # Add the list of search results to embed
        for i, taxon in enumerate(results):
            embed.description += (
                f"{i+1}. {taxon.get('matched_term', 'No term found')} "
                f"([{taxon.get('preferred_common_name')}](https://www.inaturalist.org/taxa/{taxon.get('id')}))\n")

        # Start the game session
        code = self.gen_code()
        session = GameSession(code, results, questions, location, diff, multiplayer)
        session.host_id = interaction.user.id
        session.players.add(interaction.user.id)
        session.scores[interaction.user.id] = 0

        self.sessions[code] = session
        self.user_sessions[interaction.user.id] = code

        await self.bot.db.db.execute("""
        INSERT INTO game_sessions (session_id, host_id, multi, current_index, type, taxon_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session.id,
            session.host_id,
            int(session.multi),
            session.current_index,
            session.type or "",
            None
        ))
        await self.bot.db.db.commit()

        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="pick", description="Pick a taxon from results")
    async def pick(self, interaction: discord.Interaction, num: int):
        # Make sure game is started first
        session = self.get_sess(interaction.user.id)
        if not session:
            return await interaction.response.send_message("Start a game first with /game", ephemeral=True)
        if num > len(session.taxa_results):
            return await interaction.response.send_message("Invalid pick number")

        # Get the taxon selected
        session.taxon = session.taxa_results[num - 1]
        await self.bot.db.db.execute("""
        UPDATE game_sessions
        SET taxon_id = ?
        WHERE session_id = ?
        """, (
            session.taxon["id"],
            session.id
        ))
        await self.bot.db.db.commit()


        # Send the game mode pick view
        view = View(timeout=60)
        for mode in self.game_types:
            btn = Button(label=mode, style=discord.ButtonStyle.primary)

            # Function that happens when button pressed
            async def callback(interaction: discord.Interaction, mode=mode):
                session = self.get_sess(interaction.user.id)
                                        
                if interaction.user.id != session.host_id:
                    return 
                await interaction.response.defer(ephemeral=True)

                # Set the mode for the session
                session.type = mode
                session.result_embed = discord.Embed(color=0x579E36)

                # Try initializing the game if valid
                try:
                    await self.init_game(session)
                except ValueError as e:
                    await self.exit_session(interaction)
                    return await interaction.followup.send(str(e))
                session.message = None

                # Send the first question
                await self.render_question(interaction, session)

            # Assign callback and add button to view
            btn.callback = callback
            view.add_item(btn)

        # Send the game mode embed
        embed = discord.Embed(
            title=f"Pick a Game Mode",
            description=f"Code: {session.id}\nUsers can join using /join" if session.multi else "Singleplayer mode",
            color=0x7D56E8
        )

        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="join", description="Join a multiplayer game")
    async def join(self, interaction: discord.Interaction, code: str):
        # Make sure session is valid
        session = self.sessions.get(code)
        if not session:
            return await interaction.response.send_message("Code not valid. Start a game first with /game", ephemeral=True)
        if not session.multi:
            return await interaction.response.send_message("Game is not multiplayer :(", ephemeral=True)

        session.players.add(interaction.user.id)
        session.scores[interaction.user.id] = 0
        self.user_sessions[interaction.user.id] = code
        await interaction.response.send_message(f"{interaction.user.display_name} has joined session {session.id} :)")

    @app_commands.command(name="exit", description="Exit current game")
    async def exit(self, interaction: discord.Interaction):
        if interaction.user.id in self.sessions:
            await interaction.response.defer(ephemeral=True)
            self.exit_session(interaction)
        else:
            await interaction.response.send_message("No active game", ephemeral=True)

    @app_commands.command(name="again", description="Play the previous game again")
    async def again(self, interaction: discord.Interaction):
        session = self.get_sess(interaction.user.id)
        if not session:
            return await interaction.response.send_message('Start a game first with /game', ephemeral=True)
        
        await self.render_question(interaction, session)

    @app_commands.command(name="ans", description="Answer a free response question")
    async def ans(self, interaction: discord.Interaction, *, answer: str):
        session = self.get_sess(interaction.user.id)
        user_id = interaction.user.id

        if not session:
            return await interaction.response.send_message('Start a game first with /game', ephemeral=True)

        # Multiplayer free answer
        if session.multi:
            if user_id not in session.players:
                return await interaction.response.send_message("You're not in this game", ephemeral=True)
        
            session.answered_users.add(user_id)

        
        if session.type == 'multiple choice':
            return await interaction.response.send_message("Use buttons for multiple choice", ephemeral=True)

        q = session.questions[session.current_index]
        score = fuzz.ratio(answer.strip().lower(), q['answer'].strip().lower())

        await interaction.response.send_message(str(score), ephemeral=True)

        correct = score > 80
        if correct:
            await self.bot.db.db.execute("""
            INSERT INTO game_players (session_id, user_id, score)
            VALUES (?, ?, 1)
            ON CONFLICT(session_id, user_id)
            DO UPDATE SET score = score + 1
            """, (session.id, user_id))
            await self.bot.db.db.commit()

        await self.send_response(session, q, f"[{q['answer']}]({q['answer_url']})")
        await asyncio.sleep(1.5)
        await self.next_question(interaction, session)

    async def render_question(self, interaction, session):
        # Get the current question
        q = session.questions[session.current_index]
        await self.bot.db.db.execute("""
            UPDATE game_sessions
            SET current_index = ?
            WHERE session_id = ?
            """, (session.current_index, session.id))
        await self.bot.db.db.commit()
        session.answered = False
        session.first_correct_user = None

        # For multiple choice questions
        if session.type == 'multiple choice':
            # Initialize the embed
            embed = discord.Embed(
                title=f"Question #{session.current_index+1}",
                description="Pick the correct answer\nIMG: " + q['img_url'],
                color=0x7D56E8,
            )
            embed.set_author(
                name=f"{interaction.user}",
                icon_url=interaction.user.display_avatar.url
            )
            embed.set_image(url=q['img_url'])
            embed.set_image(url=q['img_url'])
            embed.set_footer(text="Sometimes image may not display; use image link if this occurs.")
            

            # Add the button choices
            view = View(timeout=60)
            for choice in q['choices']:
                btn = Button(label=choice, style=discord.ButtonStyle.primary)


                # Function called when answer button pressed
                async def callback(interaction: discord.Interaction, choice=choice, q=q):
                    session = self.get_sess(interaction.user.id)
                    user_id = interaction.user.id

                    await interaction.response.defer(ephemeral=True)
                    
                    # Not in game
                    if session is None or (session.multi and user_id not in session.players):
                        return await interaction.followup.send("You're not in this game", ephemeral=True)

                    # Singleplayer restriction
                    if not session.multi and user_id != session.host_id:
                        return await interaction.followup.send("You're not the host", ephemeral=True)

                    
                    session.answered = True
                    

                    correct = (choice == q['choices'][q['answer']])

                    if not correct:
                        await interaction.followup.send("Wrong ❌", ephemeral=True)

                        # Check if everyone answered wrong
                        if session.multi and session.answered_users == session.players:
                            if session.first_correct_user is None:
                                await self.send_response(
                                    session,
                                    False,
                                    q,
                                    "❌ No one got it right"
                                )
                                await asyncio.sleep(1.5)
                                return await self.next_question(interaction, session)

                        return
                

                    if session.question_locked:
                        return

                    session.question_locked = True
                    session.first_correct_user = user_id

                    await self.bot.db.db.execute("""
                        INSERT INTO game_players (session_id, user_id, score)
                        VALUES (?, ?, 1)
                        ON CONFLICT(session_id, user_id)
                        DO UPDATE SET score = score + 1
                    """, (session.id, user_id))
                    await self.bot.db.db.commit()

                    # update embed
                    await self.send_response(
                        session,
                        True,
                        q,
                        f"🏆 Correct — first: <@{user_id}>"
                    )

                    # Disable buttons once pressed
                    for item in view.children:
                        item.disabled = True

                    # Send the message and go to the next question
                    await interaction.message.edit(view=view)
                    await asyncio.sleep(1.5)
                    await self.next_question(interaction, session)

                btn.callback = callback
                view.add_item(btn)

            if session.message is None:
                session.message = await interaction.channel.send(embed=embed, view=view)
            else:
                await session.message.edit(embed=embed, view=view)

            session.answered = False

        elif session.type == 'free answer':
            # Initialize answer embed
            embed = discord.Embed(
                title=f"Question #{session.current_index+1}",
                description='Use /ans to answer',
                color=0x7D56E8
            )
            embed.set_author(
                name=f"{interaction.user}",
                icon_url=interaction.user.display_avatar.url
            )
            embed.set_image(url=q['img_url'])

            session.message = await interaction.channel.send(embed=embed)

    async def init_game(self, session):
        choices = []
        params = {
            'taxon_id': session.taxon.get('id'),
            'quality_grade': 'research',
            'photos': True
        }
        if session.location:
            place = self.inat.get_place(session.location)
            if place:
                params['place_id'] = place

        obs = self.inat.get_observations(params) 
# 
        taxa = self.inat.get_taxons({
            'taxon_id': session.taxon['id'],
            'rank': 'species',
            'per_page': 200
        })

        species = {}

        for t in taxa:
            if t.get('rank') != 'species':
                continue

            if not t.get('preferred_common_name'):
                continue

            species[t['id']] = t

        valid_species = list(species.values())

        if len(valid_species) < 2:
            raise ValueError("Not enough species found.")
        
        if session.type == 'multiple choice':
            for i in range(session.question_num):
                choices = random.sample(valid_species, min(len(valid_species), 4)) 
                random.shuffle(choices)

                answer = random.randint(0, len(choices)-1)
                obs = self.inat.get_observation_of_taxa(choices[answer]['id'])
                photos = obs.get('photos', [])

                if not photos:
                    continue 

                img = photos[0].get('url')
                if img:
                    img = img.replace('square', 'original')
                    
                session.questions.append({
                    'img_url': img,#choices[answer]['default_photo']['medium_url'],
                    'choices': [
                        f"{c.get('preferred_common_name','-')} ({c['name']})"
                        for c in choices
                    ],
                    'answer': answer,
                    'answer_url': f"https://www.inaturalist.org/taxa/{choices[answer]['id']}"
                })
        elif session.type == 'free answer':
            for i in range(min(session.question_num, len(valid_species))):
                species_choice = random.choice(valid_species)

                session.questions.append({
                    'img_url': species_choice['default_photo']['medium_url'],
                    'answer': species_choice.get('preferred_common_name', species_choice['name']),
                    'answer_url': f"https://www.inaturalist.org/taxa/{species_choice['id']}"
                })

    async def send_response(self, session, correct, q=None, url=''):
        embed = discord.Embed(
            title="Correct!" if correct else "Wrong",
            description=url,
            color=0x579E36 if correct else 0xE86756
        )
        if session.multi and session.first_correct_user:
            embed.title += f" — First: <@{session.first_correct_user}>"

        if q and q.get('img_url'):
            embed.set_image(url=q['img_url'])

        await session.message.edit(embed=embed)

    async def next_question(self, interaction, session):
        session.current_index += 1

        # End the game
        if session.current_index >= len(session.questions):
            return await self.end_game(interaction, session)

        await self.render_question(interaction, session)

    async def end_game(self, interaction, session):
        # Add the score for non-multiplayer
        if not session.multi or (len(session.players) == 1):
            accuracy = session.scores[interaction.user.id] / session.question_num
            base = session.question_num * self.diff_mult.get(session.diff, 1)
            score = int(base * accuracy)

            if interaction.guild:
                await self.bot.db.add_score(interaction.guild.id, interaction.user.id, score)
            else:
                await self.bot.db.add_score(None, interaction.user.id, score)

            # Send the result embed
            embed = discord.Embed(
                title=f"You got {session.score}/{session.question_num} Correct!",
                description=f"Score: {score}",
                color=0x566CE8
            )
            
        # Add up the scores for multiplayer
        else:
            desc = ""

            for uid, score in sorted(session.scores.items(), key=lambda x: x[1], reverse=True):
                user = await self.bot.fetch_user(uid)
                desc += f"**{user.name}**: {score}\n"

            embed = discord.Embed(
                title="Multiplayer Results",
                description=desc,
                color=0x566CE8
            )


        session.reset()
        await interaction.channel.send(embed=embed)

    async def exit_session(self, interaction):
        sess_id = self.user_sessions.get(interaction.user.id)
        if not sess_id:
            return
        
        if sess_id in self.sessions:
            del self.sessions[sess_id]
            del self.user_sessions[interaction.user.id] 
            await interaction.followup.send("Game exited")

async def setup(bot):
    await bot.add_cog(NatGame(bot))