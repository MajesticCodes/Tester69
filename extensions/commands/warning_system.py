import discord
from discord import app_commands
from discord.ext import commands

from utils import DataManager


class warning_system(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    @app_commands.command(
        name="warn", description="Warns the mentioned user with a custom warning reason"
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild.id, i.user.id))
    @app_commands.describe(
        user="The user to warn",
        reason="The reason for the warning",
    )
    async def warn(
        self, interaction: discord.Interaction, user: discord.Member, reason: str
    ):
        if user.id == interaction.user.id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description="<:white_cross:1096791282023669860> You can't warn yourself",
                    colour=discord.Colour.red(),
                )
            )

        if interaction.user.top_role <= user.top_role:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description="<:white_cross:1096791282023669860> You can't warn your superiors",
                    colour=discord.Colour.red(),
                )
            )

        bot = interaction.guild.get_member(self.bot.user.id)
        if bot.top_role <= user.top_role:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description="<:white_cross:1096791282023669860> I can't warn my superiors",
                    colour=discord.Colour.red(),
                )
            )

        await DataManager.register_warning(
            interaction.guild.id,
            user.id,
            f"{reason} - Warned by {interaction.user.name}",
        )

        self.bot.dispatch(
            "warning",
            guild=interaction.guild,
            warned=user,
            warner=interaction.user,
            reason=reason,
        )

        return await interaction.response.send_message(
            embed=discord.Embed(
                description=f"<:white_checkmark:1096793014287995061> {user.name} has been warned",
                colour=discord.Colour.green(),
            )
        )

    @app_commands.command(name="delwarn", description="Deletes the warning by UUID")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild.id, i.user.id))
    @app_commands.describe(
        uuid="The UUID of the warning to delete, use the `/warnings <user>` command to get the UUID",
    )
    async def delwarn(self, interaction: discord.Interaction, uuid: str):
        delwarn = await DataManager.delete_warning(interaction.guild.id, uuid)

        if delwarn == True:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"<:white_checkmark:1096793014287995061> Deleted warning ```{uuid}```",
                    colour=discord.Colour.green(),
                )
            )
        elif delwarn == False:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"<:white_cross:1096791282023669860> Couldn't find warning with the UUID ```{uuid}```",
                    colour=discord.Colour.orange(),
                )
            )

    @app_commands.command(
        name="warnings", description="get the warning list of the user"
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild.id, i.user.id))
    @app_commands.describe(
        member="The member to get the warnings of",
    )
    async def warnings(self, interaction: discord.Interaction, member: discord.Member):
        warnings = await DataManager.get_user_warnings(interaction.guild.id, member.id)

        if warnings is None or len(warnings) == 0:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"<:white_checkmark:1096793014287995061> {member.mention} has no warnings",
                    colour=discord.Colour.green(),
                )
            )

        e = discord.Embed(
            title="Warnings",
            colour=discord.Colour.orange(),
        )
        for warn in warnings:
            for warn_uuid in warn:
                e.add_field(
                    name=f"UUID: `{warn_uuid}`",
                    value=f"\n{warn[warn_uuid]}",
                    inline=False,
                )
        if member.avatar is None:
            e.set_author(name=member.name, icon_url=member.display_avatar.url)
        else:
            e.set_author(name=member.name, icon_url=member.avatar.url)
        await interaction.response.send_message(embed=e)


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(warning_system(bot))
