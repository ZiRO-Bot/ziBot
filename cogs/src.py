import aiohttp
import discord
import json
import re

from discord.ext import commands
from cogs.utilities.formatting import pformat, realtime, hformat


class SRC(commands.Cog, name="src"):
    def __init__(self, bot):
        self.bot = bot
        self.API_URL = "https://www.speedrun.com/api/v1/"
        self.session = self.bot.session

    async def get(self, _type, **kwargs):
        async with self.session.get(self.API_URL + _type, **kwargs) as url:
            data = json.loads(await url.text())
        return data

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
        cat_id = catdict[pformat(category)]["id"]
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
            # If data is empty try getting it from abbv or name
            data = await self.get(f"games?abbreviation={game}")
            data = data["data"]
            bulk = True
            if not data:
                data = await self.get("games", params={"name": game})
                data = data["data"]
                bulk = True
        game_info = []

        if bulk:
            for i in range(len(data) - 1):
                game_info.append(
                    {
                        "id": data[i]["id"],
                        "name": data[i]["names"]["international"],
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
            icon_url="https://www.speedrun.com/themes/Default/1st.png",
        )
        await ctx.send(embed=e)

    # @commands.command()
    # async def lb(self, ctx, game, category):
    #     data = await self.get_game(game)
    #     await self.get_subcats(data[0]["id"], category)
    #     # await ctx.send(data['names']['international'])
    #     pass

    @commands.command()
    async def wr(self, ctx, game, category: str = None, sub_category: str = None):
        game = await self.get_game(game)
        game = game[0]
        subcats = await self.get_subcats(game["id"], category)
        print(subcats)

    @commands.command(aliases=["cats"])
    async def categories(self, ctx, game):
        game = await self.get_game(game)
        game = game[0]
        catdict = await self.get_cats(game["id"])
        e = discord.Embed(
            title=f"{game['name']} Categories", colour=discord.Colour.gold()
        )
        e.set_author(
            name=f"speedrun.com",
            icon_url="https://www.speedrun.com/themes/Default/1st.png",
        )
        for i in catdict:
            e.add_field(
                name=catdict[i]["name"], value=pformat(catdict[i]["name"]), inline=False
            )
        await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(SRC(bot))
