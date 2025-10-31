from pyrogram import Client, filters
from pyrogram.types import Message
import logging

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("test"))
async def test_command(client: Client, message: Message):
    logger.info(f"[HANDLER] /test command received from user {message.from_user.id}")
    try:
        await message.reply_text("[OK] **Test Successful!**\n\nBot is responding correctly to commands.")
        logger.info(f"[HANDLER] /test response sent successfully")
    except Exception as e:
        logger.error(f"[HANDLER] Error in /test handler: {e}")
