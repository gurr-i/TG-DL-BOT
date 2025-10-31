from pyrogram import Client, filters
from pyrogram.types import Message
import logging
from ..bot import file_manager

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("cleanup"))
async def cleanup_command(client: Client, message: Message):
    """Clean up old downloaded files."""
    logger.info(f"[HANDLER] /cleanup command received from user {message.from_user.id}")

    if not file_manager:
        await message.reply_text("[ERROR] **File manager not available**\n\nThis feature requires MCP integration.")
        return

    try:
        status_msg = await message.reply_text("[INFO] **Cleaning up old files...**")

        # Clean files older than 24 hours
        cleaned = await file_manager.cleanup_old_files(max_age_hours=24)

        # Get updated stats
        dir_stats = await file_manager.get_directory_stats()
        disk_info = await file_manager.monitor_disk_space()

        cleanup_text = (
            "[SUCCESS] **Cleanup Complete**\n\n"
            f"**Files Removed:** {cleaned}\n"
            f"**Remaining Files:** {dir_stats['total_files']}\n"
            f"**Total Size:** {dir_stats['total_size_mb']:.1f} MB\n"
            f"**Free Space:** {disk_info.get('free_gb', 0):.1f} GB"
        )

        await status_msg.edit(cleanup_text)
    except Exception as e:
        logger.error(f"[HANDLER] Error in /cleanup handler: {e}")
        await message.reply_text(f"[ERROR] Cleanup failed: {str(e)[:100]}")
