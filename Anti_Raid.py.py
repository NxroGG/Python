# anti_raid_bot.py (professional embed version)
import os
import asyncio
from collections import defaultdict, deque
from datetime import timedelta
import discord
from discord import Intents, Embed, Colour

# ---------- CONFIG ----------
TOKEN = "MTQzNDkxMDk5MTEzNjg1MDAzMA.GxBIPI.xZukvE7gpReIWl3VaDoy5mmcvh2CvPf7vmyoJU"  # placeholder token for testing
MOD_CHANNEL_ID = 1434909740567363661     # warning / log channel
MOD_ROLE_ID = 1434909741976653865        # moderator role
EXCLUDED_CHANNELS = {1434909741666009157, 1409312086844112961}  # ignored channels
REQUIRED_DUPES = 5            # same message count to trigger
TIMEOUT_MINUTES = 10          # timeout duration
WINDOW_SECONDS = 60           # message tracking window
# ----------------------------

intents = Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.messages = True

bot = discord.Client(intents=intents)
recent_messages = defaultdict(lambda: deque())
lock = asyncio.Lock()

def normalize_content(content: str) -> str:
    """Simplify message text to detect duplicates."""
    if not content:
        return ""
    return " ".join(content.strip().lower().split())

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} ({bot.user.id})")
    print("Anti-raid bot is online and ready (professional embed version)!")

@bot.event
async def on_message(message: discord.Message):
    # skip bots, DMs, excluded channels
    if (
        message.author.bot
        or message.guild is None
        or message.channel.id in EXCLUDED_CHANNELS
    ):
        return

    # skip staff (optional)
    if getattr(message.author.guild_permissions, "manage_messages", False):
        return

    key = (message.guild.id, message.author.id, normalize_content(message.content))
    now = discord.utils.utcnow()

    async with lock:
        dq = recent_messages[key]
        dq.append((message, now))

        # remove messages older than window
        while dq and (now - dq[0][1]).total_seconds() > WINDOW_SECONDS:
            dq.popleft()

        if len(dq) >= REQUIRED_DUPES:
            to_delete = list(dq)[-REQUIRED_DUPES:]
            dq.clear()

            deleted_count = 0
            for msg_obj, _ in to_delete:
                try:
                    await msg_obj.delete(reason="Anti-raid: repeated message spam")
                    deleted_count += 1
                except Exception:
                    pass

            timed_out = False
            try:
                until = discord.utils.utcnow() + timedelta(minutes=TIMEOUT_MINUTES)
                await message.author.edit(timeout=until, reason="Anti-raid: repeated message spam")
                timed_out = True
            except Exception:
                timed_out = False

            # Professional embed (no emojis, clean style)
            embed = discord.Embed(
                title="Anti-Spam Report",
                description=(
                    f"**User:** <@{message.author.id}> (`{message.author.id}`)\n\n"
                    "This incident was automatically handled by the Anti-Raid System."
                ),
                colour=discord.Colour.dark_red(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
            embed.set_footer(text="Anti-Raid System")

            try:
                mod_channel = bot.get_channel(MOD_CHANNEL_ID) or await bot.fetch_channel(MOD_CHANNEL_ID)
                await mod_channel.send(f"<@&{MOD_ROLE_ID}>", embed=embed)
            except Exception as e:
                print(f"⚠️ Couldn’t send embed log: {e}")

            print(f"[Anti-Raid] {message.author} | Timeout={timed_out} | Deleted={deleted_count}")

@bot.event
async def on_guild_remove(guild):
    for k in [k for k in recent_messages if k[0] == guild.id]:
        recent_messages.pop(k, None)

if __name__ == "__main__":
    bot.run(TOKEN)
