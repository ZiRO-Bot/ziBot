# NO LONGER USED, checkout https://github.com/null2264/speedrunComBot instead

import aiohttp
import discord
import json
import re

from discord.ext import commands
from cogs.utilities.formatting import pformat, realtime, hformat
from speedrunpy import SpeedrunPy


class SRC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.API_URL = "https://www.speedrun.com/api/v1/"
        self.LOGO = "https://www.speedrun.com/images/1st.png"
        self.session = self.bot.session
        self.src = SpeedrunPy(session=self.session)

    async def generate_tinyUrl(self, long_url: str):
        async with self.session.get(
            "https://tinyurl.com/api-create.php?url=" + long_url
        ) as url:
            data = await url.text()
        return data

    async def get(self, _type, **kwargs):
        async with self.session.get(self.API_URL + _type, **kwargs) as url:
            data = json.loads(await url.text())
        return data

    async def get_user_id(self, username):
        data = await self.get(f"users/{username}")
        if "data" not in data:
            return None
        data = data["data"]
        return data["id"]

    async def get_username(self, user_id):
        data = await self.get(f"users/{user_id}")
        if "data" not in data:
            return None
        data = data["data"]
        return data["names"]["international"]

    async def get_cats(self, game_id):
        categories = {}
        data = await self.get(f"games/{game_id}/categories")
        data = data["data"]
        for category in data:
            if category["type"] == "per-game":
                categories[pformat(category["name"])] = {
                    "id": category["id"],
                    "name": category["name"],
                }
        return categories

    async def get_subcats(self, game_id, category):
        catdict = await self.get_cats(game_id)
        try:
            cat_id = catdict[pformat(category)]["id"]
        except KeyError:
            return
        data = await self.get(f"games/{game_id}/variables")
        data = data["data"]
        subcategory = {}
        for i in data:
            if (
                i["is-subcategory"]
                and i["scope"]["type"] == "full-game"
                and i["category"] == cat_id
            ):
                for e in i["values"]["values"]:
                    subcategory[pformat(i["values"]["values"][e]["label"])] = {
                        "name": i["values"]["values"][e]["label"],
                        "subcat_id": i["id"],
                        "id": e,
                    }
            if (
                i["is-subcategory"]
                and i["scope"]["type"] == "full-game"
                and not i["category"]
            ):
                for e in i["values"]["values"]:
                    subcategory[pformat(i["values"]["values"][e]["label"])] = {
                        "name": i["values"]["values"][e]["label"],
                        "subcat_id": i["id"],
                        "id": e,
                    }
        return {
            category: {
                "id": cat_id,
                "name": catdict[category]["name"],
                "sub_cats": subcategory,
            }
        }

    async def get_game(self, game):
        """Get game data without abbreviation."""
        regex = r".*:\/\/.*\.speedrun\..*\/([a-zA-Z0-9]*)(.*)"
        match = re.match(regex, game)
        if match and match[1]:
            game = match[1]
        data = await self.get(f"games/{game}")
        bulk = False
        try:
            data = data["data"]
        except:
            # If data is empty try getting it from name
            data = await self.get(f"games?name={game}")
            data = data["data"]
            bulk = True
        game_info = []

        if bulk:
            for i in data:
                game_info.append(
                    {
                        "id": i["id"],
                        "name": i["names"]["international"],
                    }
                )
        else:
            game_info.append(
                {
                    "id": data["id"],
                    "name": data["names"]["international"],
                }
            )
        return game_info

    @commands.group()
    async def mcbe(self, ctx):
        """Get mcbe run informations from speedrun.com."""
        pass

    @mcbe.command(
        name="wrs",
        usage="[category] [seed] [main/ext]",
        example='{prefix}mcbe wrs "Any% Glitchless" "Set Seed"',
    )
    async def mcbe_wrs(
        self,
        ctx,
        category: str = "any",
        seed: str = "set_seed",
        leaderboard: str = "main",
    ):
        """Get mcbe world records from speedrun.com"""

        if leaderboard == "main":
            leaderboard = "mcbe"
        elif leaderboard == "ext":
            leaderboard = "mcbece"
        else:
            await ctx.send(f"Usage: {ctx.prefix}mcbe wrs [category] [seed] [main/ext]")
            return

        # preparation
        game = await self.get_game(leaderboard)
        game = game[0]

        # fetch subcats
        category = pformat(category)
        subcats = await self.get_subcats(game["id"], category)

        # get category id and display_name also separate subcats
        cat_name = subcats[category]["name"]
        cat_id = subcats[category]["id"]
        subcats = subcats[category]["sub_cats"]

        # separate seeds and platforms
        seeds = {}
        platforms = {}
        for i in subcats:
            if "seed" in i.lower():
                seeds[pformat(i)] = subcats[i]
                # seeds.append({pformat(i): subcats[i]})
            else:
                platforms[pformat(i)] = subcats[i]
                # platforms.append({pformat(i): subcats[i]})

        # get the right seed type
        sel_seed = ""
        if seed in seeds:
            sel_seed = seed
        varlink = f"&var-{seeds[sel_seed]['subcat_id']}={seeds[sel_seed]['id']}"

        # init embed
        e = discord.Embed(title="World Records", colour=discord.Colour.gold())
        e.set_thumbnail(
            url="https://raw.githubusercontent.com/null2264/null2264/master/assets/mcbe.png"
        )

        # get all platform wrs
        for platform in platforms:
            pf_varlink = (
                f"&var-{platforms[platform]['subcat_id']}={platforms[platform]['id']}"
            )
            data = await self.get(
                f"leaderboards/{game['id']}/category/{category}?top=1&embed=players{varlink}{pf_varlink}"
            )
            data = data["data"]
            rundata = data["runs"]
            runners = []
            for _runners in data["players"]["data"]:
                runners.append(_runners["names"]["international"])
            runners = ", ".join(runners)
            e.add_field(
                name=platforms[platform]["name"],
                value=f"{runners} (**[{realtime(rundata[0]['run']['times']['realtime_t'])}]({rundata[0]['run']['weblink']})**)",
                inline=False,
            )

        # finalize embed the send it
        e.set_author(
            name=f"MCBE - {cat_name} - {seeds[sel_seed]['name']}",
            icon_url=self.LOGO,
        )
        await ctx.send(embed=e)

    @commands.command(usage="(username)")
    async def runcount(self, ctx, user: str):
        """Counts the number of runs a user has."""
        offset = 0
        user_id = await self.get_user_id(user)
        if not user_id:
            return await ctx.send(f"There's no user called `{user}`")
        link = f"runs?user={user_id}&max=200"
        data = []
        fullgame_runs = 0
        runs = 0

        repeat = True
        while repeat is True:
            _ = await self.get(link + f"&offset={offset}")

            for run in _["data"]:
                data.append(run)

            if _["pagination"]["links"]:
                if _["pagination"]["links"][-1]["rel"] == "prev":
                    repeat = False
                elif _["pagination"]["links"][-1]["rel"] == "next":
                    offset += 200
            else:
                repeat = False

        for run in data:
            if not run["level"]:
                fullgame_runs += 1
            runs += 1
        await ctx.send(
            f"{await self.get_username(user_id)} has "
            + f"**{runs}** runs, **{fullgame_runs}** full game runs and "
            + f"**{runs - fullgame_runs}** IL runs"
        )

    @commands.command(usage="(username)")
    async def wrcount(self, ctx, user: str):
        """Counts the number of world records a user has."""
        link = f"users/{user}/personal-bests"
        data = await self.get(link)
        try:
            data = data["data"]
        except KeyError:
            return await ctx.send(f"There's no user called `{user}`")
        fullgame_wr = 0
        ils_wr = 0
        for pb in data:
            if pb["place"] > 1:
                continue

            if pb["run"]["level"]:
                ils_wr += 1
            elif not pb["run"]["level"]:
                fullgame_wr += 1
            else:
                # Uh oh!
                continue
        await ctx.send(
            f"{await self.get_username(await self.get_user_id(user))} has "
            + f"**{fullgame_wr + ils_wr}** world records, **{fullgame_wr}** full game "
            + f"record{'s' if fullgame_wr > 1 else ''} and "
            + f"**{ils_wr}** IL record{'s' if ils_wr > 1 else ''}"
        )

    @commands.command(aliases=["lb"], usage="(game) [category] [sub category]")
    async def leaderboard(
        self, ctx, game: str, category: str = None, sub_category: str = None
    ):
        """Get leaderboard for a specific game."""
        _ = game
        game = await self.get_game(game)
        if not game:
            return await ctx.send("There's no game called `{}`".format(_))
        game = game[0]
        link = f"games/{game['id']}/records?miscellaneous=no&scope=full-game&top=10"
        if category:
            cat_dict = await self.get_subcats(game["id"], pformat(category))
            if not cat_dict:
                return await ctx.send(
                    f"This game doesn't have a category called {category}"
                )
            link = f"leaderboards/{game['id']}/category/{cat_dict[pformat(category)]['id']}?top=10"
        var_link = ""
        if (
            sub_category
            and pformat(sub_category) in cat_dict[pformat(category)]["sub_cats"]
        ):
            sub_cats = cat_dict[pformat(category)]["sub_cats"]
            var_link = (
                "&var-"
                + sub_cats[pformat(sub_category)]["subcat_id"]
                + "="
                + sub_cats[pformat(sub_category)]["id"]
            )

        # Get data from speedrun.com api
        data = await self.get(
            link + var_link + "&embed=game,category,players,platforms,regions"
        )
        data = data["data"]
        if not category:
            data = data[0]
            category = data["category"]["data"]["name"]
            cat_dict = await self.get_subcats(game["id"], pformat(category))
        cat_name = data["category"]["data"]["name"]
        if not data:
            return

        # Get all players
        players = {}
        for player in data["players"]["data"]:
            try:
                players[player["id"]] = player["names"]["international"]
            except KeyError:
                players[player["name"]] = player["name"]

        # Get all platforms
        platforms = {}
        for platform in data["platforms"]["data"]:
            platforms[platform["id"]] = platform["name"]

        # Init discord Embed
        e = discord.Embed(
            title="Leaderboard",
            colour=discord.Colour.gold(),
            url=data["runs"][0]["run"]["weblink"],
        )

        e.set_author(
            name=cat_name,
            url=data["category"]["data"]["weblink"],
            icon_url=self.LOGO,
        )

        for run in data["runs"]:
            # Get run's players
            run_players = []
            for player in run["run"]["players"]:
                if player["rel"] == "user":
                    run_players.append(players[player["id"]])
                elif player["rel"] == "guest":
                    run_players.append(players[player["name"]])
                else:
                    # Something is wrong, lets just return None D:
                    return
            e.add_field(
                name=f"{run['place']}. "
                + ", ".join(run_players)
                + " in "
                + realtime(run["run"]["times"]["primary_t"]),
                value=f"Date Played `{run['run']['date']}` | "
                + f"Played on `{platforms[run['run']['system']['platform']]}` | "
                + f"[Watch the run]({await self.generate_tinyUrl(run['run']['weblink'])})",
                inline=False,
            )

        e.set_thumbnail(url=data["game"]["data"]["assets"]["cover-large"]["uri"])
        await ctx.send(embed=e)

    @commands.command(
        aliases=["wr"],
        usage="(game) (category) [sub category]",
        example='{prefix}worldrecord mc "Any% Glitchless" "Random Seed"\n'
        + "{prefix}wr Celeste",
    )
    async def worldrecord(
        self, ctx, game, category: str = None, sub_category: str = None
    ):
        """Get the world record for a specific game."""
        _ = game
        game = await self.get_game(game)
        if not game:
            return await ctx.send("There's no game called `{}`".format(_))
        game = game[0]
        link = f"games/{game['id']}/records?miscellaneous=no&scope=full-game&top=1"
        if category:
            cat_dict = await self.get_subcats(game["id"], pformat(category))
            if not cat_dict:
                return await ctx.send(
                    f"This game doesn't have a category called {category}"
                )
            link = f"leaderboards/{game['id']}/category/{cat_dict[pformat(category)]['id']}?top=1"
        var_link = ""
        if (
            sub_category
            and pformat(sub_category) in cat_dict[pformat(category)]["sub_cats"]
        ):
            sub_cats = cat_dict[pformat(category)]["sub_cats"]
            var_link = (
                "&var-"
                + sub_cats[pformat(sub_category)]["subcat_id"]
                + "="
                + sub_cats[pformat(sub_category)]["id"]
            )

        # Get data from speedrun.com api
        data = await self.get(
            link + var_link + "&embed=game,category,players,platforms,regions"
        )
        data = data["data"]
        if not category:
            data = data[0]
            category = data["category"]["data"]["name"]
            cat_dict = await self.get_subcats(game["id"], pformat(category))
        if not data:
            return

        players = []
        for i in data["players"]["data"]:
            try:
                players.append(i["names"]["international"])
            except KeyError:
                players.append(i["name"])

        e = discord.Embed(
            title=realtime(data["runs"][0]["run"]["times"]["primary_t"])
            + " by "
            + ", ".join(players),
            colour=discord.Colour.gold(),
            url=data["runs"][0]["run"]["weblink"],
        )
        e.set_thumbnail(url=data["game"]["data"]["assets"]["cover-large"]["uri"])
        e.set_author(
            name=f"{game['name']} - {cat_dict[pformat(category)]['name']}",
            icon_url=self.LOGO,
        )
        e.add_field(
            name="Date Played", value=data["runs"][0]["run"]["date"], inline=False
        )
        e.add_field(
            name="Played On", value=data["platforms"]["data"][0]["name"], inline=False
        )
        await ctx.send(embed=e)

    @commands.command(aliases=["cats"])
    async def categories(self, ctx, game):
        """Get speedrun categories for a specific game."""
        games = await self.src.get_games(game, embeds=["categories"])
        e = discord.Embed(
            title=f"{games[0].name} Categories",
            colour=discord.Colour.gold(),
        )
        e.set_author(
            name=f"speedrun.com",
            icon_url=self.LOGO,
        )
        e.set_thumbnail(url=str(games[0].assets["cover-large"]))
        for cat in games[0].categories:
            e.add_field(
                name=cat.name, value=pformat(cat.name), inline=False
            )
        await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(SRC(bot))
