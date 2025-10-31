from pyrogram import Client, filters
from pyrogram.types import Message
import logging

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    """Show help information."""
    logger.info(f"[HANDLER] /help command received from user {message.from_user.id}")

    help_text = (
        "[INFO] **Telegram Message Saver Bot - Help**\n\n"
        "**Basic Commands:**\n"
        "• /start - Start the bot\n"
        "• /test - Test bot functionality\n"
        "• /help - Show this help message\n"
        "• /speed - Run internet speed test\n"
        "• /stats - Show performance & disk statistics\n"
        "• /cleanup - Remove old downloaded files\n\n"
        "**Download Commands:**\n"
        "• /download <link> - Download single message\n"
        "• Send any Telegram link to download\n\n"
        "**Batch Commands:**\n"
        "• /batch - Start batch processing (parallel mode)\n"
        "• /batch_status - Check batch progress\n"
        "• /batch_pause - Pause current batch\n"
        "• /batch_resume - Resume paused batch\n"
        "• /batch_cancel - Cancel current batch\n\n"
        "**General:**\n"
        "• /cancel - Cancel current operation\n\n"
        "**Supported Link Formats:**\n"
        "• https://t.me/channel/123 (public)\n"
        "• https://t.me/c/123456/789 (private)\n\n"
        "**Note:** Private channels require userbot configuration."
    )

    await message.reply_text(help_text)
