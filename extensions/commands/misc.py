import datetime
import json
import random
from io import BytesIO
from typing import Optional

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from utils import DataManager, Paginator


class misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="source", description="Get the source code for the bot")
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id))
    async def source(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            content="https://github.com/Majestic-dev/Tester69/tree/main", ephemeral=True
        )

    @app_commands.command(
        name="search_giphy", description="Search a gif by keyword from Giphy"
    )
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id))
    @app_commands.describe(search="The keyword you want to search the Gif by")
    async def search_gif(self, interaction: discord.Interaction, search: Optional[str]):
        embed = discord.Embed(title=(f"{search} Gif" if search != None else "Random Gif"), colour=discord.Colour.green())

        if search != None:
            search.replace(" ", "+")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    (f"https://api.giphy.com/v1/gifs/random?api_key="
                    + DataManager.get("config", "giphy_key"))
                    if search is None
                    else (f"http://api.giphy.com/v1/gifs/search?q={search}&api_key="
                    + DataManager.get("config", "giphy_key"))
                ) as response:
                    data = json.loads(await response.text())
                    gif_choice = random.randint(0, 9)
                    embed.set_image(url=data["data"][gif_choice]["images"]["original"]["url"])
            except IndexError:
                response = await session.get(
                    f"https://api.giphy.com/v1/gifs/random?api_key="
                    + DataManager.get("config", "giphy_key")
                )
                data = json.loads(await response.text())
                embed.set_image(url=data["data"]["images"]["original"]["url"])

        embed.set_footer(
            icon_url=interaction.user.avatar,
            text=f"Requested by - {interaction.user} | Powered by Giphy API ❤️",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="search_unsplash", description="Search an image by keyword from Unsplash"
    )
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id))
    @app_commands.describe(search="The keyword you want to search the image by")
    async def search_unsplash(
        self, interaction: discord.Interaction, search: Optional[str]
    ):
        embed = discord.Embed(title=(f"{search} Image" if search != None else "Random Image"), colour=discord.Colour.green())

        if search != None:
            search.replace(" ", "+")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    (f"https://api.unsplash.com/photos/random?client_id="
                    + DataManager.get("config", "unsplash_key"))
                    if search is None
                    else (f"https://api.unsplash.com/search/photos?query={search}&client_id="
                    + DataManager.get("config", "unsplash_key"))
                ) as response:
                    data = json.loads(await response.text())
                    embed.set_image(url=data["urls"]["full"])

                    data = json.loads(await response.text())
                    image_choice = random.randint(0, 9)
                    embed.set_image(url=data["results"][image_choice]["urls"]["full"])
            except IndexError:
                response = await session.get(
                    f"https://api.unsplash.com/photos/random?client_id="
                    + DataManager.get("config", "unsplash_key")
                )
                data = json.loads(await response.text())
                embed.set_image(url=data["urls"]["full"])

        await session.close()
        embed.set_footer(
            icon_url=interaction.user.avatar,
            text=f"Requested by - {interaction.user} | Powered by Unsplash API ❤️",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="cat", description="Get a random cat image")
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id))
    async def cat(self, interaction: discord.Interaction):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.thecatapi.com/v1/images/search") as response:
                data = json.loads(await response.text())
                embed = discord.Embed(title="🐱 Meow", colour=discord.Colour.green())
                embed.url = data[0]["url"]
                embed.set_image(url=data[0]["url"])
                
        embed.set_footer(
            icon_url=interaction.user.avatar,
            text=f"Requested by - {interaction.user} | Powered by The Cat API ❤️",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="dog", description="Get a random dog image")
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id))
    async def dog(self, interaction: discord.Interaction):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.thedogapi.com/v1/images/search") as response:
                data = json.loads(await response.text())
                embed = discord.Embed(title="🐶 Woof", colour=discord.Colour.green())
                embed.url = data[0]["url"]
                embed.set_image(url=data[0]["url"])
        
        embed.set_footer(
            icon_url=interaction.user.avatar,
            text=f"Requested by - {interaction.user} | Powered by The Dog API ❤️",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="dadjoke", description="Get a random dad joke")
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id))
    async def dadjoke(self, interaction: discord.Interaction):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://icanhazdadjoke.com/", headers={"Accept": "text/plain"}
            ) as response:
                data = await response.text()
                
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"🤣 {data}", colour=discord.Colour.green()
            ),
            ephemeral=True,
        )

    @app_commands.command(
        name="wikipedia", description="Get a definition from Wikipedia"
    )
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id))
    @app_commands.describe(
        search="The keyword you want to search the definition from Wikipedia"
    )
    async def wikipedia(self, interaction: discord.Interaction, *, search: str):
        async with aiohttp.ClientSession() as session:
            try:
                response = await session.get(
                    f"https://en.wikipedia.org/api/rest_v1/page/summary/{search}"
                )
                data = json.loads(await response.text())
                embed = discord.Embed(title=f"📚 {search}", colour=discord.Colour.green())
                embed.url = data["content_urls"]["desktop"]["page"]
                embed.description = data["extract"]
                embed.set_footer(
                    icon_url=interaction.user.avatar,
                    text=f"Requested by - {interaction.user} | Powered by Wikipedia API ❤️",
                )
                try:
                    embed.set_thumbnail(url=data["thumbnail"]["source"])
                except KeyError:
                    pass
            except:
                embed = discord.Embed(
                    description="<:white_cross:1096791282023669860> Couldn't find a Wikipedia article with that name",
                    colour=discord.Colour.red(),
                )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="urban", description="Get a definition from Urban Dictionary"
    )
    @app_commands.describe(
        search="The keyword you want to search the definition from The Urban Dictionary"
    )
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id))
    async def urban(self, interaction: discord.Interaction, *, search: str = None):
        embeds = []

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.urbandictionary.com/v0/random" if search is None else f"https://api.urbandictionary.com/v0/define?term={search}") as response:
                for word in json.loads(await response.text())["list"]:
                    try:
                        embed = discord.Embed(
                            title=f"📚 {word['word']}", colour=discord.Colour.green()
                        )
                        embed.url = word["permalink"]
                        embed.description = word["definition"].replace("[", "").replace("]", "")
                        embed.set_footer(
                            icon_url=interaction.user.avatar,
                            text=f"Requested by - {interaction.user} | Powered by Urban Dictionary API ❤️",
                        )
                        embeds.append(embed)
                    except IndexError:
                        embed = discord.Embed(
                            description="<:white_cross:1096791282023669860> Couldn't find a definition for that term",
                            colour=discord.Colour.red(),
                        )
                        
        await Paginator.Simple().paginate(interaction, pages=embeds)

    @app_commands.command(name="github", description="Get a user's GitHub profile")
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id))
    @app_commands.describe(
        search="The GitHub username you want to search the profile of"
    )
    async def github(self, interaction: discord.Interaction, *, search: str):
        async with aiohttp.ClientSession() as session:
            try:
                response = await session.get(f"https://api.github.com/users/{search}")
                data = json.loads(await response.text())
                embed = discord.Embed(title=f"📚 {search}", colour=discord.Colour.green())
                embed.url = data["html_url"]
                if data["bio"] is not None:
                    embed.description = data["bio"]
                embed.set_footer(
                    icon_url=interaction.user.avatar,
                    text=f"Requested by - {interaction.user} | Powered by GitHub API ❤️",
                )
                embed.set_thumbnail(url=data["avatar_url"])
                embed.add_field(name="Followers", value=data["followers"], inline=True)
                embed.add_field(name="Following", value=data["following"], inline=True)
                embed.add_field(
                    name="Public Repos", value=data["public_repos"], inline=True
                )
            except KeyError:
                embed = discord.Embed(colour=discord.Colour.red())
                embed.description = "<:white_cross:1096791282023669860> Couldn't find a GitHub user with that name"
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="weather", description="Get the weather for a location")
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id))
    @app_commands.describe(search="The location you want to search the weather for")
    async def weather(self, interaction: discord.Interaction, *, search: str):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"http://api.openweathermap.org/geo/1.0/direct?q={search}&limit=1&appid="
                    + DataManager.get("config", "weather_api_key")
                ) as location:
                    lat = json.loads(await location.text())[0]["lat"]
                    lon = json.loads(await location.text())[0]["lon"]
                
                async with session.get(
                    f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid="
                    + DataManager.get("config", "weather_api_key")
                ) as response:
                    data = json.loads(await response.text())
                    embed = discord.Embed(
                        title=f"Weather for {search}",
                        description=f"* **Last Updated:** {discord.utils.format_dt(datetime.datetime.fromtimestamp(data['dt']), style='F')}\n"
                        f"* **Sunrise:** {discord.utils.format_dt(datetime.datetime.fromtimestamp(data['sys']['sunrise']), style='T')}\n"
                        f"* **Sunset:** {discord.utils.format_dt(datetime.datetime.fromtimestamp(data['sys']['sunset']), style='T')}\n"
                        f"* **Description:** {data['weather'][0]['description']}\n"
                        f"* **Temperature:** {round(data['main']['temp'] - 273.15)}°C\n"
                        f"* **Feels Like:** {round(data['main']['feels_like'] - 273.15)}°C\n"
                        f"* **Humidity:** {data['main']['humidity']}%\n"
                        f"* **Wind Speed:** {int(data['wind']['speed'] * 1.60934)} km/h ({data['wind']['speed']} mph)\n"
                        f"* **Cloudiness:** {data['clouds']['all']}%",
                        colour=discord.Colour.blurple(),
                    )

                    embed.set_footer(
                        icon_url=interaction.user.avatar,
                        text=f"Requested by - {interaction.user} | Powered by OpenWeatherMap API ❤️",
                    )
                    embed.set_thumbnail(
                        url=f"http://openweathermap.org/img/w/{data['weather'][0]['icon']}.png"
                    )
            except IndexError:
                embed = discord.Embed(colour=discord.Colour.red())
                embed.description = "<:white_cross:1096791282023669860> Couldn't find a location with that name"
            
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="forecast",
        description="Get the weather forecast for a location (in 3 hour intervals)",
    )
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id))
    @app_commands.describe(
        search="The location you want to search the weather forecast for"
    )
    async def forecast(self, interaction: discord.Interaction, *, search: str):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"http://api.openweathermap.org/geo/1.0/direct?q={search}&limit=1&appid="
                    + DataManager.get("config", "weather_api_key")
                ) as location:
                    lat = json.loads(await location.text())[0]["lat"]
                    lon = json.loads(await location.text())[0]["lon"]
                
                async with session.get(
                    f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid="
                    + DataManager.get("config", "weather_api_key")
                ) as response:
                    data = json.loads(await response.text())
                    embed = discord.Embed(
                        title=f"Weather Forecast for {search}",
                        colour=discord.Colour.from_rgb(173, 216, 230),
                    )

                    embed.set_footer(
                        icon_url=interaction.user.avatar,
                        text=f"Requested by - {interaction.user} | Powered by OpenWeatherMap API ❤️",
                    )
                    embed.set_thumbnail(
                        url=f"http://openweathermap.org/img/w/{data['list'][0]['weather'][0]['icon']}.png"
                    )
                    for i in range(0, 5):
                        embed.add_field(
                            name=f"{datetime.datetime.fromtimestamp(data['list'][i]['dt']).strftime('%H:%M')} - {datetime.datetime.fromtimestamp(data['list'][i]['dt']).strftime('%d/%m/%Y')}",
                            value=f"{data['list'][i]['weather'][0]['description']}\n{round(data['list'][i]['main']['temp'] - 273.15)}°C",
                            inline=True,
                        )
            except IndexError:
                embed = discord.Embed(colour=discord.Colour.red())
                embed.description = "<:white_cross:1096791282023669860> Couldn't find a location with that name"
            
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="transcript", description="Get a transcript of a channel"
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id))
    @app_commands.describe(channel="The channel you want to get the transcript of")
    async def transcript(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ):
        await interaction.response.defer(ephemeral=True)

        messages = [message async for message in channel.history(limit=None)]
        transcript = ""

        for message in reversed(messages):
            if message.embeds:
                transcript += (
                    f"\n\n{message.author}#{message.author.discriminator} EMBED\n\n"
                )
                if message.embeds[0].title:
                    transcript += f"Title - {message.embeds[0].title}\n"
                if message.embeds[0].description:
                    transcript += f"Description - {message.embeds[0].description}\n"
                if message.embeds[0].fields:
                    for field in message.embeds[0].fields:
                        transcript += f"{field.name} - {field.value}\n"
                if message.embeds[0].footer:
                    transcript += f"Footer - {message.embeds[0].footer.text}\n"
                if message.embeds[0].image:
                    transcript += f"Image - {message.embeds[0].image.url}\n"
                if message.embeds[0].thumbnail:
                    transcript += f"Thumbnail - {message.embeds[0].thumbnail.url}\n"
                if message.embeds[0].author:
                    transcript += f"Author - {message.embeds[0].author.name}\n"
                if message.embeds[0].url:
                    transcript += f"URL - {message.embeds[0].url}\n"
                transcript += f"Message Link - {message.jump_url}\n\n"
                continue
            if message.attachments:
                transcript += f"\n\n{message.author}#{message.author.discriminator} ATTACHMENT(S)\n\n"
                for attachment in message.attachments:
                    transcript += f"{attachment.url}\n"
                transcript += f"Message Link - {message.jump_url}\n\n"
                continue
            if message.content:
                transcript += f"\n{message.author}#{message.author.discriminator} ({message.author.id}): {message.content}"
                continue

        buffer = BytesIO(transcript.encode("utf8"))
        await channel.send(
            content=f"Transcript for {interaction.channel.mention}",
            file=discord.File(
                fp=buffer, filename=f"transcript-{interaction.channel.name}.txt"
            ),
        )


async def setup(bot):
    await bot.add_cog(misc(bot))
