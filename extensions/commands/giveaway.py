import datetime
from typing import Optional

import random
import discord
from discord import app_commands
from discord.ext import commands

from utils import DataManager, Paginator


class giveaway_modal(discord.ui.Modal, title="Create a Giveaway"):
    def __init__(self, bot) -> None:
        super().__init__()
        self.bot = bot

    def time_to_minutes(self, time: str) -> None:
        no_numbers = "".join([i for i in time if not i.isdigit()]).strip()
        no_characters = "".join([i for i in time if not i.isalpha()])

        if no_numbers.lower().startswith("s"):
            return int(no_characters) / 60
        elif no_numbers.lower().startswith("m"):
            return int(no_characters)
        elif no_numbers.lower().startswith("h"):
            return int(no_characters) * 60
        elif no_numbers.lower().startswith("d"):
            return int(no_characters) * 1440
        return None

    def winners_to_int(self, winners: str) -> None:
        no_characters = "".join([i for i in winners if not i.isalpha()])
        return int(no_characters)

    duration = discord.ui.TextInput(
        label="Duration",
        style=discord.TextStyle.short,
        placeholder="Ex: 10 minutes",
        max_length=30,
    )

    winneramount = discord.ui.TextInput(
        label="Number of winners",
        style=discord.TextStyle.short,
        default="1",
        max_length=3,
    )

    prize = discord.ui.TextInput(
        label="Prize", style=discord.TextStyle.short, max_length=100
    )

    description = discord.ui.TextInput(
        label="Description",
        style=discord.TextStyle.long,
        max_length=1000,
        required=False,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        time = self.time_to_minutes(self.duration.value)
        winners = self.winners_to_int(self.winneramount.value)

        if winners is not None:
            if time is not None:
                end_date = discord.utils.utcnow() + datetime.timedelta(minutes=time)
                await interaction.response.send_message(
                    f"Giveaway created!", ephemeral=True
                )

                message = await interaction.channel.send(
                    embed=discord.Embed(
                        title=f"{self.prize.value}",
                        description=(
                            f"{self.description.value}\n\n"
                            if self.description.value is not None
                            else ""
                        )
                        + f"Ends: {discord.utils.format_dt(end_date, style='R')} ({discord.utils.format_dt(end_date, style='F')})\n"
                        f"Hosted by: {interaction.user.mention}\n"
                        f"Entries: **0**\n"
                        f"Winners: **{winners}**",
                    ),
                    view=giveaway_views(self.bot),
                )

                await DataManager.register_giveaway(
                    message.id,
                    interaction.guild.id,
                    interaction.channel.id,
                    time,
                    winners,
                    self.prize.value,
                    self.description.value,
                    interaction.user.id,
                )

            else:
                await interaction.response.send_message(
                    f"Invalid time!", ephemeral=True
                )
        else:
            await interaction.response.send_message(
                f"Invalid winner amount!", ephemeral=True
            )

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        await interaction.response.send_message(
            f"Invalid time or winner amount!", ephemeral=True
        )


class giveaway_leave_view(discord.ui.View):
    def __init__(self, giveaway_id, bot):
        super().__init__(timeout=None)
        self.giveaway_id = giveaway_id
        self.bot = bot

    @discord.ui.button(label="Leave Giveaway", style=discord.ButtonStyle.red)
    async def leave_giveaway(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        giveaway_data = await DataManager.get_giveaway_data(self.giveaway_id)
        if interaction.user.id in giveaway_data["participants"]:
            giveaway_data["participants"].remove(interaction.user.id)
            await DataManager.edit_giveaway_data(
                self.giveaway_id, "participants", giveaway_data["participants"]
            )
            await interaction.response.edit_message(
                content="You have successfully left the giveaway!", view=None
            )

            self.bot.dispatch("giveaway_leave", self.giveaway_id, interaction.guild.id)
        else:
            await interaction.response.edit_message(
                content="You have already left the giveaway!", view=None
            )


class giveaway_views(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        style=discord.ButtonStyle.green,
        custom_id="persistent_view:giveaway",
        emoji="🎉",
    )
    async def join_giveaway(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        giveaway_data = await DataManager.get_giveaway_data(interaction.message.id)
        if (
            giveaway_data["participants"] is None
            or interaction.user.id not in giveaway_data["participants"]
        ):
            giveaway_data["participants"].append(interaction.user.id)
            await DataManager.edit_giveaway_data(
                interaction.message.id, "participants", giveaway_data["participants"]
            )
            await interaction.response.send_message(
                content="Successfully entered the giveaway!", ephemeral=True
            )

            self.bot.dispatch(
                "giveaway_join",
                interaction.message.id,
                interaction.guild.id,
            )
        elif interaction.user.id in giveaway_data["participants"]:
            return await interaction.response.send_message(
                content="You have already entered this giveaway!",
                ephemeral=True,
                view=giveaway_leave_view(interaction.message.id, self.bot),
            )

    @discord.ui.button(
        style=discord.ButtonStyle.gray,
        custom_id="persistent_view:giveaway_entrants",
        emoji="👥",
    )
    async def view_entrants(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        giveaway_data = await DataManager.get_giveaway_data(interaction.message.id)
        if giveaway_data:
            if len(giveaway_data["participants"]) > 0:
                embeds = []
                page_participants = []
                for i, participant in enumerate(giveaway_data["participants"], start=1):
                    page_participants.append(f"{i}. <@{participant}>")
                    if i % 10 == 0 or i == len(giveaway_data["participants"]):
                        current_page = (i - 1) // 10 + 1
                        total_pages = (len(giveaway_data["participants"])) // 10 + 1
                        embed = discord.Embed(
                            title=f"Giveaway Participants (Page {current_page}/{total_pages})",
                            description="\n".join(page_participants),
                            colour=discord.Colour.blurple(),
                        )
                        embeds.append(embed)
                        page_participants = []
                if embeds:
                    await Paginator.Simple(ephemeral=True).paginate(interaction, embeds)
            else:
                await interaction.response.send_message(
                    content="No entrants yet!", ephemeral=True
                )
        else:
            await interaction.response.send_message(
                content="Giveaway not found!", ephemeral=True
            )


class giveaway(commands.GroupCog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="create", description="Create a giveaway")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild.id))
    async def giveaway_create(
        self,
        interaction: discord.Interaction,
    ) -> None:
        await interaction.response.send_modal(giveaway_modal(self.bot))

    @app_commands.command(name="end", description="End a giveaway by the ID")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild.id))
    @app_commands.describe(giveaway_id="The ID of the giveaway you want to end")
    async def giveaway_end(
        self, interaction: discord.Interaction, giveaway_id: str
    ) -> None:
        if giveaway_id.isnumeric():
            if await DataManager.get_giveaway_data(int(giveaway_id)):
                giveaway_data = await DataManager.get_giveaway_data(int(giveaway_id))
                if giveaway_data["ended"]:
                    return await interaction.response.send_message(
                        f"Giveaway already ended!", ephemeral=True
                    )
                await DataManager.edit_giveaway_data(int(giveaway_id), "ended", True)
                await DataManager.edit_giveaway_data(
                    int(giveaway_id),
                    "end_date",
                    discord.utils.utcnow().isoformat(),
                )
                self.bot.dispatch(
                    "manual_giveaway_end", int(giveaway_id), interaction.guild.id
                )
                await interaction.response.send_message(
                    f"Giveaway ended!", ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"Giveaway not found!", ephemeral=True
                )
        else:
            await interaction.response.send_message(
                f"Invalid giveaway ID!", ephemeral=True
            )

    @app_commands.command(name="reroll", description="Reroll a giveaway")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild.id))
    @app_commands.describe(
        giveaway_id="The ID of the giveaway/giveaway winner you want to reroll"
    )
    async def giveaway_reroll(
        self,
        interaction: discord.Interaction,
        giveaway_id: str,
        user: Optional[discord.User],
    ) -> None:
        if giveaway_id.isnumeric():
            if await DataManager.get_giveaway_data(int(giveaway_id)):
                giveaway_data = await DataManager.get_giveaway_data(int(giveaway_id))
                if giveaway_data["ended"]:
                    if user is None:
                        if len(giveaway_data["winners"]) > 0:
                            await DataManager.draw_giveaway_winners(int(giveaway_id))
                            await interaction.response.send_message(
                                f"Giveaway rerolled!", ephemeral=True
                            )
                            self.bot.dispatch(
                                "manual_giveaway_reroll", int(giveaway_id)
                            )
                        else:
                            await interaction.response.send_message(
                                f"No winners to reroll!", ephemeral=True
                            )
                    else:
                        if user.id in giveaway_data["winners"]:
                            giveaway_data["winners"].remove(user.id)
                            participants = list(giveaway_data["participants"])
                            new_winner = random.choice(participants)
                            giveaway_data["winners"].append(new_winner)
                            await DataManager.edit_giveaway_data(
                                giveaway_id, "winners", giveaway_data["winners"]
                            )

                            await interaction.response.send_message(
                                f"Giveaway winner rerolled!", ephemeral=True
                            )
                            self.bot.dispatch(
                                "manual_giveaway_winner_reroll",
                                int(giveaway_id),
                                new_winner,
                            )
                        else:
                            await interaction.response.send_message(
                                f"User is not a winner!", ephemeral=True
                            )
                else:
                    await interaction.response.send_message(
                        f"Giveaway is still active!", ephemeral=True
                    )
            else:
                await interaction.response.send_message(
                    f"Giveaway not found!", ephemeral=True
                )
        else:
            await interaction.response.send_message(
                f"Invalid giveaway ID!", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(giveaway(bot))
