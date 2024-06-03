import datetime
import os
import re
from io import BytesIO
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image, UnidentifiedImageError

from utils import DataManager


class logging(commands.GroupCog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="set_channel",
        description="Set where all server logs will be sent and optionally where all blocked words will be sent",
    )
    @app_commands.describe(
        logging_channel="Choose the channel where all server logs will be sent",
        blocked_words_channel="Choose the channel where all blocked words will be sent",
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id))
    async def set_logs_channel(
        self,
        interaction: discord.Interaction,
        logging_channel: discord.TextChannel,
        blocked_words_channel: Optional[discord.TextChannel] = None,
    ):
        if blocked_words_channel == None:
            data = await DataManager.get_filter_data(interaction.guild.id)
            if data["channel_id"] != None:
                await DataManager.edit_filter_data(
                    interaction.guild.id, "channel_id", None
                )

            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"<:white_checkmark:1096793014287995061> Set the logging channel to {logging_channel.mention}",
                    colour=discord.Colour.green(),
                )
            )

            await DataManager.edit_guild_data(
                interaction.guild.id, "logs_channel_id", logging_channel.id
            )

        elif blocked_words_channel != None:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"<:white_checkmark:1096793014287995061> Set the logging channel to {logging_channel.mention} and the blocked words channel to {blocked_words_channel.mention}",
                    colour=discord.Colour.green(),
                )
            )

            await DataManager.edit_guild_data(
                interaction.guild.id, "logs_channel_id", logging_channel.id
            )

            await DataManager.edit_filter_data(
                interaction.guild.id, "channel_id", blocked_words_channel.id
            )

    @app_commands.command(name="disable", description="Disable logging for this server")
    @app_commands.checks.has_permissions(administrator=True)
    async def disable_logs(self, interaction: discord.Interaction):
        guild_data = await DataManager.get_guild_data(interaction.guild.id)
        logs_channel = self.bot.get_channel(guild_data["logs_channel_id"])

        if logs_channel == None:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=discord.Embed(
                    description="<:white_cross:1096791282023669860> Logging is already disabled",
                    colour=discord.Colour.red(),
                ),
            )

        else:
            await DataManager.edit_guild_data(
                interaction.guild.id, "logs_channel_id", None
            )
            return await interaction.response.send_message(
                ephemeral=True,
                embed=discord.Embed(
                    title="Logging Disabled",
                    description="Logging has been disabled for this server",
                    colour=discord.Colour.red(),
                ),
            )

    # Member Join Listener
    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_data = await DataManager.get_guild_data(member.guild.id)
        logs_channel = self.bot.get_channel(guild_data["logs_channel_id"])

        if member.guild.get_member(member.id) == None:
            return

        if logs_channel == None:
            return

        join = discord.Embed(
            title="Member Joined",
            description=f"{member.mention} has joined the server",
            colour=discord.Colour.green(),
        )
        join.add_field(
            name="Account Created",
            value=discord.utils.format_dt(member.created_at, style="F"),
        )
        join.set_author(icon_url=member.display_avatar, name=member)
        join.set_footer(text=f"ID: {member.id}")
        await logs_channel.send(embed=join)

    # Member Leave Listener
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild_data = await DataManager.get_guild_data(member.guild.id)
        logs_channel = self.bot.get_channel(guild_data["logs_channel_id"])

        if logs_channel == None:
            return

        leave = discord.Embed(
            title="Member Left",
            description=f"{member.mention} Has left the server",
            colour=discord.Colour.red(),
        )
        leave.set_author(icon_url=member.display_avatar, name=member)
        leave.set_footer(text=f"ID: {member.id}")
        await logs_channel.send(embed=leave)

    # Warning Listener
    @commands.Cog.listener()
    async def on_warning(
        self,
        guild: discord.Guild,
        warned: discord.Member,
        warner: discord.Member,
        reason: str,
    ):
        guild_data = await DataManager.get_guild_data(guild.id)
        logs_channel = self.bot.get_channel(guild_data["logs_channel_id"])

        if logs_channel == None:
            return

        warning = discord.Embed(
            title="Member Warned",
            description=f"{warned.mention} Has been warned by {warner.mention}",
            colour=discord.Colour.red(),
        )
        warning.add_field(name="Reason", value=f"```{reason}```")
        warning.set_author(icon_url=warned.display_avatar, name=warned)
        warning.set_footer(text=f"ID: {warned.id}")
        await logs_channel.send(embed=warning)

    # Member Timeout Listener
    @commands.Cog.listener()
    async def on_timeout(
        self,
        guild: discord.Guild,
        timeouter: discord.Member,
        timeouted: discord.Member,
        timedout_until: int,
        reason: str,
    ):
        guild_data = await DataManager.get_guild_data(guild.id)
        logs_channel = self.bot.get_channel(guild_data["logs_channel_id"])

        if logs_channel == None:
            return

        timeout = discord.Embed(
            title="Member Timed Out",
            description=f"{timeouted.mention} Has been timed out by {timeouter.mention}",
            colour=discord.Colour.red(),
        )
        timeout.add_field(name="Reason", value=f"```{reason}```")
        timeout.add_field(
            name="Timed Out Until",
            value=discord.utils.format_dt(
                discord.utils.utcnow() + datetime.timedelta(seconds=timedout_until),
                "F",
            ),
        )
        timeout.set_author(icon_url=timeouted.display_avatar, name=timeouted)
        timeout.set_footer(text=f"ID: {timeouted.id}")
        await logs_channel.send(embed=timeout)

    # Member Kick Listener
    @commands.Cog.listener()
    async def on_kick(
        self, kicker: discord.User, guild: discord.Guild, user: discord.User
    ):
        guild_data = await DataManager.get_guild_data(guild.id)
        logs_channel = self.bot.get_channel(guild_data["logs_channel_id"])

        if logs_channel == None:
            return

        kick = discord.Embed(
            title="Member Kicked",
            description=f"{user.mention} Has been kicked by {kicker.mention} from the server",
            colour=discord.Colour.red(),
        )
        kick.set_author(icon_url=user.display_avatar, name=user)
        kick.set_footer(text=f"ID: {user.id}")
        await logs_channel.send(embed=kick)

    # Member Ban Listener
    @commands.Cog.listener()
    async def on_ban(
        self,
        guild: discord.Guild,
        banner: discord.User,
        banned: discord.User,
        reason: str,
    ):
        guild_data = await DataManager.get_guild_data(guild.id)
        logs_channel = self.bot.get_channel(guild_data["logs_channel_id"])

        if logs_channel == None:
            return

        ban = discord.Embed(
            title="Member Banned",
            description=f"{banned.mention} Has been banned by {banner} from the server\n\nReason: `{reason}`",
            colour=discord.Colour.red(),
        )
        ban.set_author(icon_url=banned.display_avatar, name=banned)
        ban.set_footer(text=f"ID: {banned.id}")
        await logs_channel.send(embed=ban)

    # Member Unban Listener
    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        guild_data = await DataManager.get_guild_data(guild.id)
        logs_channel = self.bot.get_channel(guild_data["logs_channel_id"])

        if logs_channel == None:
            return

        unban = discord.Embed(
            title="Member Unbanned",
            description=f"{user.mention} Has been unbanned from the server",
            colour=discord.Colour.green(),
        )
        unban.set_author(icon_url=user.display_avatar, name=user)
        unban.set_footer(text=f"ID: {user.id}")
        await logs_channel.send(embed=unban)

    # Member Update Listener
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        guild_data = await DataManager.get_guild_data(before.guild.id)
        logs_channel = self.bot.get_channel(guild_data["logs_channel_id"])

        if logs_channel == None:
            return

        update = discord.Embed(
            description=f"{after.mention} has been updated",
            colour=discord.Colour.gold(),
        )

        nick = before.nick
        if nick == None:
            nick = before.name
        nick2 = after.nick
        if nick2 == None:
            nick2 = after.name

        if before.roles != after.roles:
            update.add_field(
                name="Member Roles Updated",
                value=f"**Before: `{', '.join([role.name for role in before.roles])}`**\n"
                f"**After: `{', '.join([role.name for role in after.roles])}`**\n"
                + (
                    f"**Roles Added: `{', '.join([role.name for role in set(after.roles) - set(before.roles)])}`**\n"
                    if len(set(after.roles) - set(before.roles)) > 0
                    else f"**Roles Removed: `{', '.join([role.name for role in set(before.roles) - set(after.roles)])}`**\n"
                ),
            )

        if before.nick != after.nick:
            update.add_field(
                name="Member Nickname Updated",
                value=f"**Before: {nick} \nAfter: {nick2}**",
            )

        if before.name != after.name:
            update.add_field(
                name="Member Username Updated",
                value=f"**Before: {before.name} \nAfter: {after.name}**",
            )

        if len(update.fields) <= 0:
            return

        update.set_author(icon_url=after.display_avatar, name=after)
        update.set_footer(text=f"ID: {before.id}")
        return await logs_channel.send(embed=update)

    # Role Create Listener
    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        guild_data = await DataManager.get_guild_data(role.guild.id)
        logs_channel = self.bot.get_channel(guild_data["logs_channel_id"])

        if logs_channel == None:
            return

        create = discord.Embed(
            title="Role Created",
            description=f"{role.name} Role has been created",
            colour=discord.Colour.green(),
        )
        create.set_author(icon_url=role.guild.icon, name=role.guild)
        create.set_footer(text=f"Role ID: {role.id}")
        await logs_channel.send(embed=create)

    # Role Delete Listener
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        guild_data = await DataManager.get_guild_data(role.guild.id)
        logs_channel = self.bot.get_channel(guild_data["logs_channel_id"])

        if logs_channel == None:
            return

        delete = discord.Embed(
            title="Role Deleted",
            description=f"{role.name} Role has been deleted",
            colour=discord.Colour.red(),
        )
        delete.set_author(icon_url=role.guild.icon, name=role.guild)
        delete.set_footer(text=f"Role ID: {role.id}")
        await logs_channel.send(embed=delete)

    # Role Update Listener
    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        guild_data = await DataManager.get_guild_data(before.guild.id)
        logs_channel = self.bot.get_channel(guild_data["logs_channel_id"])

        if logs_channel == None:
            return

        update = discord.Embed(
            description=f"{after.mention} Role has been updated",
            colour=discord.Colour.gold(),
        )

        if before.name != after.name:
            update.add_field(
                name=f"Role Name",
                value=f"**Before: {before.name} \nAfter: {after.name}**",
            )
        if before.colour != after.colour:
            update.add_field(
                name=f"Role Colour RGB Value",
                value=f"**Before: {before.colour} \nAfter: {after.colour}**",
            )
        if before.hoist != after.hoist:
            update.add_field(
                name=f"Role Displayed Separately From Others",
                value=f"**Before: {before.hoist} \nAfter: {after.hoist}**",
            )
        if before.mentionable != after.mentionable:
            update.add_field(
                name=f"Role Mentionable By Anyone",
                value=f"**Before: {before.mentionable} \nAfter: {after.mentionable}**",
            )
        if before.display_icon != after.display_icon:
            update.add_field(
                name=f"Role Display Icon",
                value=f"**Before: {before.display_icon} \nAfter: {after.display_icon}**",
            )
        if len(update.fields) <= 0:
            return
        update.set_author(icon_url=before.guild.icon, name=before.guild)
        update.set_footer(text=f"Role ID: {before.id}")
        return await logs_channel.send(embed=update)

    # Voice Channel Listener
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        guild_data = await DataManager.get_guild_data(member.guild.id)
        logs_channel = self.bot.get_channel(guild_data["logs_channel_id"])

        if logs_channel == None:
            return

        voice = discord.Embed(
            description=f"{member.mention} Voice channel updated",
            colour=discord.Colour.gold(),
        )

        if before.channel == None and after.channel != None:
            voice.add_field(
                name="Voice Channel Joined",
                value=f"**{member.mention} Joined {after.channel.mention} voice channel**",
            )
        if before.channel != None and after.channel == None:
            voice.add_field(
                name="Voice Channel Left",
                value=f"**{member.mention} Left {before.channel.mention} voice channel**",
            )
        if (
            before.channel != None
            and before.channel != after.channel
            and after.channel != None
        ):
            voice.add_field(
                name="Voice Channel Moved",
                value=f"**{member.mention} Swithced voice channels {before.channel.mention} -> {after.channel.mention}**",
            )
        if before.mute == False and after.mute == True:
            voice.add_field(
                name="Voice Muted By Admin",
                value=f"**{member.mention} Was muted by an admin**",
            )
        if before.mute == True and after.mute == False:
            voice.add_field(
                name="Voice Unmuted By Admin",
                value=f"**{member.mention} Was unmuted by an admin**",
            )
        if before.deaf == False and after.deaf == True:
            voice.add_field(
                name="Voice Deafened By Admin",
                value=f"**{member.mention} Was deafened by an admin**",
            )
        if before.deaf == True and after.deaf == False:
            voice.add_field(
                name="Voice Undeafened By Admin",
                value=f"**{member.mention} Was undeafened by an admin**",
            )
        if len(voice.fields) <= 0:
            return
        voice.set_author(icon_url=member.display_avatar, name=member)
        voice.set_footer(text=f"ID: {member.id}")
        return await logs_channel.send(embed=voice)

    # Blacklisted Word Listener
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.channel.type == discord.channel.ChannelType.private:
            return

        filtered_words_data = await DataManager.get_filter_data(message.guild.id)
        words_in_blacklist = [
            re.sub(r"\W+", " ", word.lower()).strip()
            for word in filtered_words_data["blacklisted_words"]
        ]
        content = re.sub(r"\W+", " ", message.content.lower().strip())

        if (
            filtered_words_data["whitelist"] is None
            or message.author.id in filtered_words_data["whitelist"]
            or any(
                role.id in filtered_words_data["whitelist"]
                for role in message.author.roles
            )
        ):
            return

        if any(word in content for word in words_in_blacklist) and not (
            message.author.guild_permissions.manage_messages
            or message.author.guild_permissions.administrator
        ):
            await message.delete()

    # Message Edit Logs
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.channel.type == discord.channel.ChannelType.private:
            return

        guild_data = await DataManager.get_guild_data(after.guild.id)
        logs_channel = self.bot.get_channel(guild_data["logs_channel_id"])
        filtered_words_data = await DataManager.get_filter_data(after.guild.id)
        blocked_words_channel = self.bot.get_channel(filtered_words_data["channel_id"])
        content = after.content.lower()

        words_in_blacklist = [
            re.sub(r"\W+", " ", word.lower()).strip()
            for word in filtered_words_data["blacklisted_words"]
        ]
        content = re.sub(r"\W+", " ", after.content.lower().strip())

        if before.author.bot and before.channel != logs_channel:
            return

        if before.is_system() == True:
            return

        if logs_channel == None:
            return

        if before.author.id in filtered_words_data["whitelist"] or any(
            role.id in filtered_words_data["whitelist"] for role in before.author.roles
        ):
            return

        if (
            any(word in content for word in words_in_blacklist)
            and blocked_words_channel != None
        ):
            try:
                return await after.delete()
            except discord.errors.NotFound:
                return

        edit = discord.Embed(
            description=f"**Message Edited in {before.channel.mention}** [Jump to Message]({before.jump_url})",
            colour=discord.Colour.orange(),
        )

        if (
            before.flags.suppress_embeds is False
            and after.flags.suppress_embeds is True
        ):
            embeds = before.embeds[0]
            return await logs_channel.send(embed=embeds)

        if len(before.content or after.content) >= 1024:
            buffer = BytesIO(
                f"Before: {before.content}\nAfter: {after.content}".encode("utf8")
            )
            embed = discord.Embed(
                title="Message Edit (Too Long)",
                description=f"**Message Edited in {before.channel.mention}** [Jump to Message]({before.jump_url})",
                colour=discord.Colour.orange(),
            )
            embed.set_author(icon_url=after.author.avatar, name=after.author)
            await logs_channel.send(
                embed=embed,
                file=discord.File(fp=buffer, filename=f"{after.author.id}_edit.txt"),
            )

        if before.content != after.content:
            edit.add_field(
                name="**Before**",
                value=f"{before.content}",
                inline=True,
            )

            edit.add_field(
                name="**After**",
                value=f"{after.content}",
                inline=True,
            )

        if len(after.attachments) >= 1:
            edit.add_field(
                name="Attachments",
                value=f"**{', '.join([attachment.url for attachment in after.attachments])}**",
                inline=False,
            )

        if len(after.stickers) >= 1:
            edit.add_field(
                name="Stickers",
                value=f"**{', '.join([sticker.url for sticker in after.stickers])}**",
                inline=False,
            )

        if before.pinned != after.pinned:
            edit.add_field(
                name="Pinned",
                value=f"**Before:** {before.pinned}\n**After:** {after.pinned}",
                inline=True,
            )
        if len(edit.fields) <= 0:
            return

        edit.set_author(icon_url=after.author.avatar, name=f"{before.author}")
        edit.set_footer(text=f"Author ID: {before.author.id}")
        await logs_channel.send(embed=edit)

    # Delete Logs
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if (
            message.author.bot
            and message.embeds == False
            or message.is_system() == True
            or message.channel.type == discord.channel.ChannelType.private
        ):
            return

        if len(message.content) >= 1024:
            buffer = BytesIO(message.content.encode("utf8"))
            embed = discord.Embed(
                title="Message Deleted (Too Long)",
                description=f"**Message sent by {message.author.mention} Deleted in {message.channel.mention}**",
                colour=discord.Colour.orange(),
            )
            embed.set_author(
                icon_url=message.author.display_avatar, name=message.author
            )
            await message.channel.send(
                embed=embed,
                file=discord.File(
                    fp=buffer, filename=f"{message.author}({message.author.id}).txt"
                ),
            )

        guild_data = await DataManager.get_guild_data(message.guild.id)
        logs_channel = self.bot.get_channel(guild_data["logs_channel_id"])
        filtered_words_data = await DataManager.get_filter_data(message.guild.id)
        blocked_words_channel = self.bot.get_channel(filtered_words_data["channel_id"])

        if message.author.bot and message.channel != logs_channel:
            return

        if logs_channel == None:
            return

        words_in_blacklist = [
            re.sub(r"\W+", " ", word.lower()).strip()
            for word in filtered_words_data["blacklisted_words"]
        ]
        content = re.sub(r"\W+", " ", message.content.lower().strip())
        bad_words_said = [word for word in words_in_blacklist if word in content]

        if (
            message.author.bot == True
            and message.embeds
            and message.channel == logs_channel
        ):
            embed = message.embeds[0]
            return await logs_channel.send(content=f"{message.content}", embed=embed)

        if message.embeds:
            embed = message.embeds[0]
            return await logs_channel.send(
                content=f"Embed sent by {message.author} deleted in {message.channel.mention}",
                embed=embed,
            )

        embed = discord.Embed(
            description=f"**Message sent by {message.author.mention} Deleted in {message.channel.mention}**",
            colour=discord.Colour.orange(),
        )
        embed.set_author(
            icon_url=message.author.display_avatar, name=f"{message.author}"
        )
        embed.set_footer(
            text=f"Author ID: {message.author.id} | Message ID: {message.id}"
        )

        if len(message.content) >= 1024:
            buffer = BytesIO(message.content.encode("utf8"))

            embed = discord.Embed(
                title="Message Deleted (Too Long)",
                description=f"**Message sent by {message.author.mention} Deleted in {message.channel.mention}**",
                colour=discord.Colour.orange(),
            )
            await logs_channel.send(
                embed=embed,
                file=discord.File(
                    fp=buffer, filename=f"{message.author}({message.author.id}).txt"
                ),
            )

        if len(message.content) > 0:
            embed.add_field(name="**Content**", value=f"{message.content}")
        if any(word in content for word in words_in_blacklist):
            if not any(
                role.id in filtered_words_data["whitelist"]
                for role in message.author.roles
            ):
                embed.add_field(name="**Reason**", value="Blacklisted Word(s)")
                embed.add_field(
                    name="**Detailed Reason**", value=f"`{'`, `'.join(bad_words_said)}`"
                )
            else:
                pass
        if len(message.attachments) > 1:
            embed.add_field(
                name="Attachments",
                value=f"**{', '.join([attachment.url for attachment in message.attachments])}**",
                inline=False,
            )
        elif len(message.attachments) == 1:
            try:
                i = 0
                while not image_data and i < 3:
                    try:
                        image_data = await message.attachments[0].read()
                    except discord.errors.HTTPException:
                        i += 1

                if image_data:
                    image = Image.open(BytesIO(image_data))
                    buffer = BytesIO()
                    image.save(buffer, format="PNG")
                    buffer.seek(0)
                    f = discord.File(fp=buffer, filename="image.png")
                    embed.set_image(url="attachment://image.png")
                else:
                    embed.set_image(url=message.attachments[0].url)
                    return await logs_channel.send(embed=embed)
                
                return await logs_channel.send(embed=embed, file=f)
            except UnidentifiedImageError:
                embed.set_image(url=message.attachments[0].url)
                return await logs_channel.send(embed=embed)
            
        if len(message.stickers) >= 1:
            embed.add_field(
                name="Stickers",
                value=f"**{', '.join([sticker.url for sticker in message.stickers])}**",
                inline=False,
            )

        if (
            any(word in content for word in words_in_blacklist)
            and blocked_words_channel != None
            and not any(
                role.id in filtered_words_data["whitelist"]
                for role in message.author.roles
            )
        ):
            await blocked_words_channel.send(embed=embed)
        else:
            await logs_channel.send(embed=embed)

    # Channel Create Listener
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        guild_data = await DataManager.get_guild_data(channel.guild.id)
        logs_channel = self.bot.get_channel(guild_data["logs_channel_id"])

        if logs_channel == None:
            return

        embed = discord.Embed(
            title="Channel Created",
            description=f"Created {channel.mention} channel",
            colour=discord.Colour.green(),
        )

        embed.set_author(name=channel.guild.name, icon_url=channel.guild.icon)
        embed.set_footer(text=f"Channel ID: {channel.id}")

        await logs_channel.send(embed=embed)

    # Channel Delete Listener
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        guild_data = await DataManager.get_guild_data(channel.guild.id)
        logs_channel = self.bot.get_channel(guild_data["logs_channel_id"])

        if logs_channel == None:
            return

        embed = discord.Embed(
            title="Channel Deleted",
            description=f"Deleted channel {channel.name}",
            colour=discord.Colour.red(),
        )

        embed.set_author(name=channel.guild.name, icon_url=channel.guild.icon)

        await logs_channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(logging(bot))
