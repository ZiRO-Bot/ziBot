import asyncio
import asyncpg
import click
import contextlib
import discord
import json
import logging
import sys

from bot import ziBot

import config


@contextlib.contextmanager
def setup_logging():
    try:
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

        yield
    finally:
        handlers = logger.handlers[:]
        for handler in handlers:
            handler.close()
            logger.removeHandler(handler)


def check_json():
    try:
        f = open("config.json", "r")
    except FileNotFoundError:
        with open("config.json", "w+") as f:
            json.dump(
                {
                    "bot_token": "",
                    "twitch": {"id": "", "secret": ""},
                    "reddit": {"id": "", "secret": "", "user_agent": ""},
                    "openweather_apikey": "",
                },
                f,
                indent=4,
            )


def init_bot():
    loop = asyncio.get_event_loop()
    logger = logging.getLogger()

    kwargs = {
        'command_timeout': 60,
        'max_size': 20,
        'min_size': 20,
    }
    try:
        pool = loop.run_until_complete(asyncpg.create_pool(config.postgresql, **kwargs))
    except Exception as e:
        click.echo('Could not set up PostgreSQL. Exiting.', file=sys.stderr)
        logger.exception('Could not set up PostgreSQL. Exiting.')
        return

    bot = ziBot()
    bot.run()


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """Launch the bot."""
    if ctx.invoked_subcommand is None:
        loop = asyncio.get_event_loop()
        with setup_logging():
            init_bot()


if __name__ == "__main__":
    main()
