import os
import discord
import wavelink
from discord.ext import commands
from discord import app_commands, ui
from collections import defaultdict
from time import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('renify_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('RenifyBot')

# --- CONFIGURATION ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_BOT_TOKEN_HERE")
LAVALINK_HOST = os.getenv("LAVALINK_HOST", "localhost")
LAVALINK_PORT = int(os.getenv("LAVALINK_PORT", 2333))
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD", "renifythoushallnotpass")

# Security constants
MAX_QUERY_LENGTH = 500
MAX_QUEUE_SIZE = 50
COMMAND_COOLDOWN = 30  # seconds
MAX_CALLS_PER_WINDOW = 5

# --- RATE LIMITER ---
class RateLimiter:
    """Simple in-memory rate limiter"""
    def __init__(self):
        self.users = defaultdict(list)
    
    def is_rate_limited(self, user_id: int, max_calls: int = MAX_CALLS_PER_WINDOW, window: int = COMMAND_COOLDOWN) -> bool:
        now = time()
        self.users[user_id] = [
            call_time for call_time in self.users[user_id] 
            if now - call_time < window
        ]
        limited = len(self.users[user_id]) >= max_calls
        if not limited:
            self.users[user_id].append(now)
        return limited
    
    def reset(self, user_id: int):
        """Reset rate limit for a user"""
        self.users[user_id] = []

rate_limiter = RateLimiter()

# --- INPUT VALIDATION ---
def validate_query(query: str) -> tuple[bool, str]:
    """Validate and sanitize user input"""
    if not query:
        return False, "❌ Please provide a search query."
    
    # Check length
    if len(query) > MAX_QUERY_LENGTH:
        return False, f"❌ Query too long (max {MAX_QUERY_LENGTH} characters)."
    
    # Remove dangerous characters
    dangerous_chars = ['\n', '\r', '\x00']
    if any(char in query for char in dangerous_chars):
        return False, "❌ Invalid characters in query."
    
    # Strip whitespace
    query = query.strip()
    
    if len(query) < 1:
        return False, "❌ Query cannot be empty."
    
    return True, query

# --- CUSTOM PLAYER CLASS ---
class RenifyPlayer(wavelink.Player):
    """Custom Wavelink Player to hold the text channel."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.home_channel = None

# --- BOT CLASS SETUP ---
class RenifyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        activity = discord.Activity(
            type=discord.ActivityType.listening, 
            name="the vibe"
        )
        
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            activity=activity
        )
        
        self.wavelink = None

    async def on_ready(self):
        logger.info(f'🤖 Logged in as: {self.user} (ID: {self.user.id})')
        logger.info(f'Starting Wavelink node connection...')
        
        await self.setup_wavelink()
        await self.tree.sync()
        logger.info('✅ Slash commands synced successfully.')
        print('--------------------------------------')

    async def setup_wavelink(self):
        try:
            node = wavelink.Node(
                uri=f'http://{LAVALINK_HOST}:{LAVALINK_PORT}',
                password=LAVALINK_PASSWORD
            )
            
            self.wavelink = await wavelink.Pool.connect(client=self, nodes=[node])
            self.wavelink.listen(wavelink.TrackStartEvent, self.on_wavelink_track_start)
            self.wavelink.listen(wavelink.TrackEndEvent, self.on_wavelink_track_end)

            logger.info(f'🎵 Wavelink node connected: {node.identifier}')

        except Exception as e:
            logger.error(f'❌ Failed to connect to Lavalink: {e}', exc_info=True)

    async def on_wavelink_track_start(self, event: wavelink.TrackStartEvent):
        player = event.player
        track = event.track
        channel = player.home_channel
        
        if channel:
            embed = discord.Embed(
                title="🎧 Now Playing",
                description=f"**[{track.title}]({track.uri})** by `{track.author}`",
                color=0x1DB954
            )
            try:
                await channel.send(embed=embed)
            except Exception as e:
                logger.error(f"Failed to send track start message: {e}")

    async def on_wavelink_track_end(self, event: wavelink.TrackEndEvent):
        player = event.player
        
        if player.queue.is_empty:
            await discord.utils.sleep_until(discord.utils.utcnow() + 30)
            if player.queue.is_empty and player.is_playing() == False:
                await player.disconnect()
                try:
                    await player.home_channel.send("Queue finished. Time to recharge! 🔋")
                except:
                    pass
        else:
            next_track = player.queue.get()
            await player.play(next_track)

# --- COMMANDS ---
@commands.guild_only()
class MusicCog(commands.Cog):
    def __init__(self, bot: RenifyBot):
        self.bot = bot

    async def get_player(self, ctx: discord.Interaction) -> RenifyPlayer | None:
        if not ctx.user.voice or not ctx.user.voice.channel:
            await ctx.response.send_message(
                "❌ You must be in a voice channel to use music commands!", 
                ephemeral=True
            )
            return None
            
        voice_channel = ctx.user.voice.channel
        player: RenifyPlayer = ctx.guild.voice_client

        if not player:
            # Check bot permissions
            me = ctx.guild.me
            if not voice_channel.permissions_for(me).connect:
                await ctx.response.send_message(
                    "❌ I don't have permission to connect to that voice channel!", 
                    ephemeral=True
                )
                return None
            
            if not voice_channel.permissions_for(me).speak:
                await ctx.response.send_message(
                    "❌ I don't have permission to speak in that voice channel!", 
                    ephemeral=True
                )
                return None
            
            player = await voice_channel.connect(cls=RenifyPlayer)
            player.home_channel = ctx.channel
            
        elif player.channel != voice_channel:
            await ctx.response.send_message(
                f"❌ I'm already playing music in {player.channel.mention}!", 
                ephemeral=True
            )
            return None
            
        return player

    @discord.app_commands.command(name="play", description="Search for a song or paste a URL to play.")
    @discord.app_commands.describe(query="The song title, artist, or URL (YouTube link).")
    async def play_command(self, interaction: discord.Interaction, query: str):
        """The main play command with security enhancements."""
        
        # Input validation
        is_valid, result = validate_query(query)
        if not is_valid:
            await interaction.response.send_message(result, ephemeral=True)
            return
        
        query = result
        
        # Rate limiting
        if rate_limiter.is_rate_limited(interaction.user.id):
            await interaction.response.send_message(
                "⏱️ You're sending commands too fast! Please wait a moment.", 
                ephemeral=True
            )
            logger.warning(f"Rate limit hit for user {interaction.user.id}")
            return
        
        await interaction.response.defer()

        player = await self.get_player(interaction)
        if not player:
            return

        # Log command usage
        logger.info(f"User {interaction.user.name} ({interaction.user.id}) requested /play with query: {query[:100]}")

        try:
            tracks = await wavelink.Playable.search(query)
        except Exception as e:
            logger.error(f"Search failed for user {interaction.user.id}: {e}", exc_info=True)
            await interaction.followup.send(
                "❌ Could not search for that track. Please try again.", 
                ephemeral=True
            )
            return
            
        if not tracks:
            await interaction.followup.send(
                f"🧐 Couldn't find any results for: **`{query[:50]}`**", 
                ephemeral=True
            )
            return
            
        # Check queue size
        if isinstance(tracks, wavelink.Playlist):
            if len(tracks.tracks) + len(player.queue) > MAX_QUEUE_SIZE:
                await interaction.followup.send(
                    f"❌ Adding this playlist would exceed queue limit ({MAX_QUEUE_SIZE}).",
                    ephemeral=True
                )
                return
            
            playlist = tracks
            player.queue.extend(playlist.tracks)
            
            if not player.is_playing() and not player.paused:
                await player.play(player.queue.get())

            await interaction.followup.send(
                f"🎶 Loaded **{len(playlist.tracks)}** tracks from playlist **[{playlist.name[:50]}]({query[:100]})**."
            )
            logger.info(f"Loaded playlist with {len(playlist.tracks)} tracks")

        else:
            track = tracks[0]
            
            if len(player.queue) >= MAX_QUEUE_SIZE:
                await interaction.followup.send(
                    f"❌ Queue is full (max {MAX_QUEUE_SIZE} tracks).", 
                    ephemeral=True
                )
                return
            
            if player.is_playing() or player.paused:
                player.queue.put(track)
                await interaction.followup.send(
                    f"🎧 Queued **[{track.title[:50]}]({track.uri})** by `{track.author}`."
                )
            else:
                await player.play(track)
                await interaction.followup.send("🎶 Found it! Playing now...")
                logger.info(f"Playing track: {track.title}")
                
    @discord.app_commands.command(name="skip", description="Skips the current track.")
    @discord.app_commands.checks.has_permissions(manage_messages=True)
    async def skip_command(self, interaction: discord.Interaction):
        player = await self.get_player(interaction)
        if not player:
            return
            
        if not player.is_playing():
            await interaction.response.send_message(
                "🤷 I'm not playing anything right now!", 
                ephemeral=True
            )
            return
            
        logger.info(f"User {interaction.user.name} skipped the track")
        await player.stop()
        await interaction.response.send_message("⏭️ Skipped! Next track coming up...")

    @discord.app_commands.command(name="pause", description="Pauses the music.")
    async def pause_command(self, interaction: discord.Interaction):
        player = await self.get_player(interaction)
        if not player:
            return

        if player.paused:
            await interaction.response.send_message(
                "It's already paused! Try `/resume`.", 
                ephemeral=True
            )
            return

        await player.pause(True)
        logger.info(f"User {interaction.user.name} paused the music")
        await interaction.response.send_message("⏸️ Paused the music. Take a breather.")

    @discord.app_commands.command(name="resume", description="Resumes the music.")
    async def resume_command(self, interaction: discord.Interaction):
        player = await self.get_player(interaction)
        if not player:
            return

        if not player.paused:
            await interaction.response.send_message(
                "I'm already playing! Try `/pause`.", 
                ephemeral=True
            )
            return

        await player.pause(False)
        logger.info(f"User {interaction.user.name} resumed the music")
        await interaction.response.send_message("▶️ Back to the music!")

    @discord.app_commands.command(name="stop", description="Stops the music and clears the queue.")
    @discord.app_commands.checks.has_permissions(manage_messages=True)
    async def stop_command(self, interaction: discord.Interaction):
        player = await self.get_player(interaction)
        if not player:
            return
            
        if not player.is_playing() and player.queue.is_empty:
            await interaction.response.send_message("Nothing to stop.", ephemeral=True)
            return
            
        logger.info(f"User {interaction.user.name} stopped the music")
        player.queue.clear()
        await player.stop()
        await player.disconnect()
        await interaction.response.send_message(
            "⏹️ Music stopped and queue cleared. Thanks for letting me handle the vibe!"
        )

    @discord.app_commands.command(name="queue", description="Shows the current music queue.")
    async def queue_command(self, interaction: discord.Interaction):
        player = await self.get_player(interaction)
        if not player:
            return

        if not player.queue.is_empty:
            # Limit queue display to first 10 tracks
            queue_preview = list(player.queue)[:10]
            queue_list = "\n".join(
                [
                    f"**{i+1}.** [{track.title[:40]}]({track.uri}) by `{track.author[:30]}`"
                    for i, track in enumerate(queue_preview)
                ]
            )
            
            if len(player.queue) > 10:
                queue_list += f"\n... and {len(player.queue) - 10} more tracks"
            
            queue_embed = discord.Embed(
                title="📜 Current Queue",
                description=queue_list,
                color=0x1DB954
            )
            
            if player.current:
                queue_embed.set_author(
                    name=f"Currently Playing: {player.current.title[:50]}", 
                    url=player.current.uri
                )
            
            await interaction.response.send_message(embed=queue_embed)
        else:
            await interaction.response.send_message(
                "The queue is empty. Use `/play` to add some tracks!", 
                ephemeral=True
            )

# --- BOT RUNNING ---
async def main():
    bot = RenifyBot()
    await bot.add_cog(MusicCog(bot))
    
    if DISCORD_TOKEN == "YOUR_BOT_TOKEN_HERE" or not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN not set!")
        print("!!! WARNING: You need to set your DISCORD_TOKEN !!!")
    else:
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutting down...")
        print("\n👋 Renify shutting down...")

