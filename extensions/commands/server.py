from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from utils import Paginator


class server_views(discord.ui.View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @discord.ui.button(
        style=discord.ButtonStyle.primary, label="View Roles", emoji="👑"
    )
    async def view_roles(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        roles = interaction.guild.roles
        roles = sorted(roles, key=lambda x: x.position, reverse=True)
        role_list = "\n".join(
            [f"{role.mention}" for role in roles if role.name != "@everyone"]
        )
        embed = discord.Embed(
            title=f"{interaction.guild.name}'s Roles (Total: {len(roles) - 1})",
            description=role_list,
            colour=discord.Colour.blurple(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(
        style=discord.ButtonStyle.primary, label="View Emojis", emoji="😝"
    )
    async def view_emojis(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        emojis = interaction.guild.emojis
        emoji_list = "\n".join(
            [f"{emoji} - {emoji.name} ({emoji.id})" for emoji in emojis]
        )
        embed = discord.Embed(
            title=f"{interaction.guild.name}'s Emojis (Total: {len(emojis)})",
            description=emoji_list,
            colour=discord.Colour.blurple(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(
        style=discord.ButtonStyle.primary, label="View Members", emoji="👥"
    )
    async def view_members(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer(ephemeral=True)
        embeds = []
        for i in range(0, len(interaction.guild.members), 10):
            members = interaction.guild.members[i : i + 10]
            member_list = "\n".join([f"{member.mention}" for member in members])
            embed = discord.Embed(
                title=f"{interaction.guild.name}'s Members (Total: {len(interaction.guild.members)}). Page {i // 10 + 1}/{len(interaction.guild.members) // 10 + 1}",
                description=member_list,
                colour=discord.Colour.blurple(),
            )
            embeds.append(embed)

        await Paginator.Simple(ephemeral=True).paginate(interaction, embeds)


class server(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="serverinfo", description="Get information about the server"
    )
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 20, key=lambda i: (i.guild.id, i.user.id))
    async def serverinfo(
        self, interaction: discord.Interaction, ephemeral: bool = True
    ):
        guild = interaction.guild

        embed = discord.Embed(
            description=f"* **Server Name:** {guild.name}\n"
            f"* **Server ID:** `{guild.id}`\n"
            f"* **Server Owner:** {guild.owner.mention}\n"
            f"* **Created At:** {discord.utils.format_dt(guild.created_at, style='F')}\n"
            f"* **Verification Level:** {guild.verification_level}\n"
            f"* **Boost Level:** {guild.premium_tier}\n"
            f"* **Boosts:** {guild.premium_subscription_count}\n"
            f"* **Categories:** {len(guild.categories)}\n"
            f"* **Text Channels:** {len(guild.text_channels)}\n"
            f"* **Voice Channels:** {len(guild.voice_channels)}\n"
            f"* **Members:** {guild.member_count}\n",
            colour=discord.Colour.random(),
        )

        embed.set_thumbnail(url=guild.icon)
        embed.set_image(url=guild.banner)
        embed.set_author(name=guild.name, icon_url=guild.icon)

        await interaction.response.send_message(
            embed=embed, ephemeral=ephemeral, view=server_views(self.bot)
        )

    @app_commands.command(
        name="membercount", description="Get the member count of the server"
    )
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 20, key=lambda i: (i.guild.id, i.user.id))
    async def membercount(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(
            title=f"Member Count",
            description=f"Total Members: {guild.member_count}",
            colour=discord.Colour.blurple(),
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="servericon", description="Get the icon of the server")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 20, key=lambda i: (i.guild.id, i.user.id))
    async def servericon(
        self, interaction: discord.Interaction, ephemeral: bool = True
    ):
        embed = discord.Embed(
            title=f"{interaction.guild.name}'s Icon",
            colour=discord.Colour.darker_gray(),
        )
        embed.set_author(
            name=f"{interaction.guild.name}", icon_url=interaction.guild.icon
        )
        embed.set_image(url=interaction.guild.icon)
        await interaction.response.send_message(embed=embed, ephemeral=ephemeral)

    @app_commands.command(
        name="serverbanner", description="Get the banner of the current server"
    )
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 20, key=lambda i: (i.guild.id, i.user.id))
    async def serverbanner(
        self, interaction: discord.Interaction, ephemeral: bool = True
    ):
        if interaction.guild.banner is not None:
            embed = discord.Embed(
                title=f"{interaction.guild.name}'s Banner",
                colour=discord.Colour.darker_gray(),
            )
            embed.set_author(
                name=f"{interaction.guild.name}", icon_url=interaction.guild.icon
            )
            embed.set_image(url=interaction.guild.banner)
            await interaction.response.send_message(embed=embed, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="<:white_cross:1096791282023669860> This server does not have a banner",
                    colour=discord.Colour.red(),
                ),
                ephemeral=True,
            )

    @app_commands.command(name="userinfo", description="Get information about a user")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 20, key=lambda i: (i.guild.id, i.user.id))
    @app_commands.describe(user="The user to get information about")
    async def userinfo(
        self,
        interaction: discord.Interaction,
        user: Optional[discord.User] = None,
        ephemeral: bool = True,
    ):
        if user is None:
            user = interaction.user
        else:
            user = await self.bot.fetch_user(user.id)

        def guess_user_nitro_status(user: discord.Member):
            if isinstance(user, discord.Member):
                has_emote_status = any(
                    [
                        a.emoji.is_custom_emoji()
                        for a in user.activities
                        if getattr(a, "emoji", None)
                    ]
                )

                return any(
                    [
                        user.display_avatar.is_animated(),
                        has_emote_status,
                        user.premium_since,
                        user.guild_avatar,
                    ]
                )

        def boosting_server(user: discord.Member):
            for member in interaction.guild.premium_subscribers:
                if member.id == user.id:
                    return True
                else:
                    return False

        badges = []

        if user.public_flags.active_developer:
            badges.append("<:active_dev:1132653957110566982>")
        if user.public_flags.bug_hunter:
            badges.append("<:bughunter:1132657021724926074>")
        if user.public_flags.bug_hunter_level_2:
            badges.append("<:bughuntergold:1132656646896767056>")
        if user.public_flags.discord_certified_moderator:
            badges.append("<:verifiedmoderator:1132656453971361802>")
        if user.public_flags.early_supporter:
            badges.append("<:Earlysupporter:1132657480263016520>")
        if user.public_flags.early_verified_bot_developer:
            badges.append("<:earlybotdev:1132657476936925225>")
        if user.public_flags.hypesquad_balance:
            badges.append("<:balance:1132657481676509235>")
        if user.public_flags.hypesquad_bravery:
            badges.append("<:hypesquadbravery:1132657486063738910>")
        if user.public_flags.hypesquad_brilliance:
            badges.append("<:brilliance:1132657484570570843>")
        if user.public_flags.partner:
            badges.append("<:partner:1132657491260493865>")
        if user.public_flags.staff:
            badges.append("<:staff:1132657487468830810>")
        if guess_user_nitro_status(user):
            badges.append("<:nitro:1132663522162122812>")
        if boosting_server(user):
            badges.append("<:boosting:1134076723508559893>")

        embed = discord.Embed(
            description=f"* **Username**: {user.name}\n"
            f"* **Display Name**: {user.display_name}\n"
            f"* **User ID**: `{user.id}`\n"
            f"* **Bot**: {'Yes' if user.bot else 'No'}\n"
            f"* **Account Created**: {discord.utils.format_dt(user.created_at, style='F')}\n"
            f"* **Joined At**: {discord.utils.format_dt(interaction.guild.get_member(user.id).joined_at, style='F')}\n"
            f"* **Badges**: {', '.join(badges) if badges else 'No Badges'}\n"
            f"* **Roles**: {', '.join([role.mention for role in interaction.guild.get_member(user.id).roles if role.name != '@everyone'])}\n",
            colour=discord.Colour.blurple(),
        )

        if user.avatar is not None:
            embed.set_thumbnail(url=user.avatar.url)

        await interaction.response.send_message(embed=embed, ephemeral=ephemeral)

    @app_commands.command(
        name="avatar", description="Get the avatar of an user or yourself"
    )
    @app_commands.checks.cooldown(1, 20, key=lambda i: (i.guild.id, i.user.id))
    @app_commands.describe(user="The user to get the avatar of, defaults to yourself")
    async def avatar(
        self,
        interaction: discord.Interaction,
        user: Optional[discord.User] = None,
        ephemeral: bool = True,
    ):
        if user is None:
            user = interaction.user

        embed = discord.Embed(
            title=f"{user.name}'s Avatar", colour=discord.Colour.darker_gray()
        )
        embed.set_author(name=f"{user.name}#{user.discriminator}", icon_url=user.avatar)
        embed.set_image(url=user.avatar)
        await interaction.response.send_message(embed=embed, ephemeral=ephemeral)

    @app_commands.command(name="info", description="Get information about a channel")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 20, key=lambda i: (i.guild.id, i.user.id))
    @app_commands.describe(channel="The channel to get information about")
    async def channelinfo(
        self,
        interaction: discord.Interaction,
        channel: Optional[discord.TextChannel] = None,
        ephemeral: bool = True,
    ):
        if channel is None:
            channel = interaction.channel

        embed = discord.Embed(
            description=f"* **Channel Name:** {channel.name}\n"
            f"* **Channel ID:** `{channel.id}`\n"
            f"* **Created At:** {discord.utils.format_dt(channel.created_at, style='F')}\n"
            f"* **Channel Type:** {channel.type}\n"
            f"* **NSFW Channel:** {'Yes' if channel.is_nsfw() else 'No'}\n"
            f"* **Channel Position:** {channel.position}\n"
            f"* **Slowmode:** {f'{channel.slowmode_delay} Seconds' if channel.slowmode_delay > 0 else 'No Slowmode'}\n"
            f"* **Channel Topic:** {channel.topic if channel.topic else 'No Topic'}\n",
            colour=discord.Colour.random(),
        )
        embed.set_thumbnail(url=channel.guild.icon)

        await interaction.response.send_message(embed=embed, ephemeral=ephemeral)


async def setup(bot):
    await bot.add_cog(server(bot))
