import asyncio
from telethon import TelegramClient, events

# —— CONFIGURATION —— #
API_ID   = 25341849                   # replace with your api_id
API_HASH = 'c22013816f700253000e3c24a64db3b6'  # replace with your api_hash
SESSION  = 'forwarder_session'       # name for the .session file

# Map “source_channel” → “destination_channel”
# You can use channel usernames ('@sourcechan') or numeric IDs (e.g. -1001234567890)
CHANNEL_MAPPING = {
    -1002025087044: -1002539731328,
}

# —— END CONFIG —— #

async def main():
    client = TelegramClient(SESSION, API_ID, API_HASH)
    # If you're logging in as a user, this will prompt for code.
    # If you're using a bot token, do client.start(bot_token='…')
    await client.start(bot_token="7070027599:AAHJ3zf_UZghJxf32n3bB2UMMb3-_NiC0II")


    # 1) Forward **historical** messages first (oldest → newest)
    for src, dst in CHANNEL_MAPPING.items():
        print(f"Fetching history from {src} → forwarding to {dst}…")
        async for msg in client.iter_messages(src, limit=None, reverse=True):
            if msg.video or msg.document:
                await client.forward_messages(dst, msg)
                # polite pause to avoid hitting flood limits
                await asyncio.sleep(0.3)

    # 2) Now watch for **new** messages in each source channel
    @client.on(events.NewMessage(chats=list(CHANNEL_MAPPING.keys())))
    async def _(event):
        msg = event.message
        src = event.chat.username or event.chat.id
        dst = CHANNEL_MAPPING.get(src)
        if not dst:
            return
        if msg.video or msg.document:
            await client.forward_messages(dst, msg)

    print("✅ Forwarder is now running. Press Ctrl+C to stop.")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
