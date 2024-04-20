import os
from typing import Optional

import discord
from discord.ext import commands

from utils import DataManager


class owner_only(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    @commands.command(name="add", description="Add set amount of 🪙 to your balance")
    @commands.is_owner()
    async def add(
        self,
        ctx: commands.Context,
        amount: int,
        member: Optional[discord.Member] = None,
    ):
        user_data = await DataManager.get_user_data(
            (member.id) if member else ctx.author.id
        )

        if user_data["balance"] + amount > 92233720368547758071:
            return await ctx.reply(
                embed=discord.Embed(
                    description=(
                        f"<:white_cross:1096791282023669860> That's too much! Please try lowering your needed amount"
                    ),
                    colour=discord.Colour.red(),
                )
            )

        await DataManager.edit_user_data(
            (member.id) if member else ctx.author.id,
            "balance",
            user_data["balance"] + amount,
        )
        return await ctx.reply(
            embed=discord.Embed(
                description=(
                    f"<:white_checkmark:1096793014287995061> Added {amount} 🪙 "
                )
                + (
                    f"to {member.mention}'s bank. Their new balance is {user_data["balance"] + amount} 🪙"
                    if member
                    else f"to your bank. Your new balance is {user_data["balance"] + amount} 🪙"
                ),
                colour=discord.Colour.green(),
            )
        )

    @commands.command(name="add_item", description="Add an item to your inventory")
    @commands.is_owner()
    async def add_item(
        self,
        ctx,
        item_name: str,
        amount: Optional[int] = 1,
        member: Optional[discord.Member] = None,
    ):
        items = DataManager.get("economy", "items")
        if item_name.lower() not in items:
            return await ctx.reply(
                embed=discord.Embed(
                    description=(
                        f"<:white_cross:1096791282023669860> {item_name} does not exist"
                    ),
                    colour=discord.Colour.red(),
                )
            )

        if member == None:
            member = ctx.author

        await DataManager.edit_user_inventory(member.id, item_name, amount)

        if member == ctx.author:
            return await ctx.reply(
                embed=discord.Embed(
                    description=("<:white_checkmark:1096793014287995061> ")
                    + ("Added " if amount > 1 else "Removed ")
                    + (f"{abs(amount)} {items[item_name.lower()]["emoji"]} {item_name}")
                    + ("s to your inventory" if amount > 1 else " to your inventory"),
                    colour=discord.Colour.green(),
                )
            )

        else:
            return await ctx.reply(
                embed=discord.Embed(
                    description=("<:white_checkmark:1096793014287995061>")
                    + ("Added " if amount >= 1 else "Removed ")
                    + (f"{abs(amount)} {items[item_name.lower()]["emoji"]} {item_name}")
                    + (
                        f"s to {member.mention}'s inventory"
                        if amount > 1
                        else f" to {member.mention}'s inventory"
                    ),
                    colour=discord.Colour.green(),
                )
            )

    @commands.command(name="reload", description="Reload the cogs in the bot")
    @commands.is_owner()
    async def reload(self, ctx):
        for root, _, files in os.walk("extensions"):
            for file in files:
                if file.endswith(".py"):
                    extension_name = root.replace("\\", ".") + "." + file[:-3]
                    if extension_name in self.bot.extensions:
                        await self.bot.unload_extension(extension_name)
                    try:
                        await self.bot.load_extension(extension_name)
                    except discord.ext.commands.errors.ExtensionAlreadyLoaded:
                        print(f"Extension {extension_name} is already loaded.")
        await ctx.reply(
            embed=discord.Embed(
                description="<:white_checkmark:1096793014287995061> Reloaded all cogs",
                colour=discord.Colour.green(),
            )
        )
        return await self.bot.tree.sync()

    @commands.command(name="skipcooldown", description="Skip the cooldown of a command")
    @commands.is_owner()
    async def skipcooldown(
        self, ctx, command: str, member: Optional[discord.Member] = None
    ):
        if member == None:
            if command == "all":
                await DataManager.remove_cooldown(ctx.author.id, "all")
                return await ctx.reply(
                    embed=discord.Embed(
                        description=(
                            f"<:white_checkmark:1096793014287995061> Skipped all cooldowns"
                        ),
                        colour=discord.Colour.green(),
                    )
                )

            user_data = await DataManager.get_user_data(ctx.author.id)
            if command not in user_data["cooldowns"]:
                return await ctx.reply(
                    embed=discord.Embed(
                        description=(
                            f"<:white_cross:1096791282023669860> {command} command is not on cooldown or does not exist"
                        ),
                        colour=discord.Colour.red(),
                    )
                )

            await DataManager.remove_cooldown(ctx.author.id, command)

            return await ctx.reply(
                embed=discord.Embed(
                    description=(
                        f"<:white_checkmark:1096793014287995061> Skipped cooldown for {command} command"
                    ),
                    colour=discord.Colour.green(),
                )
            )

        else:
            if command == "all":
                await DataManager.remove_cooldown(member.id, "all")
                return await ctx.reply(
                    embed=discord.Embed(
                        description=(
                            f"<:white_checkmark:1096793014287995061> Skipped all cooldowns for {member.mention}"
                        ),
                        colour=discord.Colour.green(),
                    )
                )

            user_data = await DataManager.get_user_data(member.id)
            if command not in user_data["cooldowns"]:
                return await ctx.reply(
                    embed=discord.Embed(
                        description=(
                            f"<:white_cross:1096791282023669860> {command} command is not on cooldown or does not exist"
                        ),
                        colour=discord.Colour.red(),
                    )
                )

            await DataManager.remove_cooldown(member.id, command)

            return await ctx.reply(
                embed=discord.Embed(
                    description=(
                        f"<:white_checkmark:1096793014287995061> Skipped cooldown for {command} command for {member.name}"
                    ),
                    colour=discord.Colour.green(),
                )
            )


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(owner_only(bot))
