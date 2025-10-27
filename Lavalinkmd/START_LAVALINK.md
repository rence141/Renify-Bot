# Starting Your Renify Music Bot

## Current Status
- ✅ Bot code is ready (`renify_core.py` and `renify_controller.py`)
- ✅ Lavalink.jar is downloaded
- ✅ Configuration is ready
- ✅ Java is installed

## Step-by-Step Instructions

### Step 1: Install Java 17 or Higher

**Quick Installation:**
1. Download: https://www.azul.com/downloads/?package=jdk#zulu
2. Click "Windows x64 .msi" under "Zulu Community (Free)"
3. Install the downloaded file
4. **IMPORTANT:** Restart your terminal/PowerShell after installation

**Verify Installation:**
Open a new PowerShell and run:
```powershell
java -version
```
Should show: `openjdk version "17.x.x"` or higher

### Step 2: Start Lavalink Server

Since you're already in the right directory, just run:
```powershell
java -jar Lavalink.jar
```

You should see:
```
[main] INFO lavalink.server.io.SocketContext - Socket server listening on 0.0.0.0:2333
[main] INFO lavalink.server.LavalinkServer - Lavalink server started.
```

**⚠️ Keep this terminal open!** Lavalink needs to keep running.

### Step 3: Run Your Bot (in a NEW terminal)

Open a **new PowerShell window** and run:

```powershell
cd C:\xampp\htdocs\Renify_Bot

# Install dependencies
pip install -r requirements.txt

# Set your Discord bot token
$env:DISCORD_TOKEN="YOUR_BOT_TOKEN_HERE"

# Run the bot
python renify_core.py
```

### Your Bot Configuration
- **Host:** localhost
- **Port:** 2333
- **Password:** renifythoushallnotpass

## Available Bot Commands
- `/play <song name>` - Play music
- `/skip` - Skip current track
- `/pause` - Pause music
- `/resume` - Resume music
- `/stop` - Stop and disconnect
- `/queue` - Show queue
- `/controller` - Interactive controls (in renify_controller.py)

