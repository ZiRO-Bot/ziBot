import asyncio
import discord
import json
import logging
import sqlite3

from bot import ziBot, get_prefix, shard, shard_count, token


def setup_logging():
    FORMAT = "%(asctime)s - [%(levelname)s]: %(message)s"
    DATE_FORMAT = "%d/%m/%Y (%H:%M:%S)"

    logger = logging.getLogger("discord")
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(
        filename="discord.log", mode="a", encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(fmt=FORMAT, datefmt=DATE_FORMAT))
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(fmt=FORMAT, datefmt=DATE_FORMAT))
    console_handler.setLevel(logging.WARNING)
    logger.addHandler(console_handler)


def check_json():
    try:
        f = open("config.json", "r")
    except FileNotFoundError:
        token = input("[Bot Setup] Enter your bot token: ")
        with open("config.json", "w+") as f:
            json.dump({"token": token}, f, indent=4)

def init_bot():

    logger = logging.getLogger("discord")
    
    check_json()

    if token is None:
        logger.error('No token found, please add environment variable "TOKEN"!')
        return

    bot = ziBot(
        command_prefix=get_prefix,
        case_insensitive=True,
        allowed_mentions=discord.AllowedMentions(
            users=True, roles=False
        ),
        intents=discord.Intents.all(),
        shard_id=int(shard),
        shard_count=int(shard_count),
    )
    bot.run()


if __name__ == "__main__":
    setup_logging()
    init_bot()
