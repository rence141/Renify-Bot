# Lavalink Setup Instructions for Renify Bot

## Current Status
✅ Lavalink.jar is downloaded  
⚠️ Java 17+ is NOT installed  
✅ Configuration file is ready  

## Steps to Complete Setup

### 1. Install Java
You need Java 17 or higher to run Lavalink.

**Download Java:**
- Visit: https://www.azul.com/downloads/?package=jdk#zulu
- Download and install Zulu OpenJDK (Java 17 or higher)
- During installation, make sure to add Java to your PATH

**Verify Installation:**
```powershell
java -version
```
You should see something like: `openjdk version "17.x.x"` or higher

### 2. Start Lavalink Server
Once Java is installed, run this command from the `renify_lavalink` directory:

```powershell
java -jar renify_lavalink\Lavalink.jar
```

You should see output like:
```
[main] INFO lavalink.server.io.SocketContext - Socket server listening on 0.0.0.0:2333
[main] INFO lavalink.server.LavalinkServer - Lavalink server started.
```

**Keep this terminal open!** Lavalink needs to keep running.

### 3. Update Bot Token
Set your Discord bot token in the environment or create a `.env` file:

**Option A: Environment Variable**
```powershell
$env:DISCORD_TOKEN="YOUR_BOT_TOKEN_HERE"
```

**Option B: Create .env file** (install python-dotenv first):
```powershell
pip install python-dotenv
```

Then create `.env` file with:
```
DISCORD_TOKEN=YOUR_BOT_TOKEN_HERE
LAVALINK_HOST=localhost
LAVALINK_PORT=2333
LAVALINK_PASSWORD=youshallnotpass
```

### 4. Run Your Bot
```powershell
python renify_core.py
```

Or if you want to use the controller version:
```powershell
python renify_controller.py
```

## Configuration Summary

### Lavalink Configuration (`renify_lavalink/application.yml`)
- Port: 2333
- Password: youshallnotpass
- Sources: YouTube, Bandcamp, Soundcloud, Twitch, Vimeo

### Bot Configuration
- Host: localhost
- Port: 2333  
- Password: youshallnotpass

## Troubleshooting

**If Lavalink won't start:**
- Make sure Java 17+ is installed: `java -version`
- Check if port 2333 is already in use
- Make sure `application.yml` is in the same directory as `Lavalink.jar`

**If bot can't connect:**
- Make sure Lavalink server is running
- Check that password matches: "youshallnotpass"
- Verify the bot has internet connection

**Need to run Lavalink in the background?**
- Use Task Manager
- Or create a batch file: `start-lavalink.bat`:
```batch
@echo off
cd renify_lavalink
java -jar Lavalink.jar
pause
```

