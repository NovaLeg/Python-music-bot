import discord
import os
from discord.ext import commands
from setting.config import token, owner

def format_guild_count(count):
    if count >= 1000:
        return f"{count / 1000:.1f}k"
    return f"{count}"

def get_custom_activity(bot):
    guild_count = format_guild_count(len(bot.guilds))
    return discord.CustomActivity(
        name="Custom Status",
        state=f"/help - {guild_count} Servers!",
    )

class nova(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(command_prefix='.', intents=discord.Intents.all(), shard_count=2)
        self.owner_ids = owner

    async def on_ready(self):
        print(f'{self.user.display_name} is ready!')
        activity = get_custom_activity(self)
        await self.change_presence(activity=activity)

    async def setup_hook(self):
        await self.load_extension('jishaku')
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f'[Loaded] `{filename}`')
                except Exception as e:
                    print(f'Failed to load {filename}: {e}')
        await self.tree.sync()

bot = nova()
bot.run("token")
