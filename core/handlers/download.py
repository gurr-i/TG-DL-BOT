from pyrogram import Client, filters
from pyrogram.types import Message
import logging
import time
from ..bot import active_downloads, user_states, parse_link, userbot_client, bot_client, fetch_message, process_message

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("download"))
async def download_command(client: Client, message: Message):
    logger.info(f"[HANDLER] /download command received from user {message.from_user.id}")
    user_id = message.from_user.id

    if user_id in active_downloads and active_downloads[user_id]:
        await message.reply_text("[WARNING] **Download in progress**\n\nPlease wait for current download to complete.")
        return

    if len(message.command) > 1:
        link = " ".join(message.command[1:])
        await process_download_link(message, link)
    else:
        user_states[user_id] = {
            "step": "download",
            "chat_id": int(message.chat.id),
            "timestamp": time.time()
        }
        await message.reply_text(
            "[DOWNLOAD] **Single Download**\n\n"
            "Send me the message link to download.\n\n"
            "**Examples:**\n"
            "• https://t.me/channel/123\n"
            "• https://t.me/c/123456/789\n\n"
            "Or use: /download <link>"
        )

async def process_download_link(m: Message, link: str) -> None:
    """Process a download link."""
    user_id = m.from_user.id
    destination = int(m.chat.id)

    # Mark as active
    active_downloads[user_id] = True

    try:
        # Parse link
        chat_id, message_id, link_type = parse_link(link)
        if not chat_id or not message_id:
            await m.reply_text(
                "[ERROR] **Invalid link format**\n\n"
                "**Supported formats:**\n"
                "• https://t.me/channel/123 (public)\n"
                "• https://t.me/c/123456/789 (private)\n\n"
                "Please check your link and try again."
            )
            return

        # Check private channel access
        if link_type == "private" and not userbot_client:
            await m.reply_text(
                "[WARNING] **Private Channel Access Required**\n\n"
                "This is a private channel, but userbot is not configured.\n\n"
                "**Setup Steps:**\n"
                "1. Use /session to generate session string\n"
                "2. Add SESSION=... to your .env file\n"
                "3. Restart the bot\n\n"
                "Contact admin for help."
            )
            return

        # Start processing
        status_msg = await m.reply_text("[SEARCH] **Fetching message...**")

        # Fetch message
        msg = await fetch_message(bot_client, userbot_client, chat_id, message_id, link_type)

        if not msg:
            await status_msg.edit("[ERROR] **Message not found or deleted**")
            return

        # Process the message
        result = await process_message(bot_client, userbot_client, msg, destination, link_type, user_id)

        # Update status based on result
        if "[OK]" in result:
            await status_msg.edit("[SUCCESS] **Download completed successfully!**")
        else:
            await status_msg.edit(f"[WARNING] **Result**: {result}")

    except Exception as e:
        logger.error(f"Download processing error: {e}")
        await m.reply_text(f"[ERROR] **Processing failed**: {str(e)[:100]}")

    finally:
        # Clean up
        active_downloads.pop(user_id, None)
        user_states.pop(user_id, None)
