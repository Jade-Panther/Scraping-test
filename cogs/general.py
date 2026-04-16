from discord.ext import commands
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
    async def lb(self, ctx):
        if ctx.guild is None:
            embed = discord.Embed(
                title="No leaderboard available",
                description=f"You must be in a server",
                color=0xE5AC12,
            )
        else:
            embed = discord.Embed(
                title="Server Leaderboard",
                description=f"Top 10 identifiers\n",
                color=0xE5AC12,
            )
            embed.set_author(
                name=f"{ctx.author} Leaderboard",
                icon_url=ctx.author.display_avatar.url
            )
            embed.set_thumbnail(url=ctx.author.display_avatar.url)

            leaderboard = await self.bot.db.get_leaderboard(ctx.guild.id)
            medals = ["🥇", "🥈", "🥉"]
            for i, (user_id, score) in enumerate(leaderboard, start=1):
                member = ctx.guild.get_member(int(user_id))
                username = member.display_name if member else f"User {user_id}"

                medal = medals[i - 1] if i <= 3 else f"{i}."

                embed.description += f"{medal} {username} - {score} pts\n"
            await ctx.send(leaderboard)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))