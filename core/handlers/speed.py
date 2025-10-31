from pyrogram import Client, filters
from pyrogram.types import Message
import logging
from ..speed_test import run_speedtest

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("speed"))
async def speed_command(client: Client, message: Message):
    """Run internet speed test."""
    logger.info(f"[HANDLER] /speed command received from user {message.from_user.id}")
    try:
        result = await run_speedtest(client, message)
        if result:
            await message.reply_text(result)
    except Exception as e:
        logger.error(f"[HANDLER] Error in /speed handler: {e}")
        await message.reply_text(f"[ERROR] Speed test failed: {str(e)[:100]}")
