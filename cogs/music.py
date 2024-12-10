import discord
from discord import app_commands
from discord.ext import commands
from collections import deque
import wavelink
import random
from setting.config import COLOR

class music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = deque()
        self.loop = False
        self.is_shuffled = False

    @commands.Cog.listener()
    async def on_ready(self):
        await self.node_connect()

    async def node_connect(self):
        await self.bot.wait_until_ready()
        await wavelink.NodePool.create_node(
            bot=self.bot,
            host="LAVALINK",
            port=0000,
            password="PASSWORD",
            https=False
        )

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel is not None and len(before.channel.members) == 1:
            vc: wavelink.Player = member.guild.voice_client
            if vc and vc.is_connected():
                await vc.disconnect()

    @app_commands.command(name="play", description="Play a song from a URL or search query.")
    @app_commands.checks.cooldown(1, 5)
    async def play(self, interaction: discord.Interaction, *, search: str):
        if not interaction.user.voice:
            return await interaction.response.send_message("You need to be in a voice channel to play music.", ephemeral=True)

        channel = interaction.user.voice.channel
        if not interaction.guild.voice_client:
            vc = await channel.connect(cls=wavelink.Player, self_deaf=True)
        else:
            vc: wavelink.Player = interaction.guild.voice_client

        tracks = await wavelink.YouTubeTrack.search(search)
        if not tracks:
            return await interaction.response.send_message("No tracks found.", ephemeral=True)

        track = tracks[0]
        self.queue.append(track)

        if not vc.is_playing():
            await vc.play(track)
            embed = discord.Embed(
                title="Now Playing",
                description=f"[{track.title}]({track.uri}) [<@{interaction.user.id}>]",
                color=COLOR
            )
            await interaction.response.send_message(embed=embed, view=self.setup_buttons())
        else:
            embed = discord.Embed(
                description=f"Added to queue: [{track.title}]({track.uri}) by {track.author}.",
                color=COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="queue", description="View the current queue of songs.")
    @app_commands.checks.cooldown(1, 5)
    async def queue_command(self, interaction: discord.Interaction):
        if not self.queue:
            embed = discord.Embed(description="The queue is currently empty.", color=COLOR)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        queue_list = "\n".join([f"[{track.title}]({track.uri})" for track in self.queue])
        embed = discord.Embed(title="Current Queue", description=queue_list, color=COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="skip", description="Skip the currently playing song.")
    @app_commands.checks.cooldown(1, 5)
    async def skip(self, interaction: discord.Interaction):
        vc: wavelink.Player = interaction.guild.voice_client
        if vc.is_playing():
            await vc.stop()
            if self.queue:
                next_track = self.queue.popleft()
                await vc.play(next_track)
                embed = discord.Embed(description=f"Skipped to: [{next_track.title}]({next_track.uri})", color=COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(description="No more tracks in the queue.", color=COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(description="Nothing is currently playing.", color=COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="pause", description="Pause the currently playing song.")
    @app_commands.checks.cooldown(1, 5)
    async def pause(self, interaction: discord.Interaction):
        vc: wavelink.Player = interaction.guild.voice_client
        if vc.is_playing():
            await vc.pause()
            embed = discord.Embed(description="Paused the player!", color=COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await vc.resume()
            embed = discord.Embed(description="Resumed the music!", color=COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="stop", description="Stop the music and clear the queue.")
    @app_commands.checks.cooldown(1, 5)
    async def stop(self, interaction: discord.Interaction):
        vc: wavelink.Player = interaction.guild.voice_client
        self.queue.clear()
        await vc.stop()
        await vc.disconnect()
        embed = discord.Embed(description="Stopped the music and disconnected!", color=COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="loop", description="Toggle loop for the current song.")
    @app_commands.checks.cooldown(1, 5)
    async def loop(self, interaction: discord.Interaction):
        self.loop = not self.loop
        status = "enabled" if self.loop else "disabled"
        embed = discord.Embed(description=f"Loop is now {status}.", color=COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="shuffle", description="Toggle shuffle for the queue.")
    @app_commands.checks.cooldown(1, 5)
    async def shuffle(self, interaction: discord.Interaction):
        self.is_shuffled = not self.is_shuffled
        if self.is_shuffled:
            random.shuffle(self.queue)
            embed = discord.Embed(description="Shuffle enabled.", color=COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(description="Shuffle disabled.", color=COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    def setup_buttons(self):
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Pause", style=discord.ButtonStyle.secondary, custom_id="music_pause"))
        view.add_item(discord.ui.Button(label="Skip", style=discord.ButtonStyle.secondary, custom_id="music_skip"))
        view.add_item(discord.ui.Button(label="Loop", style=discord.ButtonStyle.secondary, custom_id="music_loop"))
        view.add_item(discord.ui.Button(label="Shuffle", style=discord.ButtonStyle.secondary, custom_id="music_shuffle"))
        view.add_item(discord.ui.Button(label="Stop", style=discord.ButtonStyle.danger, custom_id="music_stop"))
        return view

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            if interaction.user.voice is None:
                return await interaction.response.send_message("You need to be in a voice channel.", ephemeral=True)

            vc: wavelink.Player = interaction.guild.voice_client

            if interaction.data['custom_id'] == "music_pause":
                if vc.is_playing():
                    await vc.pause()
                    embed = discord.Embed(description="Paused the player!", color=COLOR)
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await vc.resume()
                    embed = discord.Embed(description="Resumed the music!", color=COLOR)
                    await interaction.response.send_message(embed=embed, ephemeral=True)

            elif interaction.data['custom_id'] == "music_skip":
                await vc.stop()
                if self.queue:
                    next_track = self.queue.popleft()
                    await vc.play(next_track)
                    embed = discord.Embed(description=f"Skipped to: [{next_track.title}]({next_track.uri})", color=COLOR)
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    embed = discord.Embed(description="No more tracks in the queue.", color=COLOR)
                    await interaction.response.send_message(embed=embed, ephemeral=True)

            elif interaction.data['custom_id'] == "music_loop":
                self.loop = not self.loop
                status = "enabled" if self.loop else "disabled"
                embed = discord.Embed(description=f"Loop is now {status}.", color=COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=True)

            elif interaction.data['custom_id'] == "music_shuffle":
                self.is_shuffled = not self.is_shuffled
                if self.is_shuffled:
                    random.shuffle(self.queue)
                    embed = discord.Embed(description="Shuffle enabled.", color=COLOR)
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    embed = discord.Embed(description="Shuffle disabled.", color=COLOR)
                    await interaction.response.send_message(embed=embed, ephemeral=True)

            elif interaction.data['custom_id'] == "music_stop":
                self.queue.clear()
                await vc.stop()
                await vc.disconnect()
                embed = discord.Embed(description="Stopped the music and disconnected!", color=COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(music(bot))
