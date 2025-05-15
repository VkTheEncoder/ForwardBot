#!/usr/bin/env python3
import os
import asyncio
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, UsernameNotOccupiedError

# ── CONFIG ──
API_ID   = int(os.environ['API_ID'])
API_HASH = os.environ['API_HASH']
BOT_TOKEN = os.environ['BOT_TOKEN']    # required
SESSION  = 'forwarder_session'         # this file will be auto-created
# Pass your mapping as a JSON-encoded env var, e.g.
#   CHANNEL_MAPPING='{"-1002025087044":"-1002539731328"}'
import json
_mapping = json.loads(os.environ['CHANNEL_MAPPING'])
CHANNEL_MAPPING = {
    int(src) if src.startswith("-") else src:
    int(dst) if dst.startswith("-") else dst
    for src, dst in _mapping.items()
}
# ── END CONFIG ──

async def main():
    client = TelegramClient(SESSION, API_ID, API_HASH)

    # Bot-only start (won’t prompt for phone/code)
    print("🔑 Logging in with bot token…")
    await client.start(bot_token=BOT_TOKEN)
    print("✅ Logged in, session file:", SESSION)

    # Back-fill history
    for src, dst in CHANNEL_MAPPING.items():
        try:
            src_ent = await client.get_input_entity(src)
            dst_ent = await client.get_input_entity(dst)
        except Exception as e:
            print(f"⚠ Could not resolve {src} → {dst}: {e}")
            continue

        print(f"⏳ Back-filling {src} → {dst} …")
        async for msg in client.iter_messages(src_ent, limit=None, reverse=True):
            if msg.video or msg.document:
                try:
                    await client.forward_messages(dst_ent, msg)
                except FloodWaitError as e:
                    print(f"  ⏱ FloodWait {e.seconds}s, sleeping…")
                    await asyncio.sleep(e.seconds)
                    await client.forward_messages(dst_ent, msg)
                await asyncio.sleep(0.3)

    # Live watcher
    @client.on(events.NewMessage(chats=list(CHANNEL_MAPPING.keys())))
    async def handler(evt):
        m = evt.message
        if m.video or m.document:
            dst = CHANNEL_MAPPING.get(evt.chat.id) or CHANNEL_MAPPING.get(evt.chat.username)
            if not dst:
                return
            try:
                await client.forward_messages(dst, m)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
                await client.forward_messages(dst, m)

    print("▶️  Forwarder is up and running.")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
