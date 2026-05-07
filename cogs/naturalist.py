from discord.ext import commands
from discord import app_commands
import discord
import random

from helpers.inatclient import INatClient

from itertools import islice

def chunks(iterable, size):
    it = iter(iterable)
    for first in it:
        yield [first] + list(islice(it, size-1))


class Naturalist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.inat = self.bot.inat
        self.search_results = {}


    @app_commands.command(name="rare", description="Get rare species near you")
    async def get_rare(self, interaction: discord.Interaction, lat: float = None, lng: float = None, radius: int = 100):
        """
        Get recent rare species observations nearby
        """
        await interaction.response.defer()
        
        if not lat and not lng:
            data = await self.bot.db.get_location(interaction.user.id)
            if data is None:
                return await interaction.followup.send("You must set a location with /setlocation or input it with the command")
            lat, lng = map(float, data)

        try:
            params = {
                "lat": lat, 
                "lng": lng,
                "radius": radius,
                "order_by": "observed_on",
                "order": "desc",
                "per_page": 200,
                "quality_grade": "research",
                "fields": "all"
            }
            observations = self.inat.get_observations(params)
        # print(observations)
            if not observations:
                return await interaction.followup.send("No observations found nearby.")

          #  print('OBSERVATIONS: ' + str(len(observations)))
            taxon_ids = [int(obs['taxon']['id']) for obs in observations if obs.get('taxon')]
          #  print("TAXON IDS: " + str(taxon_ids))
            taxon_data = {}
            for chunk in chunks(taxon_ids, 30):
                results = self.inat.get_taxons({"fields": "all"}, ",".join(map(str, chunk)))
                #print('RESULTS ' + str(results))
                for taxon in results:
                    taxon_data[int(taxon['id'])] = taxon

           # print('DATA ' + str(taxon_data))


            RARE_CODES = ['EX','EW','CR','EN','VU','NT','S1','S2','N1','N2']
            rare_obs = []
            for obs in observations:
                taxon = obs.get('taxon')
                #print('OBS TAXON: ' + str(taxon))
                if not taxon:
                    continue

                taxon_info = taxon_data.get(int(taxon['id']))
                #print('TAXON INFO: ' + str(taxon_info))
                if not taxon_info:
                    continue
               
                for status in taxon_info.get('conservation_statuses', []):
                    code = status.get('status')
                  #  print(code)
                    if code and any(c in RARE_CODES for c in code.split(',')) and taxon_info.get('observations_count', 0) < 10000:
                        rare_obs.append(obs)
                        break

            if not rare_obs:
                return await interaction.followup.send("No rare species discovered.")

            for obs in rare_obs[:5]:
                embed = discord.Embed(
                    title="🌿 Naturalist Alert",
                    description="A rare species was discovered nearby!",
                    color=0x00FF00,
                )

                photos = obs.get("photos") or []
                if photos:
                    url = photos[0].get("url", "").replace("large", "original")
                    embed.set_image(url=url)

                species_name = obs.get("species_guess", "Unknown species")
                obs_id = obs.get("id")

                embed.set_author(
                    name=str(interaction.user),
                    icon_url=interaction.user.display_avatar.url
                )
                embed.add_field(
                    name=species_name,
                    value=f"[View Observation](https://www.inaturalist.org/observations/{obs_id})",
                    inline=False,
                )

                await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"Error fetching data: {e}")

    @app_commands.command(name="search", description="Searches database for taxa/species matching query")
    async def search(self, interaction: discord.Interaction, search: str, rank: str, number: int = 10):
        """
        Search for a species/taxa from iNaturalist
        """
        await interaction.response.defer()

        data = {
            "q": search,
            "per_page": number,
            "order_by": "taxon_name",
            "order": "desc",
            "rank": rank
        }

        results = self.inat.get_taxons(data)
        if not results:
            return await interaction.followup.send("No results found.")

        embed = discord.Embed(
            title=f"🔎 Results for {search}",
            description="\n",
            color=0x2ECC71
        )
        embed.set_author(
            name=str(interaction.user),
            icon_url=interaction.user.display_avatar.url
        )

        for i, tax in enumerate(results[:number]):
            name = tax.get("preferred_common_name") or tax.get("name")
            
            embed.description += f"{i + 1}. ([{name}](https://www.inaturalist.org/taxa/{tax.get('id')}))\n"
        self.search_results[interaction.user.id] = results

        embed.set_footer(text="Not seeing results? Adjust taxon rank or increase number shown")

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
        taxon = self.inat.get_taxon_by_id(taxon_id)

        image_url = None
        photo = taxon.get("default_photo")
        if photo:
            image_url = photo.get("medium_url") or photo.get("url")


        embed = discord.Embed(
            title=taxon.get("preferred_common_name") or taxon["name"],
            color=0x2ECC71,
            url=f"https://www.inaturalist.org/taxa/{taxon['id']}"
        )

        embed.add_field(
            name=taxon.get('preferred_common_name', '-'),
            value=taxon["name"],
            inline=False
        )

        embed.add_field(
            name="📊 Rank",
            value=taxon.get("rank", "Unknown"),
            inline=True
        )

        embed.add_field(
            name="👀 Observations",
            value=taxon.get('observations_count'),
            inline=True
        )

        if taxon.get("extinct"):
            embed.add_field(
                name="EXTINCT",
                value=" ",
                inline=True
            )
        

        if image_url:
            embed.set_image(url=image_url)

        embed.set_footer(text="Data from iNaturalist")

        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="randomspecies", description="Returns info on a random species")
    async def random_species(self, interaction: discord.Interaction):
        """
        Get a random species
        """
        await interaction.response.defer()
        try:
            page = random.randint(1, 200)

            results = self.inat.get_taxons({
                "rank": "species",
                "page": page,
                "per_page": 30
            })

            if not results:
                await interaction.followup.send("Couldn't find any species.")
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
                name=f"{interaction.user}",
                icon_url=interaction.author.display_avatar.url
            )
            embed.add_field(
                name=scientific,
                value=f"[View Taxon](https://www.inaturalist.org/taxa/{species.get('id')})",
                inline=False
            )

            if image_url:
                embed.set_image(url=image_url)

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"Error fetching species: {e}")

    @app_commands.command(name="setlocation", description="Set your location")
    async def setlocation(self, interaction: discord.Interaction, lat: float, lng: float):
        await self.bot.db.set_location(str(interaction.user.id), lat, lng)

        await interaction.response.send_message(
            "Location saved",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Naturalist(bot))