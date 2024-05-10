import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random
import time
import json
from utils import DataManager, cooldown_check


async def find_user_level(user_id: int):
    user_data = await DataManager.get_user_data(user_id)
    if user_data["mining_xp"] == None:
        return 0
    levels = DataManager.get("levels", "levels")
    for level in levels:
        required_xp = levels[level]["requiredXP"]
        if user_data["mining_xp"] < required_xp:
            return int(level) - 1
        elif user_data["mining_xp"] == required_xp:
            return int(level)
    return 50


class mining_buttons(discord.ui.View):
    def __init__(self, bot, mine: str):
        super().__init__(timeout=60)

        self.bot = bot
        self.response: discord.Message = None
        self.mine_name = mine
        self.mine = DataManager.get("mines", mine)
        self.max_ores: dict = {}
        self.ore_positions: dict = {}
        self.ores = DataManager.get("ores", "ores")
        self.mined_ores = 0
        self.mined_items = {}
        self.gained_xp = 0
        self.button_clicked = False
        self.closed = False

        random.seed(time.time())

        positions = list(range(1, 26))
        random.shuffle(positions)

        ores = []
        for ore in self.mine["resources"]:
            min_ore = int(self.mine["resources"][ore]["min"])
            max_ore = int(self.mine["resources"][ore]["max"])
            ore_count = random.randint(min_ore, max_ore)
            ores.extend([ore] * ore_count)
        random.shuffle(ores)

        for position, ore in zip(positions, ores):
            self.max_ores[ore] = ore_count
            self.ore_positions[position] = ore

        for i in range(1, 26):
            row = (i - 1) // 5
            button = discord.ui.Button(
                style=discord.ButtonStyle.gray, label="⠀", row=row
            )
            button.callback = self.create_callback(i)
            self.add_item(button)

    def get_random_ore_pos(self):
        unmined_ore_positions = [
            pos for pos in self.ore_positions if not self.children[pos - 1].disabled
        ]
        if unmined_ore_positions:
            return random.choice(unmined_ore_positions)

    def create_callback(self, i):
        async def callback(interaction: discord.Interaction):
            await interaction.response.defer()
            button = self.children[i - 1]
            button.disabled = True

            if not self.closed:
                if i not in self.ore_positions:
                    if random.randint(0, 100) > 95:
                        random_position = self.get_random_ore_pos()
                        if random_position is not None:
                            random_button = self.children[random_position - 1]
                            random_button.disabled = True
                            self.mined_ores += 1
                            random_button.label = None
                            random_button.emoji = self.ores[
                                self.ore_positions[random_position]
                            ]["emoji"]

                            xp = self.ores[self.ore_positions[random_position]]["xp"]
                            self.gained_xp += xp

                            ore = self.ore_positions[random_position]
                            if ore in self.mined_items:
                                self.mined_items[ore] += 1
                            else:
                                self.mined_items[ore] = 1
                            await interaction.edit_original_response(view=self)
                        else:
                            await interaction.edit_original_response(view=self)

                if i in self.ore_positions:
                    self.mined_ores += 1
                    button.label = None
                    button.emoji = self.ores[self.ore_positions[i]]["emoji"]

                    xp = self.ores[self.ore_positions[i]]["xp"]
                    self.gained_xp += xp

                    ore = self.ore_positions[i]
                    if ore in self.mined_items:
                        self.mined_items[ore] += 1
                    else:
                        self.mined_items[ore] = 1

                await interaction.edit_original_response(view=self)

                if not self.button_clicked:
                    self.button_clicked = True

                    await asyncio.sleep(17)
                    self.closed = True

                    if self.mined_ores == len(self.ore_positions):
                        pass
                    else:
                        user_data = await DataManager.get_user_data(interaction.user.id)
                        mining_xp = user_data["mining_xp"]
                        if mining_xp == None:
                            mining_xp = 0

                        await DataManager.edit_user_data(
                            interaction.user.id, "mining_xp", mining_xp + self.gained_xp
                        )

                        for ore, quantity in self.mined_items.items():
                            await DataManager.edit_user_inventory(
                                interaction.user.id, ore, quantity
                            )

                        return await interaction.edit_original_response(
                            embed=discord.Embed(
                                title="The mine crumbles down!",
                                description=f"As the {self.mine_name} crumbles down, you are forced to leave.",
                                colour=discord.Colour.from_rgb(139, 69, 19),
                            ),
                            view=None,
                        )

                if self.mined_ores == len(self.ore_positions):
                    await interaction.edit_original_response(
                        embed=discord.Embed(
                            title="You have mined all the ores!",
                            description="You have mined all the ores in the mine, you are forced to leave.",
                            colour=discord.Colour.from_rgb(139, 69, 19),
                        ),
                        view=None,
                    )

                    user_data = await DataManager.get_user_data(interaction.user.id)
                    mining_xp = user_data["mining_xp"]
                    if mining_xp == None:
                        mining_xp = 0

                    await DataManager.edit_user_data(
                        interaction.user.id, "mining_xp", mining_xp + self.gained_xp
                    )

                    for ore, quantity in self.mined_items.items():
                        await DataManager.edit_user_inventory(
                            interaction.user.id, ore, quantity
                        )

        return callback


class choose_mine(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=60)
        self.bot = bot
        self.response: discord.Message = None

        with open("data/mine/mines.json", "r") as f:
            self.mines = json.load(f)

        for mine in self.mines:
            button = discord.ui.Button(
                style=discord.ButtonStyle.green,
                label=mine,
                emoji=self.mines[mine]["emoji"],
            )
            button.callback = self.create_callback(mine)
            self.add_item(button)

    async def on_timeout(self) -> None:
        return await self.response.delete()

    def create_callback(self, mine):
        async def callback(interaction: discord.Interaction):
            user_level = await find_user_level(interaction.user.id)
            if user_level < self.mines[mine]["requiredLevel"]:
                await interaction.response.send_message(
                    f"You need to be level {self.mines[mine]['requiredLevel']} to enter the {mine} mine! Your current level is {user_level}",
                    ephemeral=True,
                )
                return

            view = mining_buttons(self.bot, mine)
            await interaction.response.edit_message(
                embed=discord.Embed(
                    description=f"You have entered the {mine}, here you can find mostly {self.mines[mine]["mainOre"]}, but maybe some {self.mines[mine]['secondaryOre']} as well.",
                    colour=discord.Colour.from_rgb(139, 69, 19),
                ),
                attachments=[],
                view=view,
            )
            view.response = await interaction.original_response()

        return callback


class mine(commands.GroupCog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    @app_commands.command(name="start", description="Mine for resources")
    async def mine_start(self, interaction: discord.Interaction):
        if await cooldown_check(
            interaction.user.id,
            "<:white_cross:1096791282023669860> You already went mining",
            "mine",
            1800,
        ):
            f = discord.File(
                "data/mine/mining_assets/mine_background.jpg", filename="mining.jpg"
            )
            view = choose_mine(self.bot)
            await interaction.response.send_message(
                file=f,
                embed=discord.Embed(
                    description="Welcome to the mines, here you are able to mine for various resources, and later smelt them down to craft various items with them.",
                    colour=discord.Colour.from_rgb(139, 69, 19),
                ).set_image(url="attachment://mining.jpg"),
                view=view,
            )
            view.response = await interaction.original_response()


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(mine(bot))
