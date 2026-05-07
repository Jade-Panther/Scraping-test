from discord.ext import commands
from discord import app_commands
import discord

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Latency: {round(self.bot.latency * 1000)}ms",
            color=0xE62055,
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def hi(self, ctx):
        await ctx.send(f"Hello {ctx.author.name}!")

    @commands.command()
    async def fun(self, ctx):
        data = await self.bot.db.get_location(ctx.author.id)
    
        if data is None:
            await ctx.send("No location set.")
        else:
            await ctx.send(f"Latitude: {data[0]}, Longitude: {data[1]}")

    @app_commands.command(name="lb", description="Display server leaderboard for IDs")
    async def lb(self,  interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.guild is None:
            score = await self.bot.db.get_score('DM', interaction.user.id)
            embed = discord.Embed(
                title="No leaderboard available",
                description=f"Your score: {score[0]}",
                color=0xE5AC12,
            )
        else:
            embed = discord.Embed(
                title="Server Leaderboard",
                description=f"Top 10 identifiers\n",
                color=0xE5AC12,
            )
            embed.set_author(
                name=f"{interaction.user}",
                icon_url=interaction.user.display_avatar.url
            )

            leaderboard = await self.bot.db.get_leaderboard(interaction.guild.id)
            medals = ["🥇", "🥈", "🥉"]
            for i, (user_id, score) in enumerate(leaderboard, start=1):
                try:
                    member = await interaction.guild.fetch_member(int(user_id))
                    username = member.display_name
                except:
                    username = f"User {user_id}"

                medal = medals[i - 1] if i <= 3 else f"{i}."

                embed.description += f"{medal} {username} - {score} pts\n"
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="stats", description="Display stats for a user")
    async def stats(self,  interaction: discord.Interaction, user: discord.Member = None):
        await interaction.response.defer()
        user = user or interaction.user
        guild_id = str(interaction.guild.id) if interaction.guild else 'DM'

        score = await self.bot.db.get_score(guild_id, user.id)
        score = score if score else [0]  
        embed = discord.Embed(
            title=f"Stats for {user.display_name}",
            color=0x3498DB
        )
        embed.add_field(name="Score", value=score[0], inline=True)
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))