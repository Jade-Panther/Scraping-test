from discord.ext import commands
from discord import app_commands
import discord
import random

from helpers.naturalist import INatClient


class Naturalist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.inat = self.bot.inat
        self.search_results = {}

        self.lat = 39.1928853
        self.lng = -76.7241371

    @commands.command()
    async def info(self, ctx, radius: int = 100):
        """
        Get recent rare species observations nearby
        """
        try:
            data = {
                "lat": self.lat,
                "lng": self.lng,
                "radius": radius,
                "order_by": "observed_on",
                "order": "desc",
                "per_page": 100,
                "quality_grade": "research",
                "fields": "all",
            }

            observations = self.inat.get_observations(data)
            rare_sightings = self.inat.filter_rare(observations)[:6]

            if not rare_sightings:
                await ctx.send("No rare species discovered.")
                return

            for obs in rare_sightings[:5]:
                embed = discord.Embed(
                    title="🌿 Naturalist Alert",
                    description="A rare species was discovered nearby!",
                    color=0x00FF00,
                )

                # Image
                photos = obs.get("photos")
                if photos and len(photos) > 0:
                    url = photos[0].get("url", "").replace("large", "original")
                    embed.set_image(url=url)

                # Name and link
                species_name = obs.get("species_guess", "Unknown species")
                obs_id = obs.get("id")

                embed.set_author(
                    name=f"{ctx.author}",
                    icon_url=ctx.author.display_avatar.url
                )
                embed.add_field(
                    name=species_name,
                    value=f"[View Observation](https://www.inaturalist.org/observations/{obs_id})",
                    inline=False,
                )

                await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error fetching data: {e}")

    @app_commands.command(name="search", description="Searches database for taxa/species matching query")
    async def search(self, interaction: discord.Interaction, search: str, rank: str = "species", number: int = 10):
        """
        Search for a species/taxa from iNaturalist
        """
        await interaction.response.defer()

        data = {
            "q": search,
            "per_page": results,
            "order_by": "taxon_name",
            "order": "desc",
            "rank": rank
        }

        results = self.inat.get_taxons(data)
        if not results:
            return await interaction.followup.send("No results found.")

        embed = discord.Embed(
            title=f"🔎 Results for {search}",
            color=0x2ECC71
        )
        embed.set_author(
            name=str(interaction.user),
            icon_url=interaction.user.display_avatar.url
        )

        for tax in results[:number]:
            name = tax.get("preferred_common_name") or tax.get("name")
            
            embed.add_field(
                name=name,
                value=f"([{tax.get('preferred_common_name')}](https://www.inaturalist.org/taxa/{tax.get('id')}))",
                inline=False
            )
        self.search_results[interaction.user.id] = results

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="fetch", description="Get data on a species. If value=number, fetch from search, else fetch from scientific name")
    async def fetch_data(self, interaction: discord.Interaction, value: str):
        """
        Get data on a species/taxa
        """
        await interaction.response.defer()

        user_id = interaction.user.id
        cached = self.search_results.get(user_id)

        if value.isdigit():
            if not cached:
                return await interaction.followup.send("No search history found. Use /search <query>")

            try:
                taxon = cached[int(value) - 1]
            except IndexError:
                return await interaction.followup.send("Invalid index.")
        else:
            results = self.inat.get_taxons({
                "q": value,
                "per_page": 1
            })

            if not results:
                return await interaction.followup.send("No taxon found.")

            taxon = results[0]

        taxon_id = taxon["id"]

        embed = discord.Embed(
            title=taxon.get("preferred_common_name") or taxon["name"],
            description=f"**Scientific:** {taxon['name']}",
            color=0x12E5B7
        )

        embed.add_field(name="Rank", value=taxon.get("rank", "Unknown"))
        embed.add_field(
            name="Link",
            value=f"https://www.inaturalist.org/taxa/{taxon_id}",
            inline=False
        )

        await interaction.followup.send(embed=embed)
    

    @commands.command(name="randomspecies")
    async def random_species(self, ctx):
        """
        Get a random species
        """
        try:
            page = random.randint(1, 200)

            results = self.inat.get_taxons({
                "rank": "species",
                "page": page,
                "per_page": 30
            })

            if not results:
                await ctx.send("Couldn't find any species.")
                return

            species = random.choice(results)

            name = species.get("preferred_common_name", "Unknown")
            scientific = species.get("name", "Unknown")
            summary = species.get("wikipedia_summary", "No description available.")

            photo = species.get("default_photo", {})
            image_url = photo.get("url")

            if image_url:
                image_url = image_url.replace("square", "large")

            embed = discord.Embed(
                title=name,
                description=summary[:2000],
                color=0x7D56E8
            )
            embed.set_author(
                name=f"{ctx.author}",
                icon_url=ctx.author.display_avatar.url
            )

            embed.add_field(
                name=scientific,
                value=f"[View Taxon](https://www.inaturalist.org/taxa/{species.get('id')})",
                inline=False
            )

            if image_url:
                embed.set_image(url=image_url)

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error fetching species: {e}")

    @app_commands.command(name="setlocation", description="Set your location")
    async def setlocation(self, interaction: discord.Interaction, lat: float, lng: float):
        await self.bot.db.set_location(str(interaction.user.id), lat, lng)

        await interaction.response.send_message(
            "Location saved",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Naturalist(bot))