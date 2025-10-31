from pyrogram import Client, filters
from pyrogram.types import Message
import logging
from ..performance import performance_optimizer
from ..managers.download_manager import download_manager
from ..managers.file_manager import file_manager

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("stats"))
async def stats_command(client: Client, message: Message):
    """Show performance statistics."""
    logger.info(f"[HANDLER] /stats command received from user {message.from_user.id}")
    try:
        perf_stats = performance_optimizer.get_metrics()
        dl_stats = download_manager.get_stats()

        # Get disk space info (if file_manager available)
        if file_manager:
            disk_info = await file_manager.monitor_disk_space()
            dir_stats = await file_manager.get_directory_stats()
        else:
            disk_info = {"free_gb": 0, "warning": False}
            dir_stats = {"total_files": 0, "total_size_mb": 0}

        stats_text = (
            "[METRICS] **Performance Statistics**\n\n"
            f"**Downloads:** {perf_stats['total_downloads']}\n"
            f"**Uploads:** {perf_stats['total_uploads']}\n"
            f"**Data Downloaded:** {perf_stats['total_data_downloaded_mb']} MB\n"
            f"**Data Uploaded:** {perf_stats['total_data_uploaded_mb']} MB\n"
            f"**Avg Download Speed:** {perf_stats['average_download_speed_mbps']} MB/s\n"
            f"**Avg Upload Speed:** {perf_stats['average_upload_speed_mbps']} MB/s\n"
            f"**Success Rate:** {perf_stats['success_rate']}%\n"
            f"**Failed Operations:** {perf_stats['failed_operations']}\n"
            f"**Retry Count:** {perf_stats['retry_count']}\n"
            f"**Uptime:** {perf_stats['uptime_seconds']}s\n\n"
            f"**Download Manager:**\n"
            f"• Max Concurrent: {dl_stats['max_concurrent']}\n"
            f"• Active Tasks: {dl_stats['active_tasks']}\n"
            f"• Available Slots: {dl_stats['available_slots']}\n\n"
            f"**Disk Usage:**\n"
            f"• Files: {dir_stats['total_files']}\n"
            f"• Size: {dir_stats['total_size_mb']:.1f} MB\n"
            f"• Free Space: {disk_info.get('free_gb', 0):.1f} GB"
        )

        if disk_info.get('warning'):
            stats_text += "\n\n[WARNING] Low disk space! Use /cleanup"

        await message.reply_text(stats_text)
    except Exception as e:
        logger.error(f"[HANDLER] Error in /stats handler: {e}")
        await message.reply_text(f"[ERROR] Could not retrieve stats: {str(e)[:100]}")
