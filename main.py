import os
import traceback
from typing import Literal, Optional

import discord
from discord import app_commands
from discord.ext import commands

from utils import DataManager

DataManager(
    [
        ("guilds", "data/guilds.json", {}),
        ("users", "data/users.json", {}),
        (
            "config",
            "data/config.json",
            {
                "token": None,
                "giphy_key": None,
                "unsplash_key": None,
                "global_whitelist": [],
                "owners": [],
            },
        ),
        (
            "economy",
            "data/economy.json",
            {
                "hunt_items": {
                    "skunk": {"chance": 20, "price": 500},
                    "pig": {"chance": 15, "price": 1000},
                    "cow": {"chance": 10, "price": 2000},
                    "deer": {"chance": 7, "price": 300},
                    "bear": {"chance": 5, "price": 4000},
                    "junk": {"chance": 2, "price": 250},
                    "treasure": {"chance": 0.5, "price": 100000},
                },
                "fish_items": {
                    "common fish": {"chance": 45, "price": 100},
                    "uncommon fish": {"chance": 30, "price": 200},
                    "rare fish": {"chance": 15, "price": 500},
                    "epic fish": {"chance": 7, "price": 2000},
                    "legendary fish": {"chance": 1, "price": 10000},
                    "junk": {"chance": 0.9, "price": 250},
                    "treasure": {"chance": 0.1, "price": 100000},
                    "seaweed": {"chance": 1, "price": 250},
                },
                "sell_prices": {
                    "common fish": 5,
                    "uncommon fish": 10,
                    "rare fish": 25,
                    "epic fish": 100,
                    "legendary fish": 500,
                    "junk": 15,
                    "treasure": 10000,
                    "seaweed": 15,
                    "skunk": 5,
                    "pig": 10,
                    "cow": 25,
                    "deer": 150,
                    "bear": 200,
                },
            },
        ),
    ]
)

if "fonts" not in os.listdir("."):
    os.mkdir("fonts")

bot = commands.AutoShardedBot(
    command_prefix="'", owner_id=705435835306213418, intents=discord.Intents.all()
)
bot.remove_command("help")


@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game(f"/help | https://discord.gg/VsDDf8YKBV"),
    )

    try:
        for root, _, files in os.walk("extensions"):
            for file in files:
                if file.endswith(".py"):
                    await bot.load_extension(root.replace("\\", ".") + "." + file[:-3])
    except commands.ExtensionAlreadyLoaded:
        pass
    await bot.tree.sync()


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            delete_after=error.retry_after,
            embed=discord.Embed(
                description=f"<:white_cross:1096791282023669860> Wait {error.retry_after:.1f} seconds before using this command again.",
                colour=discord.Colour.red(),
            ),
        )
    else:
        await bot.get_user(bot.owner_id).send(
            embed=discord.Embed(
                title="Error",
                description=f"If this error persists, DM <@705435835306213418> or mail them: `tester69.discord@gmail.com`\n```py\n{traceback.format_exc()}\n```",
                colour=discord.Colour.red(),
            )
        )


@bot.event
async def on_error(event, *args, **kwargs):
    await bot.get_user(bot.owner_id).send(
        embed=discord.Embed(
            title="Error",
            description=f"```py\n{traceback.format_exc()}\n```",
            colour=discord.Colour.red(),
        )
    )


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.reply(
            embed=discord.Embed(
                description=f"<:white_cross:1096791282023669860> Command not found.",
                colour=discord.Colour.red(),
            )
        )
    else:
        await bot.get_user(bot.owner_id).send(
            embed=discord.Embed(
                description=f"If this error persists, DM <@705435835306213418> or mail them: `tester69.discord@gmail.com`\n```py\n{traceback.format_exc()}\n```",
                colour=discord.Colour.red(),
            )
        )


@commands.guild_only()
@commands.is_owner()
async def sync(
    ctx: commands.Context,
    guilds: commands.Greedy[discord.Object],
    spec: Optional[Literal["~", "*", "^"]] = None,
) -> None:
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


if DataManager.get("config", "token") is None:
    print("Please set your bot's token in data/config.json.")
else:
    bot.run(DataManager.get("config", "token"))
