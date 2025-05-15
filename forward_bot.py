#!/usr/bin/env python3
import os
import sys
import json
import asyncio
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, UsernameNotOccupiedError

# ───────────────────────────────────────────────────────────────────────────────
# 1) Validate required environment variables up front
required = ["API_ID", "API_HASH", "BOT_TOKEN", "CHANNEL_MAPPING"]
missing = [k for k in required if k not in os.environ]
if missing:
    print("❌ Missing env vars:", missing, file=sys.stdout)
    sys.exit(1)

# 2) Parse simple scalar vars
try:
    API_ID = int(os.environ["API_ID"])
except ValueError:
    print("❌ API_ID must be an integer.", file=sys.stdout)
    sys.exit(1)

API_HASH  = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

# 3) Parse JSON-encoded channel mapping
raw_map = os.environ["CHANNEL_MAPPING"]
try:
    mapping = json.loads(raw_map)
except json.JSONDecodeError as e:
    print("❌ CHANNEL_MAPPING is not valid JSON:", e, file=sys.stdout)
    sys.exit(1)

# 4) Convert mapping keys/values to ints when possible
CHANNEL_MAPPING = {}
for src, dst in mapping.items():
    try:
        src_key = int(src)
    except:
        src_key = src
    try:
        dst_val = int(dst)
    except:
        dst_val = dst
    CHANNEL_MAPPING[src_key] = dst_val

SESSION = "forwarder_session"  # Telethon will persist here

# ───────────────────────────────────────────────────────────────────────────────

async def main():
    # Initialize client and login with bot token (no interactive prompt)
    client = TelegramClient(SESSION, API_ID, API_HASH)
    print("🔑 Logging in with bot token…")
    await client.start(bot_token=BOT_TOKEN)
    print("✅ Bot authorized, session file:", SESSION)

    # 1) Back-fill history
    for src, dst in CHANNEL_MAPPING.items():
        print(f"⏳ Back-filling {src} → {dst} …")
        try:
            src_ent = await client.get_input_entity(src)
            dst_ent = await client.get_input_entity(dst)
        except Exception as e:
            print(f"⚠ Could not resolve {src} or {dst}: {e}")
            continue

        async for msg in client.iter_messages(src_ent, limit=None, reverse=True):
            if msg.video or msg.document:
                try:
                    await client.forward_messages(dst_ent, msg)
                except FloodWaitError as e:
                    print(f"  ⏱ FloodWait {e.seconds}s, sleeping…")
                    await asyncio.sleep(e.seconds)
                    await client.forward_messages(dst_ent, msg)
                await asyncio.sleep(0.3)

    # 2) Live-forward new files
    @client.on(events.NewMessage(chats=list(CHANNEL_MAPPING.keys())))
    async def handler(event):
        m = event.message
        if m.video or m.document:
            # resolve dst by numeric ID or username
            dst = (CHANNEL_MAPPING.get(event.chat.id) or
                   CHANNEL_MAPPING.get(event.chat.username))
            if not dst:
                return
            try:
                await client.forward_messages(dst, m)
            except FloodWaitError as e:
                print(f"  ⏱ FloodWait (live) {e.seconds}s, sleeping…")
                await asyncio.sleep(e.seconds)
                await client.forward_messages(dst, m)

    print("▶️  Forwarder is up and running.")
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print("❌ Fatal error:", e, file=sys.stdout)
        import traceback; traceback.print_exc()
        sys.exit(1)
