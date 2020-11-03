import discord
from discord.ext import commands, ipc

class IpcRoutes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @ipc.server.route()
    async def get_bot_guilds(self, data):
        return self.bot.guilds 
    
    @ipc.server.route()
    async def get_member_count(self, data):
        guild = self.bot.get_guild(int(data.guild_id)) # get the guild object using parsed guild_id

        return guild.member_count # return the member count to the client

    @ipc.server.route()
    async def set_prefixes(self, data):
        guild = self.bot.get_guild(int(data.guild_id))
        prefixes = list(data.prefixes)
        self.bot.set_guild_prefixes(guild, prefixes)

def setup(bot):
    bot.add_cog(IpcRoutes(bot))
