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
            leaderboard = self.bot.db.get_leaderboard(ctx.guild.id)
            for i, (user_id, score) in enumerate(leaderboard, start=1):
                embed.description += f"{i}. <@{user_id}> - {score} points\n"
            await ctx.send(leaderboard)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))