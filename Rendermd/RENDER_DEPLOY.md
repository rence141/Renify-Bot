# 🚀 Deploying Renify Bot to Render

## Option 1: Single Container (Recommended for Render)

This runs both Lavalink and the bot in one container using Supervisor.

### Setup:

1. **Fork your repository to GitHub**
2. **Go to Render Dashboard**: https://dashboard.render.com
3. **Click "New +" → "Web Service"**
4. **Configure**:
   - **Name**: `renify-bot`
   - **Repository**: Connect your GitHub repo
   - **Branch**: `main` (or `master`)
   - **Root Directory**: Leave empty
   - **Build Command**: Leave empty (uses Dockerfile)
   - **Start Command**: Leave empty
   - **Dockerfile**: `Dockerfile.single`
   - **Region**: Choose closest to you
   - **Plan**: Free (or upgrade if needed)

5. **Environment Variables**:
   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   LAVALINK_HOST=localhost
   LAVALINK_PORT=2333
   LAVALINK_PASSWORD=renifythoushallnotpass
   ```

6. **Click "Create Web Service"**

---

## Option 2: Separate Services (More Scalable)

Deploy Lavalink and Bot as separate services.

### Deploy Lavalink:

1. **New + → "Web Service"**
2. **Configure**:
   - **Name**: `renify-lavalink`
   - **Dockerfile**: `Dockerfile`
   - **Environment**: Set Lavalink password
3. **Create**

### Deploy Bot:

1. **New + → "Background Worker"**
2. **Configure**:
   - **Name**: `renify-bot`
   - **Dockerfile**: `Dockerfile.bot`
   - **Environment**: Set DISCORD_TOKEN
   - Connect to Lavalink service
3. **Create**

---

## Environment Variables

Add these in Render Dashboard under your service's "Environment" tab:

### Required:
```bash
DISCORD_TOKEN=your_discord_bot_token_here
```

### Optional (defaults provided):
```bash
LAVALINK_HOST=localhost  # For single container
LAVALINK_PORT=2333
LAVALINK_PASSWORD=renifythoushallnotpass
```

---

## Files Structure

Your repository should have:
```
Renify_Bot/
├── Dockerfile.single      # For single container deployment
├── Dockerfile             # For Lavalink only
├── Dockerfile.bot         # For bot only
├── renify_core.py        # Bot code
├── requirements.txt       # Python dependencies
├── renify_lavalink/
│   └── application.yml   # Lavalink config
└── .dockerignore
```

---

## Free Tier Limits on Render

- **Web Services**: 1 per account
- **RAM**: 512MB
- **CPU**: Shared
- **Sleep**: Services sleep after 15 minutes of inactivity
- **Wake Time**: 30-60 seconds

**Note**: The free tier may not be ideal for music bots due to sleep times.

---

## Upgrade Considerations

For better performance on Render, consider upgrading to the **Starter Plan** ($7/month):
- ✅ No sleep
- ✅ 512MB RAM (enough for both services)
- ✅ Better CPU priority
- ✅ Custom domains

---

## Health Checks

Render will automatically check:
- Lavalink responds on port 2333
- Bot process stays running

If health checks fail, check the logs in Render dashboard.

---

## Monitoring

View logs in Render dashboard:
1. Go to your service
2. Click "Logs" tab
3. See real-time output from both services

---

## Troubleshooting

### Bot won't connect to Lavalink
- Check `LAVALINK_HOST` is `localhost` (single container) or service URL (separate)
- Verify `LAVALINK_PASSWORD` matches in both services

### Service keeps restarting
- Check logs for errors
- Verify DISCORD_TOKEN is set
- Check environment variables

### Music doesn't play
- Wait 30-60 seconds for service to fully start
- Check if Lavalink is healthy in logs
- Verify bot is connected (should see "Wavelink node connected")

---

## Quick Start Commands

Once deployed, your bot will be live at:
```
Your Discord server: /play song name
```

Test commands:
- `/play Never Gonna Give You Up Rick Astley`
- `/queue`
- `/skip` (requires permissions)

---

## Cost Estimate

### Free Tier:
- **Cost**: $0/month
- **Drawbacks**: Sleeps after inactivity, slower startup

### Starter Plan:
- **Cost**: $7/month per service
- **Includes**: No sleep, better performance
- **Recommended**: For serious use

### Pro Plan:
- **Cost**: $25/month
- **Includes**: More RAM, dedicated CPU
- **For**: High-traffic servers

---

## Alternative: Railway or Fly.io

Both offer better free tier options:
- **Railway**: $5 free credit/month, no sleep
- **Fly.io**: Generous free tier, no sleep

Consider migrating if Render's limitations are too restrictive.

---

## Security Notes

- Never commit `DISCORD_TOKEN` to Git
- Use Render's environment variables
- Keep Lavalink password secure
- Enable 2FA on Discord developer account

