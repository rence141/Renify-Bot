import os
import discord
import wavelink
from discord.ext import commands
from collections import defaultdict
from time import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('renify_bot.log'), logging.StreamHandler()]
)
logger = logging.getLogger('RenifyBot')

# --- CONFIGURATION ---
# It's best practice to use environment variables for sensitive info!
# Use a .env file and a library like `python-dotenv` for local testing.
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_BOT_TOKEN_HERE")
LAVALINK_HOST = os.getenv("LAVALINK_HOST", "localhost")
LAVALINK_PORT = int(os.getenv("LAVALINK_PORT", 2333))
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD", "renifythoushallnotpass")

# Security constants
MAX_QUERY_LENGTH = 500
MAX_QUEUE_SIZE = 50  # Default (will be overridden by tier)
COMMAND_COOLDOWN = 30
MAX_CALLS_PER_WINDOW = 5

# Tier system
TIER_LIMITS = {
    'FREE': 500,      # Free tier: 500 tracks
    'PREMIUM': 5000,  # Premium tier: 5000 tracks
    'DIAMOND': None   # Diamond tier: Unlimited (None = unlimited)
}

def get_user_tier(user_id: int) -> str:
    """Get user's tier. For now, default to FREE."""
    # TODO: Implement your payment/subscription system here
    # Example: Check database or payment API
    return 'FREE'  # Default

def get_queue_limit(tier: str) -> int | None:
    """Get queue limit based on tier."""
    return TIER_LIMITS.get(tier, 500)

# --- RATE LIMITER ---
class RateLimiter:
    def __init__(self):
        self.users = defaultdict(list)
    
    def is_rate_limited(self, user_id: int) -> bool:
        now = time()
        self.users[user_id] = [call_time for call_time in self.users[user_id] if now - call_time < COMMAND_COOLDOWN]
        limited = len(self.users[user_id]) >= MAX_CALLS_PER_WINDOW
        if not limited:
            self.users[user_id].append(now)
        return limited

rate_limiter = RateLimiter()

# --- INPUT VALIDATION ---
def validate_query(query: str) -> tuple[bool, str]:
    """Validate and sanitize user input"""
    if not query:
        return False, "❌ Please provide a search query."
    if len(query) > MAX_QUERY_LENGTH:
        return False, f"❌ Query too long (max {MAX_QUERY_LENGTH} characters)."
    dangerous_chars = ['\n', '\r', '\x00']
    if any(char in query for char in dangerous_chars):
        return False, "❌ Invalid characters in query."
    query = query.strip()
    if len(query) < 1:
        return False, "❌ Query cannot be empty."
    return True, query

# --- BOT CLASS SETUP ---
class RenifyBot(commands.Bot):
    """
    Renify – The Conversational Music Bot Core.
    Handles Wavelink connection and core commands.
    """
    def __init__(self):
        # Intents are required for Discord to allow your bot to see certain events
        intents = discord.Intents.default()
        intents.message_content = True  # Required for text commands (mentions/NLP later)
        
        # Use a music-themed activity
        activity = discord.Activity(
            type=discord.ActivityType.listening, 
            name="the vibe"
        )
        
        super().__init__(
            command_prefix=commands.when_mentioned, # For @Renify commands later
            intents=intents,
            activity=activity
        )
        
        # This will hold the Wavelink node connection
        self.wavelink = None

    async def on_ready(self):
        """Called when the bot is connected to Discord."""
        logger.info(f'🤖 Logged in as: {self.user} (ID: {self.user.id})')
        print(f'🤖 Logged in as: {self.user} (ID: {self.user.id})')
        print(f'Starting Wavelink node connection...')
        
        # 1. Connect to Lavalink
        await self.setup_wavelink()
        
        # 2. Sync Application Commands (Slash Commands)
        await self.tree.sync()
        logger.info('✅ Slash commands synced successfully.')
        print('✅ Slash commands synced successfully.')
        print('--------------------------------------')


    async def setup_wavelink(self):
        """Connects the bot to the Lavalink server."""
        try:
            # Create a Wavelink node object
            node = wavelink.Node(
                uri=f'http://{LAVALINK_HOST}:{LAVALINK_PORT}',
                password=LAVALINK_PASSWORD
            )
            
            # Connect the node to the bot
            self.wavelink = await wavelink.Pool.connect(client=self, nodes=[node])
            
            # Bind the event listener for when tracks end
            self.wavelink.listen(wavelink.TrackStart, self.on_wavelink_track_start)
            self.wavelink.listen(wavelink.TrackEndEvent, self.on_wavelink_track_end)

            logger.info(f'🎵 Wavelink node connected: {node.identifier}')
            print(f'🎵 Wavelink node connected: {node.identifier}')

        except Exception as e:
            logger.error(f'❌ Failed to connect to Lavalink: {e}', exc_info=True)
            print(f'❌ Failed to connect to Lavalink: {e}')

    
    async def on_wavelink_track_start(self, event: wavelink.TrackStart):
        """Event handler for when a track starts playing."""
        player = event.player
        track = event.track
        channel = player.home_channel # We'll set this in the /play command
        
        # Create the 'Now Playing' embed
        embed = discord.Embed(
            title="🎧 Now Playing",
            description=f"**[{track.title}]({track.uri})** by `{track.author}`",
            color=0x1DB954 # Spotify Green
        )
        
        # If possible, get the thumbnail for a sleeker look
        # Note: Wavelink's Track object might not always have the thumbnail URL readily
        # available without extra lookups depending on the source (YouTube/Spotify).
        # You'll likely need to fetch it in the /play command and store it.
        # For this foundation, we'll keep it simple:
        
        await channel.send(embed=embed)


    async def on_wavelink_track_end(self, event: wavelink.TrackEndEvent):
        """Event handler for when a track finishes."""
        player = event.player
        
        # Check if there are more tracks in the queue
        if player.queue.is_empty:
            # No more songs, automatically disconnect after a short delay
            await discord.utils.sleep_until(discord.utils.utcnow() + 30) # Wait 30 seconds
            if player.queue.is_empty and player.is_playing() == False:
                 await player.disconnect()
                 await player.home_channel.send("Queue finished. Time to recharge! 🔋")
        else:
            # Play the next track in the queue
            next_track = player.queue.get()
            await player.play(next_track)
            
# --- COMMANDS ---

# We'll use a subclass of wavelink.Player to add a 'home_channel' attribute
# which is useful for sending 'Now Playing' messages.
class RenifyPlayer(wavelink.Player):
    """Custom Wavelink Player to hold the text channel."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.home_channel = None # The text channel where commands are used

@commands.guild_only() # Music commands should only work in a server
class MusicCog(commands.Cog):
    """Cog for all the music-related slash commands."""
    
    def __init__(self, bot: RenifyBot):
        self.bot = bot

    async def get_player(self, ctx: discord.Interaction) -> RenifyPlayer:
        """Helper function to get the player or connect if necessary."""
        
        # Get the voice channel the user is in
        if not ctx.user.voice or not ctx.user.voice.channel:
            await ctx.response.send_message("❌ You must be in a voice channel to use music commands!", ephemeral=True)
            return None
            
        voice_channel = ctx.user.voice.channel
        
        # Check bot permissions
        me = ctx.guild.me
        if not voice_channel.permissions_for(me).connect:
            await ctx.response.send_message("❌ I don't have permission to connect to that voice channel!", ephemeral=True)
            return None
        
        if not voice_channel.permissions_for(me).speak:
            await ctx.response.send_message("❌ I don't have permission to speak in that voice channel!", ephemeral=True)
            return None
        
        # Get the Wavelink player for this guild
        player: RenifyPlayer = ctx.guild.voice_client

        if not player:
            # Bot is not connected, connect it now
            player = await voice_channel.connect(cls=RenifyPlayer)
            player.home_channel = ctx.channel # Set the text channel
            
        elif player.channel != voice_channel:
            # Bot is in a different channel
            await ctx.response.send_message(f"❌ I'm already playing music in {player.channel.mention}!", ephemeral=True)
            return None
            
        return player

    @discord.app_commands.command(name="play", description="Search for a song/playlist or paste a URL to play.")
    @discord.app_commands.describe(query="The song title, artist, or URL (YouTube/Spotify link).")
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
            await interaction.response.send_message("⏱️ You're sending commands too fast! Please wait a moment.", ephemeral=True)
            logger.warning(f"Rate limit hit for user {interaction.user.id}")
            return
        
        await interaction.response.defer() # Acknowledge the command immediately

        player = await self.get_player(interaction)
        if not player:
            return

        # Log command usage
        logger.info(f"User {interaction.user.name} ({interaction.user.id}) requested /play with query: {query[:100]}")

        try:
            # Search for tracks using Wavelink's search function
            tracks = await wavelink.Playable.search(query)
        except Exception as e:
            logger.error(f"Search failed for user {interaction.user.id}: {e}", exc_info=True)
            await interaction.followup.send("❌ Could not search for that track. Please try again.", ephemeral=True)
            return
            
        if not tracks:
            await interaction.followup.send(f"🧐 Couldn't find any results for: **`{query[:50]}`**", ephemeral=True)
            return
        
        # Get user tier and queue limit
        user_tier = get_user_tier(interaction.user.id)
        queue_limit = get_queue_limit(user_tier)
        current_queue_size = len(player.queue)
        
        # Check queue size limits based on tier
        if isinstance(tracks, wavelink.Playlist):
            # Handle playlists (e.g., Spotify/YouTube playlists)
            playlist = tracks
            
            if queue_limit is not None:
                if len(playlist.tracks) + current_queue_size > queue_limit:
                    tier_emoji = {"FREE": "🆓", "PREMIUM": "⭐", "DIAMOND": "💎"}.get(user_tier, "")
                    await interaction.followup.send(
                        f"❌ {tier_emoji} Your {user_tier} tier allows {queue_limit} tracks. "
                        f"Adding this playlist ({len(playlist.tracks)} tracks) would exceed the limit. "
                        f"Upgrade to increase your limit!",
                        ephemeral=True
                    )
                    return
            
            player.queue.extend(playlist.tracks)
            
            # Start playing if not already playing
            if not player.is_playing() and not player.paused:
                await player.play(player.queue.get())

            tier_emoji = {"FREE": "🆓", "PREMIUM": "⭐", "DIAMOND": "💎"}.get(user_tier, "")
            await interaction.followup.send(
                f"{tier_emoji} 🎶 Loaded **{len(playlist.tracks)}** tracks from playlist **[{playlist.name[:50]}]({query[:100]})**. "
                f"({current_queue_size}/{queue_limit if queue_limit else '∞'} in queue)"
            )
            logger.info(f"Loaded playlist with {len(playlist.tracks)} tracks for {user_tier} tier user")

        else:
            # Handle single tracks (take the best result)
            track = tracks[0]
            
            if queue_limit is not None and len(player.queue) >= queue_limit:
                tier_emoji = {"FREE": "🆓", "PREMIUM": "⭐", "DIAMOND": "💎"}.get(user_tier, "")
                await interaction.followup.send(
                    f"❌ {tier_emoji} Queue is full (max {queue_limit} tracks for {user_tier} tier). "
                    f"Upgrade for a higher limit!",
                    ephemeral=True
                )
                return
            
            if player.is_playing() or player.paused:
                # Add to queue if something is already playing
                player.queue.put(track)
                await interaction.followup.send(
                    f"🎧 Queued **[{track.title[:50]}]({track.uri})** by `{track.author}`."
                )
            else:
                # Start playing immediately
                await player.play(track)
                # The 'Now Playing' message is sent by the on_wavelink_track_start event
                await interaction.followup.send(f"🎶 Found it! Playing now...")
                logger.info(f"Playing track: {track.title}")
                
                
    @discord.app_commands.command(name="skip", description="Skips the current track.")
    @discord.app_commands.checks.has_permissions(manage_messages=True)
    async def skip_command(self, interaction: discord.Interaction):
        """Skips the current track."""
        player = await self.get_player(interaction)
        if not player:
            return
            
        if not player.is_playing():
            await interaction.response.send_message("🤷 I'm not playing anything right now!", ephemeral=True)
            return
        
        logger.info(f"User {interaction.user.name} skipped the track")
        # The TrackEndEvent handler will automatically play the next track (if any)
        await player.stop() 
        await interaction.response.send_message("⏭️ Skipped! Next track coming up...")

    @discord.app_commands.command(name="pause", description="Pauses the music.")
    async def pause_command(self, interaction: discord.Interaction):
        """Pauses the music."""
        player = await self.get_player(interaction)
        if not player:
            return

        if player.paused:
            await interaction.response.send_message("It's already paused! Try `/resume`.", ephemeral=True)
            return

        await player.pause(True)
        await interaction.response.send_message("⏸️ Paused the music. Take a breather.")

    @discord.app_commands.command(name="resume", description="Resumes the music.")
    async def resume_command(self, interaction: discord.Interaction):
        """Resumes the music."""
        player = await self.get_player(interaction)
        if not player:
            return

        if not player.paused:
            await interaction.response.send_message("I'm already playing! Try `/pause`.", ephemeral=True)
            return

        await player.pause(False)
        await interaction.response.send_message("▶️ Back to the music!")

    @discord.app_commands.command(name="stop", description="Stops the music and clears the queue.")
    @discord.app_commands.checks.has_permissions(manage_messages=True)
    async def stop_command(self, interaction: discord.Interaction):
        """Stops the music and clears the queue."""
        player = await self.get_player(interaction)
        if not player:
            return
            
        if not player.is_playing() and player.queue.is_empty:
             await interaction.response.send_message("Nothing to stop.", ephemeral=True)
             return
        
        logger.info(f"User {interaction.user.name} stopped the music")
        # Clear the queue
        player.queue.clear()
        
        # Stop the player (triggers TrackEnd and disconnects if queue is empty)
        await player.stop()
        
        # Disconnect immediately
        await player.disconnect()
        
        await interaction.response.send_message("⏹️ Music stopped and queue cleared. Thanks for letting me handle the vibe!")

    @discord.app_commands.command(name="help", description="Shows a helpful guide for using Renify Bot.")
    async def help_command(self, interaction: discord.Interaction):
        """Shows help information for first-time users."""
        embed = discord.Embed(
            title="🎵 Renify Bot - Help & Guide",
            description="Welcome to **Renify**, your music bot! Here's everything you need to know.",
            color=0x1DB954
        )
        
        # Commands section
        commands_text = """
**🎵 Music Commands:**
`/play <song name>` - Play music or add to queue
`/pause` - Pause the current song
`/resume` - Resume paused music
`/queue` - View your music queue

**⚙️ Control Commands (Requires Permissions):**
`/skip` - Skip to next song
`/stop` - Stop music and disconnect bot

**❓ Help:**
`/help` - Show this guide
        """
        embed.add_field(name="📜 Commands", value=commands_text, inline=False)
        
        # Queue limits
        user_tier = get_user_tier(interaction.user.id)
        queue_limit = get_queue_limit(user_tier)
        tier_emoji = {"FREE": "🆓", "PREMIUM": "⭐", "DIAMOND": "💎"}.get(user_tier, "")
        limit_text = f"{queue_limit:,} tracks" if queue_limit else "Unlimited tracks"
        
        tier_info = f"""
**Your Tier:** {tier_emoji} {user_tier}
**Queue Limit:** {limit_text}
**Current Plan:** Free (All users start here)
        """
        embed.add_field(name="💎 Your Subscription", value=tier_info, inline=False)
        
        # Quick start
        quick_start = """
1. **Join a voice channel** in this server
2. Use `/play <song name>` to start playing music
3. Queue up to 500 songs (your free tier limit)
4. Enjoy! The bot will auto-disconnect when queue ends
        """
        embed.add_field(name="🚀 Quick Start", value=quick_start, inline=False)
        
        # Tips
        tips = """
• You can search for songs by name or paste YouTube URLs
• Add playlists with `/play <playlist url>`
• Queue fills up! Check `/queue` to see what's next
• Bot needs to be in your voice channel to work
        """
        embed.add_field(name="💡 Tips & Tricks", value=tips, inline=False)
        
        embed.set_footer(text="Renify Bot v1.0 | Made with ❤️ for music lovers")
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="queue", description="Shows the current music queue.")
    async def queue_command(self, interaction: discord.Interaction):
        """Shows the current music queue."""
        player = await self.get_player(interaction)
        if not player:
            return

        if not player.queue.is_empty:
            queue_list = "\n".join(
                [
                    f"**{i+1}.** [{track.title}]({track.uri}) by `{track.author}`"
                    for i, track in enumerate(player.queue)
                ]
            )
            
            queue_embed = discord.Embed(
                title="📜 Current Queue",
                description=queue_list,
                color=0x1DB954
            )
            
            # Add currently playing track to the embed header
            if player.current:
                queue_embed.set_author(name=f"Currently Playing: {player.current.title}", url=player.current.uri)
            
            await interaction.response.send_message(embed=queue_embed)
        else:
            await interaction.response.send_message("The queue is empty. Use `/play` to add some tracks!", ephemeral=True)

# --- BOT RUNNING ---
async def main():
    """Main function to run the bot."""
    bot = RenifyBot()
    # Add the music commands cog
    await bot.add_cog(MusicCog(bot))
    
    # Check for token and run
    if not DISCORD_TOKEN or DISCORD_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("DISCORD_TOKEN not set!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!! WARNING: You need to set your DISCORD_TOKEN in the script or environment variables. !!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    else:
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    # Use asyncio.run for a cleaner shutdown
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutting down...")
        print("\n👋 Renify shutting down...")

        