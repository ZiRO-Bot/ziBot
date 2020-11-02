import json

from discord.ext import ipc
from quart import Quart
from requests_oauthlib import OAuth2Session

with open("config.json", "r") as f:
    config = json.load(f)

app = Quart(__name__)
base_discord_api_url = 'https://discordapp.com/api'
ipc_client = ipc.Client(secret_key=config['webserver']['secret']) # secret_key must be the same as your server

@app.before_first_request
async def before():
    app.ipc_node = await ipc_client.discover() # discover IPC Servers on your network

@app.route("/")
async def index():
    member_count = await app.ipc_node.request("get_member_count", guild_id=745481731133669476) # get the member count of server with ID 12345678

    return str(member_count) # display member count

if __name__ == "__main__":
    app.run()
