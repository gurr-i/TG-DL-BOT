from pyrogram import Client, filters
from pyrogram.types import Message
import logging

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    logger.info(f"[HANDLER] /start command received from user {message.from_user.id}")
    try:
        response = (
            "[START] **Welcome to Telegram Message Saver Bot!**\n\n"
            "[OK] Bot is working perfectly!\n\n"
            "**Quick Commands:**\n"
            "• /download <link> - Download a single message\n"
            "• /batch - Start batch processing\n"
            "• /help - Show all commands\n"
            "• /test - Test bot functionality\n\n"
            "**Status:** All systems operational!\n\n"
            "Send me a message link to get started!"
        )
        await message.reply_text(response)
        logger.info(f"[HANDLER] /start response sent successfully")
    except Exception as e:
        logger.error(f"[HANDLER] Error in /start handler: {e}")
