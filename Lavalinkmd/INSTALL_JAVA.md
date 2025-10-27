# How to Install Java for Lavalink

## Quick Install Guide

### Option 1: Using Chocolatey (Recommended if you have it)
```powershell
choco install zulu17 -y
```

### Option 2: Manual Download

1. **Download Java 17:**
   - Visit: https://www.azul.com/downloads/?package=jdk#zulu
   - Click "Download" for Zulu Community (Windows x64)
   - The file will be something like: `zulu17.50.xx-windows_x64.zip` or `.msi`

2. **Install:**
   - If you downloaded `.zip`:
     - Extract it to `C:\Program Files\Zulu`
     - Add `C:\Program Files\Zulu\zulu17.xx\bin` to your PATH
   - If you downloaded `.msi`:
     - Double-click and follow the installer
     - Make sure to check "Add to PATH" during installation

3. **Verify Installation:**
   ```powershell
   java -version
   ```
   Should show: `openjdk version "17.x.x"` or higher

4. **Restart Terminal:**
   After installing, close and reopen your PowerShell terminal

## After Java is Installed

Start Lavalink:
```powershell
cd renify_lavalink
java -jar Lavalink.jar
```

You should see:
```
[main] INFO lavalink.server.io.SocketContext - Socket server listening on 0.0.0.0:2333
[main] INFO lavalink.server.LavalinkServer - Lavalink server started.
```

**Keep this terminal open!** Lavalink needs to keep running.

Then in a **NEW terminal**, run your bot:
```powershell
cd C:\xampp\htdocs\Renify_Bot
pip install -r requirements.txt
python renify_core.py
```

