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
    handlers=[logging.FileHandler('renify_bot.log'), logging.StreamHandler()]
)
logger = logging.getLogger('RenifyBot')

# --- CONFIGURATION (Same as before) ---
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

# --- CUSTOM PLAYER CLASS (Updated) ---
class RenifyPlayer(wavelink.Player):
    """Custom Wavelink Player to hold the text channel and controller message."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.home_channel: discord.TextChannel = None 
        self.controller_message: discord.Message = None # Tracks the interactive message

    # You might want to override disconnect to clear the controller message
    async def disconnect(self):
        if self.controller_message:
            await self.controller_message.delete()
            self.controller_message = None
        await super().disconnect()


# --- BOT CLASS SETUP ---
class RenifyBot(commands.Bot):
    """
    Renify – The Conversational Music Bot with Interactive Controller.
    Handles Wavelink connection and core commands.
    """
    def __init__(self):
        # Intents are required for Discord to allow your bot to see certain events
        intents = discord.Intents.default()
        # intents.message_content = True  # Commented out to avoid privileged intents error
        
        # Use a music-themed activity
        activity = discord.Activity(
            type=discord.ActivityType.listening, 
            name="the vibe"
        )
        
        super().__init__(
            command_prefix=commands.when_mentioned,
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
            
            # Register event listeners after connection is established
            if self.get_cog('MusicCog'):
                # Note: Event listeners are handled differently in newer Wavelink versions
                # We'll handle track events through the player directly
            
            logger.info(f'🎵 Wavelink node connected: {node.identifier}')
            print(f'🎵 Wavelink node connected: {node.identifier}')
            
        except Exception as e:
            logger.error(f'❌ Failed to connect to Lavalink: {e}', exc_info=True)
            print(f'❌ Failed to connect to Lavalink: {e}')
    
    async def setup_hook(self):
        """Called when setting up the bot, before on_ready."""
        # Register the event listeners after cogs are loaded
        await super().setup_hook()

# --- VIEW/BUTTONS CLASS ---

class MusicControls(ui.View):
    """A persistent view for the music controller with buttons."""
    
    def __init__(self, bot):
        super().__init__(timeout=None) # Set timeout to None for persistent view
        self.bot = bot
        
    async def get_player(self, interaction: discord.Interaction) -> RenifyPlayer | None:
        """Helper to get the player and perform basic checks."""
        player: RenifyPlayer = interaction.guild.voice_client
        
        if not player or not player.is_connected():
            await interaction.response.send_message("❌ The bot is not currently playing or connected.", ephemeral=True)
            return None
        
        if interaction.user.voice and player.channel != interaction.user.voice.channel:
             await interaction.response.send_message("❌ You must be in the same voice channel to control the music.", ephemeral=True)
             return None

        return player

    @ui.button(label="Pause", style=discord.ButtonStyle.secondary, custom_id="persistent:pause_btn", emoji="⏸️")
    async def pause_button(self, interaction: discord.Interaction, button: ui.Button):
        player = await self.get_player(interaction)
        if not player: return
        
        if player.paused:
            await player.pause(False)
            button.label = "Pause"
            button.emoji = "⏸️"
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("▶️ Resumed!", ephemeral=True)
        else:
            await player.pause(True)
            button.label = "Resume"
            button.emoji = "▶️"
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("⏸️ Paused!", ephemeral=True)

    @ui.button(label="Skip", style=discord.ButtonStyle.primary, custom_id="persistent:skip_btn", emoji="⏭️")
    async def skip_button(self, interaction: discord.Interaction, button: ui.Button):
        player = await self.get_player(interaction)
        if not player: return
        
        await player.stop()
        await interaction.response.send_message("⏭️ Skipped! Next track coming up...", ephemeral=True)

    @ui.button(label="Stop", style=discord.ButtonStyle.danger, custom_id="persistent:stop_btn", emoji="⏹️")
    async def stop_button(self, interaction: discord.Interaction, button: ui.Button):
        player = await self.get_player(interaction)
        if not player: return
        
        player.queue.clear()
        await player.disconnect()
        await interaction.response.send_message("⏹️ Music stopped and controller cleared.", ephemeral=True)
        
# --- COMMANDS (Updated) ---

@commands.guild_only() 
class MusicCog(commands.Cog):
    
    def __init__(self, bot: RenifyBot):
        self.bot = bot
        # Add the persistent view to the bot
        self.bot.add_view(MusicControls(self.bot))
    

    async def get_player(self, ctx: discord.Interaction) -> RenifyPlayer | None:
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
        
        player: RenifyPlayer = ctx.guild.voice_client

        if not player:
            player = await voice_channel.connect(cls=RenifyPlayer)
            player.home_channel = ctx.channel 
            
        elif player.channel != voice_channel:
            await ctx.response.send_message(f"❌ I'm already playing music in {player.channel.mention}!", ephemeral=True)
            return None
            
        return player
    
    # --- Controller Logic ---
    
    def create_controller_embed(self, player: RenifyPlayer, track: wavelink.abc.Playable) -> discord.Embed:
        """Creates the dynamic 'Now Playing' embed."""
        embed = discord.Embed(
            title="🎧 Now Playing | Renify Controller",
            description=f"**[{track.title}]({track.uri})** by `{track.author}`",
            color=0x1DB954 # Spotify Green
        )
        embed.add_field(name="Queue Size", value=f"{len(player.queue)} tracks", inline=True)
        # You'd need to calculate a progress bar here, which is more complex.
        # For simplicity, we omit the progress bar for now.
        embed.set_thumbnail(url=track.thumbnail if hasattr(track, 'thumbnail') else None)
        embed.set_footer(text=f"Requested by: {player.home_channel.guild.me.display_name}")
        return embed

    async def update_controller_message(self, player: RenifyPlayer, track: wavelink.abc.Playable = None):
        """Updates the interactive message with the current track info."""
        if not player.controller_message:
            return

        track = track or player.current
        
        if track:
            embed = self.create_controller_embed(player, track)
            try:
                # The view needs to be reset to ensure button states are correct
                view = MusicControls(self.bot)
                await player.controller_message.edit(embed=embed, view=view)
            except discord.NotFound:
                player.controller_message = None # Message was deleted, reset

    @app_commands.command(name="controller", description="Sends or updates the interactive music controller panel.")
    async def controller_command(self, interaction: discord.Interaction):
        player = interaction.guild.voice_client
        if not player:
            return await interaction.response.send_message("🎶 Nothing is playing, use `/play` first!", ephemeral=True)

        # Delete old controller message if it exists
        if player.controller_message:
            try:
                await player.controller_message.delete()
            except:
                pass # Ignore if already deleted

        # Send the new controller message
        current_track = player.current
        embed = self.create_controller_embed(player, current_track)
        
        # Send the message with the persistent view
        await interaction.response.send_message(embed=embed, view=MusicControls(self.bot))
        
        # Store the message object for later updates
        player.controller_message = await interaction.original_response()
        
    # --- Wavelink Events (Modified) ---

    # async def on_wavelink_track_start(self, event: wavelink.TrackStart):
        """Event handler for when a track starts playing."""
        player: RenifyPlayer = event.player
        track = event.track
        
        # Call the update logic to refresh the controller message
        await self.update_controller_message(player, track)

    # async def on_wavelink_track_end(self, event: wavelink.TrackEndEvent):
    #     """Event handler for when a track finishes."""
    #     pass

    # --- Slash Commands (Modified /play) ---
    
    @discord.app_commands.command(name="play", description="Search for a song/playlist or paste a URL to play.")
    @discord.app_commands.describe(query="The song title, artist, or URL (Spotify/Apple Music/Deezer/SoundCloud link).")
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
        
        await interaction.response.defer() 

        player = await self.get_player(interaction)
        if not player: return
        
        # Log command usage
        logger.info(f"User {interaction.user.name} ({interaction.user.id}) requested /play with query: {query[:100]}")

        try:
            # Search for tracks using Wavelink's search function
            # Wavelink handles multi-source searching for us (if Lavalink plugins are installed)
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
            if queue_limit is not None:
                if len(tracks.tracks) + current_queue_size > queue_limit:
                    tier_emoji = {"FREE": "🆓", "PREMIUM": "⭐", "DIAMOND": "💎"}.get(user_tier, "")
                    await interaction.followup.send(
                        f"❌ {tier_emoji} Your {user_tier} tier allows {queue_limit} tracks. "
                        f"Adding this playlist ({len(tracks.tracks)} tracks) would exceed the limit. "
                        f"Upgrade to increase your limit!",
                        ephemeral=True
                    )
                    return
        
        # Handle single tracks or the first track of a playlist
        track = tracks[0] if not isinstance(tracks, wavelink.Playlist) else tracks.tracks[0]

        if player.is_playing() or player.paused:
            # Check queue limit before adding
            if queue_limit is not None and len(player.queue) >= queue_limit:
                tier_emoji = {"FREE": "🆓", "PREMIUM": "⭐", "DIAMOND": "💎"}.get(user_tier, "")
                await interaction.followup.send(
                    f"❌ {tier_emoji} Queue is full (max {queue_limit} tracks for {user_tier} tier). "
                    f"Upgrade for a higher limit!",
                    ephemeral=True
                )
                return
            
            tier_emoji = {"FREE": "🆓", "PREMIUM": "⭐", "DIAMOND": "💎"}.get(user_tier, "")
            
            # Add to queue
            if isinstance(tracks, wavelink.Playlist):
                player.queue.extend(tracks.tracks)
                response_text = f"{tier_emoji} 🎶 Loaded **{len(tracks.tracks)}** tracks from playlist **[{tracks.name[:50]}]({query[:100]})**. ({current_queue_size}/{queue_limit if queue_limit else '∞'} in queue)"
            else:
                player.queue.put(track)
                response_text = f"{tier_emoji} 🎧 Queued **[{track.title[:50]}]({track.uri})** by `{track.author}`. ({current_queue_size}/{queue_limit if queue_limit else '∞'} in queue)"
            
            await interaction.followup.send(response_text)
            logger.info(f"Added track(s) to queue for {user_tier} tier user")
            
            # Update the existing controller message to show the new queue size
            await self.update_controller_message(player)
            
        else:
            # Start playing immediately
            tier_emoji = {"FREE": "🆓", "PREMIUM": "⭐", "DIAMOND": "💎"}.get(user_tier, "")
            
            if isinstance(tracks, wavelink.Playlist):
                player.queue.extend(tracks.tracks[1:]) # Queue the rest after the first track
                remaining = len(tracks.tracks) - 1
                response_text = f"{tier_emoji} 🎶 Found it! Playing **[{track.title[:50]}]({track.uri})** and queued {remaining} more tracks from the playlist. ({remaining}/{queue_limit if queue_limit else '∞'} in queue)"
            else:
                response_text = f"{tier_emoji} 🎶 Found it! Playing **[{track.title[:50]}]({track.uri})** now."

            await player.play(track)
            await interaction.followup.send(response_text)
            logger.info(f"Playing track: {track.title}")
            
            # Auto-send the controller message after starting play, if one doesn't exist
            if not player.controller_message:
                 await self.controller_command(interaction)

    @discord.app_commands.command(name="sync", description="Sync slash commands with Discord (Admin only).")
    @discord.app_commands.default_permissions(administrator=True)
    async def sync_commands(self, interaction: discord.Interaction):
        """Sync slash commands with Discord."""
        try:
            synced = await self.bot.tree.sync()
            await interaction.response.send_message(
                f"✅ Successfully synced {len(synced)} slash commands!", 
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to sync commands: {str(e)}", 
                ephemeral=True
            )

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

**🎮 Interactive Controller:**
`/controller` - Get an interactive control panel with buttons

**⚙️ Control Commands:**
Buttons on controller handle pause/skip/stop
(Requires appropriate permissions)

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
3. Use `/controller` for interactive buttons
4. Queue up to 500 songs (your free tier limit)
5. Enjoy! The bot will auto-disconnect when queue ends
        """
        embed.add_field(name="🚀 Quick Start", value=quick_start, inline=False)
        
        # Tips
        tips = """
• You can search for songs by name or paste YouTube URLs
• Add playlists with `/play <playlist url>`
• Queue fills up! Check `/queue` to see what's next
• Use `/controller` for a nice button interface
• Bot needs to be in your voice channel to work
        """
        embed.add_field(name="💡 Tips & Tricks", value=tips, inline=False)
        
        embed.set_footer(text="Renify Bot v1.0 | Made with ❤️ for music lovers")
        
        await interaction.response.send_message(embed=embed)


# --- BOT RUNNING (Keep the same) ---
async def main():
    """Main function to run the bot."""
    bot = RenifyBot()
    # Add the music commands cog
    await bot.add_cog(MusicCog(bot))
    
    # ... (Run logic) ...
    # Be sure to enable the Message Content Intent in the Discord Developer Portal 
    # for the conversational (FlaviBot-like prefix/mention) commands later.
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