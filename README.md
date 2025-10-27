# Renify Music Bot 🎵

A Discord music bot built with Discord.py and Wavelink.

## Features

- Play music from YouTube
- Queue management
- Pause/Resume controls
- Skip tracks
- Auto-disconnect when queue ends

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Lavalink Server

You need to run a Lavalink server. Download it from: https://github.com/lavalink-devs/lavalink/releases

Create an `application.yml` file in the same directory as the Lavalink JAR:

```yaml
server:
  port: 2333
  address: 127.0.0.1
  
lavalink:
  server:
    password: "youshallnotpass"
    sources:
      youtube: true
```

Run the Lavalink server:
```bash
java -jar Lavalink.jar
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and add your Discord bot token:

```bash
copy .env.example .env
```

Then edit `.env` and add your Discord bot token.

### 4. Run the Bot

```bash
python renify_core.py
```

## Commands

- `/play <query>` - Play a song or add to queue
- `/skip` - Skip current track
- `/pause` - Pause the music
- `/resume` - Resume paused music
- `/stop` - Stop music and clear queue
- `/queue` - Show current queue

## Notes

- Make sure your Discord bot has the necessary permissions to join voice channels
- Enable "Server Members Intent" in the Discord Developer Portal
- The bot requires a running Lavalink server to function

