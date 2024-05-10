import asyncio
import datetime
import json
import os
import random
import uuid
from typing import Any

import asyncpg
import discord


class DataManager:
    __data: dict[str, str] = {}
    initialised = False

    @classmethod
    def setup(cls, paths: list[tuple[str, str, str]]) -> None:
        for path in paths:
            path, default = path

            if not os.path.exists(path):
                if not os.path.exists(os.path.dirname(path)):
                    os.makedirs(os.path.dirname(path))

                with open(path, "w") as file:
                    file.write(json.dumps(default, indent=4))

    @classmethod
    async def initialise(cls) -> None:
        for root, _, files in os.walk(os.curdir):
            for file in files:
                if not file.endswith(".json"):
                    continue

                with open(os.path.join(root, file), "r") as f:
                    try:
                        cls.__data[file[:-5]] = json.load(f)
                    except json.JSONDecodeError:
                        print(f"Failed to load {file}")
                        print(f"File content: {f.read()}")

        DataManager.initialised = True

        cls.db_connection = await asyncpg.create_pool(
            user=DataManager.get("config", "postgres_user"),
            host="127.0.0.1",
            password=DataManager.get("config", "postgres_password"),
            database=DataManager.get("config", "postgres_database"),
        )

        await cls.db_connection.execute(
            """CREATE TABLE IF NOT EXISTS users (
                id bigint PRIMARY KEY,
                inventory JSONB,
                cooldowns JSONB,
                balance bigint DEFAULT 0,
                bank bigint DEFAULT 0,
                mining_xp bigint DEFAULT 0
            );"""
        )

        await cls.db_connection.execute(
            """CREATE TABLE IF NOT EXISTS guilds (
                id bigint PRIMARY KEY,
                unverified_role_id bigint,
                verification_channel_id bigint,
                verification_logs_channel_id bigint,
                logs_channel_id bigint,
                appeal_link TEXT,
                welcome_message TEXT,
                warned_users JSONB
            );"""
        )

        await cls.db_connection.execute(
            """CREATE TABLE IF NOT EXISTS filtered_words (
                guild_id bigint PRIMARY KEY,
                channel_id bigint,
                blacklisted_words TEXT ARRAY DEFAULT '{}'::text[],
                whitelist bigint ARRAY DEFAULT '{}'::bigint[]
            );"""
        )

        await cls.db_connection.execute(
            """CREATE TABLE IF NOT EXISTS giveaways (
                id bigint PRIMARY KEY,
                guild_id bigint,
                channel_id bigint,
                end_date TEXT,
                winner_amount bigint,
                prize TEXT,
                extra_notes TEXT,
                host_id bigint,
                participants bigint ARRAY DEFAULT '{}'::bigint[],
                winners bigint ARRAY DEFAULT '{}'::bigint[],
                ended BOOLEAN DEFAULT FALSE
            );"""
        )

        await cls.db_connection.execute(
            """CREATE TABLE IF NOT EXISTS panels (
                id bigint PRIMARY KEY,
                channel_id bigint,
                guild_id bigint,
                limit_per_user bigint,
                panel_title TEXT,
                panel_description TEXT,
                panel_moderators bigint ARRAY DEFAULT '{}'::bigint[]
            );"""
        )

        await cls.db_connection.execute(
            """CREATE TABLE IF NOT EXISTS tickets (
                panel_id bigint PRIMARY KEY,
                tickets JSONB
            );"""
        )

    @classmethod
    def get(cls, path: str, key: str) -> Any:
        return cls.__data.get(path, {}).get(key, None)

    @classmethod
    async def add_column(cls, table: str, column_name: str, column_type: Any) -> None:
        async with cls.db_connection.acquire():
            columnexists = await cls.db_connection.fetchval(
                f"SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = '{table}' AND column_name = '{column_name}')"
            )

            if not columnexists:
                await cls.db_connection.execute(
                    f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column_name} {column_type}"
                )

            elif columnexists:
                await cls.db_connection.execute(
                    f"ALTER TABLE {table} ALTER COLUMN {column_name} TYPE {column_type} USING {column_name}::{column_type}"
                )

    @classmethod
    async def remove_column(cls, table: str, column_name: str) -> None:
        async with cls.db_connection.acquire():
            columnexists = await cls.db_connection.fetchval(
                f"SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = '{table}' AND column_name = '{column_name}')"
            )

            if columnexists:
                await cls.db_connection.execute(
                    f"ALTER TABLE {table} DROP COLUMN IF EXISTS {column_name}"
                )

            elif not columnexists:
                return

    @classmethod
    async def user_check(cls, user_id: int) -> None:
        async with cls.db_connection.acquire():
            userexists = await cls.db_connection.fetchval(
                "SELECT EXISTS (SELECT 1 FROM users WHERE id = $1)", user_id
            )

            if not userexists:
                await cls.add_user_data(user_id)

    @classmethod
    async def add_user_data(cls, user_id: int) -> None:
        async with cls.db_connection.acquire():
            await cls.db_connection.execute(
                "INSERT INTO users (id) VALUES ($1)", user_id
            )

    @classmethod
    async def get_all_users(cls) -> None:
        async with cls.db_connection.acquire():
            rows = await cls.db_connection.fetch("SELECT id FROM users")
            return [row["id"] for row in rows]

    @classmethod
    async def get_user_data(cls, user_id: int) -> None:
        await cls.user_check(user_id)
        async with cls.db_connection.acquire():
            return await cls.db_connection.fetchrow(
                "SELECT * FROM users WHERE id = $1", user_id
            )

    @classmethod
    async def edit_user_data(cls, user_id: int, column: str, value: Any) -> None:
        await cls.user_check(user_id)
        async with cls.db_connection.acquire():
            return await cls.db_connection.execute(
                f"UPDATE users SET {column} = $1 WHERE id = $2", value, user_id
            )

    @classmethod
    async def edit_user_inventory(cls, user_id: int, item: str, amount: int) -> None:
        await cls.user_check(user_id)
        async with cls.db_connection.acquire():
            user_data = await cls.get_user_data(user_id)
            if user_data["inventory"] is None:
                return await cls.edit_user_data(
                    user_id, "inventory", json.dumps({item: amount})
                )

            elif user_data["inventory"] is not None:
                if item not in user_data["inventory"]:
                    user_inventory = json.loads(user_data["inventory"])
                    user_inventory[item] = amount
                    return await cls.edit_user_data(
                        user_id, "inventory", json.dumps(user_inventory)
                    )

                elif item in user_data["inventory"]:
                    user_inventory = json.loads(user_data["inventory"])
                    user_inventory[item] += amount
                    return await cls.edit_user_data(
                        user_id, "inventory", json.dumps(user_inventory)
                    )

    @classmethod
    async def add_cooldown(cls, user_id: int, command_name: str, seconds: int) -> None:
        await cls.user_check(user_id)
        async with cls.db_connection.acquire():
            user_data = await cls.get_user_data(user_id)
            end_time = discord.utils.utcnow() + datetime.timedelta(seconds=seconds)
            if user_data["cooldowns"] is None:
                return await cls.edit_user_data(
                    user_id,
                    "cooldowns",
                    json.dumps({command_name: end_time.isoformat()}),
                )

            elif user_data["cooldowns"] is not None:
                if command_name not in user_data["cooldowns"]:
                    user_cooldowns = json.loads(user_data["cooldowns"])
                    user_cooldowns[command_name] = end_time.isoformat()
                    return await cls.edit_user_data(
                        user_id, "cooldowns", json.dumps(user_cooldowns)
                    )

                elif command_name in user_data["cooldowns"]:
                    user_cooldowns = json.loads(user_data["cooldowns"])
                    user_cooldowns[command_name] = end_time.isoformat()
                    return await cls.edit_user_data(
                        user_id, "cooldowns", json.dumps(user_cooldowns)
                    )

    @classmethod
    async def remove_cooldown(cls, user_id: int, command_name: str) -> bool:
        await cls.user_check(user_id)
        async with cls.db_connection.acquire():
            user_data = await cls.get_user_data(user_id)
            if command_name == "all":
                return await cls.edit_user_data(user_id, "cooldowns", None)
            elif user_data["cooldowns"] is not None:
                user_cooldowns = json.loads(user_data["cooldowns"])
                if command_name in user_cooldowns:
                    del user_cooldowns[command_name]
                    await cls.edit_user_data(
                        user_id, "cooldowns", json.dumps(user_cooldowns)
                    )
                    return True
                elif command_name not in user_cooldowns:
                    return False

    @classmethod
    async def guild_check(cls, guild_id: int) -> None:
        async with cls.db_connection.acquire():
            guildexists = await cls.db_connection.fetchval(
                "SELECT EXISTS (SELECT 1 FROM guilds WHERE id = $1)", guild_id
            )

            if not guildexists:
                await cls.add_guild_data(cls, guild_id)

    classmethod

    async def add_guild_data(cls, guild_id: int) -> None:
        async with cls.db_connection.acquire():
            await cls.db_connection.execute(
                "INSERT INTO guilds (id) VALUES ($1)", guild_id
            )

    @classmethod
    async def get_guild_data(cls, guild_id: int) -> None:
        await cls.guild_check(guild_id)
        async with cls.db_connection.acquire():
            return await cls.db_connection.fetchrow(
                "SELECT * FROM guilds WHERE id = $1", guild_id
            )

    @classmethod
    async def edit_guild_data(cls, guild_id: int, column: str, value: Any) -> None:
        await cls.guild_check(guild_id)
        async with cls.db_connection.acquire():
            return await cls.db_connection.execute(
                f"UPDATE guilds SET {column} = $1 WHERE id = $2", value, guild_id
            )

    @classmethod
    async def register_warning(cls, guild_id: int, user_id: int, reason: str) -> None:
        await cls.guild_check(guild_id)
        async with cls.db_connection.acquire():
            warning = {str(uuid.uuid4()): reason}
            guild_data = await cls.get_guild_data(guild_id)
            warned_users = guild_data["warned_users"]
            if warned_users is None:
                warned_users = {}
            elif warned_users is not None:
                warned_users = json.loads(warned_users)
            if str(user_id) not in warned_users:
                warned_users[str(user_id)] = [warning]
            else:
                warned_users[str(user_id)].append(warning)
            return await cls.edit_guild_data(
                guild_id, "warned_users", json.dumps(warned_users)
            )

    @classmethod
    async def delete_warning(cls, guild_id: int, warning_uuid: uuid.uuid4) -> bool:
        await cls.guild_check(guild_id)
        async with cls.db_connection.acquire():
            guild_data = await cls.get_guild_data(guild_id)
            warned_users = json.loads(guild_data["warned_users"])
            for user_id in warned_users:
                for warning in warned_users[user_id]:
                    if warning_uuid in warning:
                        warned_users[user_id].remove(warning)
                        await cls.edit_guild_data(
                            guild_id, "warned_users", json.dumps(warned_users)
                        )
                        return True
                    elif warning_uuid not in warning:
                        return False

    @classmethod
    async def get_user_warnings(cls, guild_id: int, user_id: int) -> None:
        await cls.guild_check(guild_id)
        async with cls.db_connection.acquire():
            guild_data = await cls.get_guild_data(guild_id)
            if guild_data["warned_users"] is None:
                return []
            elif guild_data["warned_users"] is not None:
                warned_users = json.loads(guild_data["warned_users"])
                return warned_users.get(str(user_id), [])

    @classmethod
    async def filter_check(cls, guild_id: int) -> None:
        await cls.guild_check(guild_id)
        async with cls.db_connection.acquire():
            filterexists = await cls.db_connection.fetchrow(
                "SELECT * FROM filtered_words WHERE guild_id = $1", guild_id
            )

            if not filterexists:
                await cls.add_filter_data(guild_id)

    @classmethod
    async def get_filter_data(cls, guild_id: int) -> None:
        await cls.filter_check(guild_id)
        async with cls.db_connection.acquire():
            return await cls.db_connection.fetchrow(
                "SELECT * FROM filtered_words WHERE guild_id = $1", guild_id
            )

    @classmethod
    async def add_filter_data(cls, guild_id: int) -> None:
        async with cls.db_connection.acquire():
            await cls.db_connection.execute(
                "INSERT INTO filtered_words (guild_id) VALUES ($1)", guild_id
            )

    @classmethod
    async def edit_filter_data(cls, guild_id: int, column: str, value: Any) -> None:
        await cls.filter_check(guild_id)
        async with cls.db_connection.acquire():
            return await cls.db_connection.execute(
                f"UPDATE filtered_words SET {column} = $1 WHERE guild_id = $2",
                value,
                guild_id,
            )

    @classmethod
    async def register_giveaway(
        cls,
        giveaway_id: int,
        guild_id: int,
        channel_id: int,
        minutes: int,
        winners: int,
        prize: str,
        extra_notes: str,
        host_id: int,
    ) -> None:
        await cls.guild_check(guild_id)
        async with cls.db_connection.acquire():
            end_date = discord.utils.utcnow() + datetime.timedelta(minutes=minutes)
            await cls.db_connection.execute(
                "INSERT INTO giveaways (id, guild_id, channel_id, end_date, winner_amount, prize, extra_notes, host_id) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",
                giveaway_id,
                guild_id,
                channel_id,
                end_date.isoformat(),
                winners,
                prize,
                extra_notes,
                host_id,
            )

    @classmethod
    async def get_giveaway_data(cls, giveaway_id: int) -> None:
        async with cls.db_connection.acquire():
            return await cls.db_connection.fetchrow(
                "SELECT * FROM giveaways WHERE id = $1", giveaway_id
            )

    @classmethod
    async def edit_giveaway_data(
        cls, giveaway_id: int, column: str, value: Any
    ) -> None:
        async with cls.db_connection.acquire():
            return await cls.db_connection.execute(
                f"UPDATE giveaways SET {column} = $1 WHERE id = $2",
                value,
                int(giveaway_id),
            )

    @classmethod
    async def draw_giveaway_winners(cls, giveaway_id: int) -> list[int]:
        async with cls.db_connection.acquire():
            giveaway_data = await cls.get_giveaway_data(giveaway_id)
            winners = random.sample(
                giveaway_data["participants"], giveaway_data["winner_amount"]
            )
            for winner in winners:
                giveaway_data["participants"].remove(winner)
            await cls.edit_giveaway_data(
                giveaway_id,
                "participants",
                giveaway_data["participants"],
            )
            await cls.edit_giveaway_data(giveaway_id, "winners", winners)
            await cls.edit_giveaway_data(giveaway_id, "ended", True)
            return winners

    @classmethod
    async def get_all_panels(cls) -> None:
        async with cls.db_connection.acquire():
            rows = await cls.db_connection.fetch("SELECT * FROM panels")
            return [dict(row) for row in rows]

    @classmethod
    async def create_panel(
        cls,
        panel_id: int,
        channel_id: int,
        guild_id: int,
        limit_per_user: int,
        panel_title: str,
        panel_description: str,
        panel_moderators: list[int],
    ) -> None:
        await cls.guild_check(guild_id)
        async with cls.db_connection.acquire():
            await cls.db_connection.execute(
                "INSERT INTO panels (id, channel_id, guild_id, limit_per_user, panel_title, panel_description, panel_moderators) VALUES ($1, $2, $3, $4, $5, $6, $7)",
                panel_id,
                channel_id,
                guild_id,
                limit_per_user,
                panel_title,
                panel_description,
                panel_moderators,
            )

    @classmethod
    async def get_panel_data(cls, panel_id: int) -> None:
        async with cls.db_connection.acquire():
            return await cls.db_connection.fetchrow(
                "SELECT * FROM panels WHERE id = $1", panel_id
            )

    @classmethod
    async def edit_panel_data(cls, panel_id: int, column: str, value: Any) -> None:
        async with cls.db_connection.acquire():
            if column == "delete" and value == True:
                return await cls.db_connection.execute(
                    "DELETE FROM panels WHERE id = $1", panel_id
                )
            else:
                return await cls.db_connection.execute(
                    f"UPDATE panels SET {column} = $1 WHERE id = $2", value, panel_id
                )

    @classmethod
    async def get_all_tickets(cls):
        async with cls.db_connection.acquire():
            rows = await cls.db_connection.fetch("SELECT * FROM tickets")
            all_tickets = []
            for row in rows:
                if dict(row)["tickets"] is not None:
                    tickets = json.loads(dict(row)["tickets"])
                    for ticket_id, ticket_data in tickets.items():
                        ticket_data["ticket_id"] = ticket_id
                        all_tickets.append(ticket_data)
            return all_tickets

    @classmethod
    async def get_panel_tickets(cls, panel_id: int) -> None:
        async with cls.db_connection.acquire():
            return await cls.db_connection.fetchrow(
                "SELECT tickets FROM tickets WHERE panel_id = $1", panel_id
            )

    @classmethod
    async def create_ticket(
        cls, panel_id: int, ticket_id: int, ticket_creator: int
    ) -> None:
        async with cls.db_connection.acquire():
            tickets = await cls.get_panel_tickets(panel_id)
            if tickets is None:
                tickets = {}
            elif tickets["tickets"] is None:
                tickets = {}
            else:
                tickets = json.loads(tickets["tickets"])

            tickets[ticket_id] = {"ticket_creator": ticket_creator, "closed": False}

            existing_panel = await cls.db_connection.fetchval(
                "SELECT panel_id FROM tickets WHERE panel_id = $1", panel_id
            )
            if existing_panel is None:
                await cls.db_connection.execute(
                    "INSERT INTO tickets (panel_id, tickets) VALUES ($1, $2)",
                    panel_id,
                    json.dumps(tickets),
                )
            else:
                await cls.db_connection.execute(
                    "UPDATE tickets SET tickets = $1 WHERE panel_id = $2",
                    json.dumps(tickets),
                    panel_id,
                )

    @classmethod
    async def get_panel_id_by_ticket_id(cls, ticket_id: int):
        async with cls.db_connection.acquire():
            rows = await cls.db_connection.fetch("SELECT * FROM tickets")
            for row in rows:
                if dict(row)["tickets"] is not None:
                    tickets = json.loads(dict(row)["tickets"])
                    if str(ticket_id) in tickets:
                        return dict(row)["panel_id"]
            return None

    @classmethod
    async def get_ticket_data(cls, panel_id: int, ticket_id: int):
        async with cls.db_connection.acquire():
            tickets = await cls.db_connection.fetchval(
                "SELECT tickets FROM tickets WHERE panel_id = $1", panel_id
            )
            if tickets is not None:
                tickets = json.loads(tickets)
                if str(ticket_id) in tickets:
                    ticket_data = tickets[str(ticket_id)]
                else:
                    ticket_data = {}
            else:
                ticket_data = {}
            return ticket_data

    @classmethod
    async def close_ticket(cls, panel_id: int, ticket_id: int) -> None:
        async with cls.db_connection.acquire():
            tickets = await cls.db_connection.fetchval(
                "SELECT tickets FROM tickets WHERE panel_id = $1", panel_id
            )
            if tickets is not None:
                tickets = json.loads(tickets)
                if str(ticket_id) in tickets:
                    tickets[str(ticket_id)]["closed"] = True
                    await cls.db_connection.execute(
                        "UPDATE tickets SET tickets = $1 WHERE panel_id = $2",
                        json.dumps(tickets),
                        panel_id,
                    )

    @classmethod
    async def open_ticket(cls, panel_id: int, ticket_id: int) -> None:
        async with cls.db_connection.acquire():
            tickets = await cls.db_connection.fetchval(
                "SELECT tickets FROM tickets WHERE panel_id = $1", panel_id
            )
            if tickets is not None:
                tickets = json.loads(tickets)
                if str(ticket_id) in tickets:
                    tickets[str(ticket_id)]["closed"] = False
                    await cls.db_connection.execute(
                        "UPDATE tickets SET tickets = $1 WHERE panel_id = $2",
                        json.dumps(tickets),
                        panel_id,
                    )


async def main():
    await DataManager.initialise()


if __name__ == "__main__":
    asyncio.run(main())
