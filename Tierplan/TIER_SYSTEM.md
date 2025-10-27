# 💎 Renify Bot Tier System

## Overview
Your Renify bot now supports a 3-tier subscription system with different queue limits.

## Tiers

### 🆓 FREE Tier
- **Queue Limit:** 500 tracks
- **Price:** Free
- **Features:**
  - Full music playback
  - Queue up to 500 songs
  - All basic commands

### ⭐ PREMIUM Tier
- **Queue Limit:** 5,000 tracks
- **Price:** Custom (implement your pricing)
- **Features:**
  - 10x more queue space (5,000 tracks)
  - Priority support
  - All Free tier features

### 💎 DIAMOND Tier
- **Queue Limit:** Unlimited
- **Price:** Custom (implement your pricing)
- **Features:**
  - Unlimited queue
  - Highest priority support
  - Early access to new features
  - All Premium tier features

---

## Current Implementation

### Location in Code
The tier system is defined in:
- `renify_core.py` (lines 32-46)
- `renify_controller.py` (lines 30-45)

### Current Behavior
```python
def get_user_tier(user_id: int) -> str:
    """Get user's tier. For now, default to FREE."""
    return 'FREE'  # TODO: Implement your payment/subscription system
```

**By default, all users are on the FREE tier (500 track limit).**

---

## How to Implement Payment System

You need to implement the `get_user_tier()` function to check user subscriptions. Here are some options:

### Option 1: Simple In-Memory Dictionary
```python
# Add this near the top of your file
user_tiers = {
    123456789012345678: 'PREMIUM',  # Example user ID
    987654321098765432: 'DIAMOND',   # Another user ID
}

def get_user_tier(user_id: int) -> str:
    """Get user's tier from dictionary."""
    return user_tiers.get(user_id, 'FREE')
```

### Option 2: Database (Recommended for production)
```python
import sqlite3

def get_user_tier(user_id: int) -> str:
    """Get user's tier from database."""
    conn = sqlite3.connect('renify_users.db')
    c = conn.cursor()
    
    c.execute("SELECT tier FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    
    return result[0] if result else 'FREE'
```

### Option 3: Payment API Integration
```python
import requests

def get_user_tier(user_id: int) -> str:
    """Get user's tier from your payment API."""
    try:
        response = requests.get(
            f'https://your-payment-api.com/api/users/{user_id}/tier',
            headers={'Authorization': f'Bearer {YOUR_API_KEY}'}
        )
        if response.status_code == 200:
            return response.json()['tier']
    except:
        pass
    return 'FREE'
```

### Option 4: Discord Role-Based (Simple)
```python
async def get_user_tier_async(interaction: discord.Interaction) -> str:
    """Get user's tier from Discord roles."""
    user = interaction.user
    
    if any(role.name == 'Diamond Subscriber' for role in user.roles):
        return 'DIAMOND'
    elif any(role.name == 'Premium Subscriber' for role in user.roles):
        return 'PREMIUM'
    else:
        return 'FREE'

# Then use in play_command:
user_tier = await get_user_tier_async(interaction)
```

---

## Updating Tier Limits

To change the limits, edit the `TIER_LIMITS` dictionary:

```python
TIER_LIMITS = {
    'FREE': 1000,      # Increased to 1000
    'PREMIUM': 10000,  # Increased to 10,000
    'DIAMOND': None    # Still unlimited
}
```

---

## User-Facing Messages

The bot automatically displays:
- Tier emoji in messages (🆓 FREE, ⭐ PREMIUM, 💎 DIAMOND)
- Current queue size vs limit (e.g., "250/500" or "∞")
- Upgrade prompts when limits are reached

Example messages:
- `🆓 🎶 Loaded 50 tracks from playlist. (250/500 in queue)`
- `❌ 🆓 Queue is full (max 500 tracks for FREE tier). Upgrade for a higher limit!`

---

## Testing Different Tiers

To test different tiers during development, temporarily modify the function:

```python
def get_user_tier(user_id: int) -> str:
    """Get user's tier for testing."""
    # Test user IDs
    if user_id == YOUR_DISCORD_ID:
        return 'DIAMOND'  # You get Diamond tier
    elif user_id == 123456789:  # Test user
        return 'PREMIUM'
    else:
        return 'FREE'
```

Replace `YOUR_DISCORD_ID` with your actual Discord user ID.

---

## Next Steps

1. ✅ Tier system is implemented
2. ✅ Queue limits are enforced
3. ⚠️ Implement your payment/subscription logic in `get_user_tier()`
4. ⚠️ Create a database or API to store user tiers
5. ⚠️ Add a command to check tier: `/mytier`
6. ⚠️ Add upgrade command: `/upgrade`

---

## Adding Tier Check Command

Here's a simple command you can add:

```python
@discord.app_commands.command(name="mytier", description="Check your current subscription tier.")
async def my_tier_command(self, interaction: discord.Interaction):
    """Shows user's current tier and limits."""
    tier = get_user_tier(interaction.user.id)
    queue_limit = get_queue_limit(tier)
    
    emoji = {"FREE": "🆓", "PREMIUM": "⭐", "DIAMOND": "💎"}.get(tier, "❓")
    limit_text = f"{queue_limit:,} tracks" if queue_limit else "Unlimited tracks"
    
    embed = discord.Embed(
        title=f"{emoji} Your Subscription Tier",
        description=f"**Tier:** {tier}\n**Queue Limit:** {limit_text}",
        color=0x1DB954 if tier == 'DIAMOND' else 0xFFD700 if tier == 'PREMIUM' else 0x808080
    )
    
    await interaction.response.send_message(embed=embed)
```

