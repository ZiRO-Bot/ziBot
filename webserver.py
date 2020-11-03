import getpass
import os
import json

from discord.ext import ipc
from quart import Quart, request, redirect, session
from requests_oauthlib import OAuth2Session

with open("config.json", "r") as f:
    config = json.load(f)

app = Quart(__name__)
ipc_client = ipc.Client(secret_key=config['webserver']['secret']) # secret_key must be the same as your server

# Settings for oauth
base_discord_api_url = 'https://discordapp.com/api'
client_id = config['webserver']['discord_client_id'] # Get from https://discordapp.com/developers/applications
client_secret = config['webserver']['discord_secret'] 
redirect_uri=f"https://127.0.0.1:5000/oauth_callback"
scope = ['identify', 'guilds']
token_url = 'https://discordapp.com/api/oauth2/token'
authorize_url = 'https://discordapp.com/api/oauth2/authorize'

@app.before_first_request
async def before():
    app.ipc_node = await ipc_client.discover() # discover IPC Servers on your network

app.secret_key = os.urandom(24)

@app.route("/")
async def index():
    """
    Presents the 'Login with Discord' link
    """
    oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)
    login_url, state = oauth.authorization_url(authorize_url)
    session['state'] = state
    if 'discord_token' in session:
        discord = OAuth2Session(client_id, token=session['discord_token'])
        response = discord.get(base_discord_api_url + '/users/@me')
        data = response.json()
        return f"Welcome back, {data['username']}" + f"<img src='https://cdn.discordapp.com/avatars/{data['id']}/{data['avatar']}.jpg'/>"
    return '<a href="' + login_url + '">Login with Discord</a>'

@app.route("/oauth_callback")
async def oauth_callback():
    """
    The callback we specified in our app.
    Processes the code given to us by Discord and sends it back
    to Discord requesting a temporary access token so we can 
    make requests on behalf (as if we were) the user.
    e.g. https://discordapp.com/api/users/@me
    The token is stored in a session variable, so it can
    be reused across separate web requests.
    """
    discord = OAuth2Session(client_id, redirect_uri=redirect_uri, state=session['state'], scope=scope)
    token = discord.fetch_token(
        token_url,
        client_secret=client_secret,
        authorization_response=request.url,
    )
    session['discord_token'] = token
    return 'Thanks for granting us authorization. We are logging you in! You can now visit <a href="/guilds">/guilds</a>'


@app.route("/guilds")
async def guilds():
    """
    Example profile page to demonstrate how to pull the user information
    once we have a valid access token after all OAuth negotiation.
    """
    if not session:
        return "<b>Something went wrong!</b>"
    discord = OAuth2Session(client_id, token=session['discord_token'])
    response = discord.get(base_discord_api_url + '/users/@me/guilds')
    json_guilds = response.json()
    guilds = {}
    for guild in json_guilds:
        perm = guild['permissions']
        man_guild = False
        if (int(perm) & 32) == 32:
            man_guild = True
        if man_guild:
            guilds[guild['id']] = {"name": guild['name'], "MANAGE_GUILD": man_guild}
    member_count = await app.ipc_node.request("get_member_count", guild_id=745481731133669476)
    # https://discordapp.com/developers/docs/resources/user#user-object-user-structure
    return 'Manage Guild: %s' % guilds

@app.cli.command('run')
def run():
    app.run(port=5000, certfile='certificate.pem', keyfile='privkey.pem')

# if __name__ == "__main__":
#     app.run(certfile='certificate.pem', keyfile='privkey.pem')
