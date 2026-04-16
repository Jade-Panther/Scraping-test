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
        guild_id = ctx.guild.id

        if guild_id is None:
            embed = discord.Embed(
                title="No leaderboard available",
                description=f"You must be in a server",
                color=0xE5AC12,
            )
        else:
            embed = discord.Embed(
                title="Server Leaderboard",
                description=f"Top 10 identifiers",
                color=0xE5AC12,
            )
            leaderboard = self.bot.db.get_leaderboard(guild_id)
            await ctx.send(leaderboard)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))