from pyrogram import Client, filters
from pyrogram.types import Message
import logging
import time
from ..bot import user_states, batch_controller, process_batch_messages, active_downloads
from ..batch import BatchState
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("batch"))
async def batch_command(client: Client, message: Message):
    """Handle batch processing command."""
    logger.info(f"[HANDLER] /batch command received from user {message.from_user.id}")
    user_id = message.from_user.id

    # Check if user already has an active batch
    current_batch = await batch_controller.get_progress(user_id)
    if current_batch and current_batch.state in [BatchState.RUNNING, BatchState.PAUSED]:
        await message.reply_text(
            f"[WARNING] **Batch operation in progress**\n\n"
            f"Current: {current_batch.current}/{current_batch.total}\n"
            f"Status: {current_batch.state.value}\n\n"
            f"Use /batch_status to check progress\n"
            f"Use /batch_cancel to cancel current batch"
        )
        return

    # Start new batch setup
    user_states[user_id] = {
        "step": "batch_link",
        "chat_id": int(message.chat.id),
        "timestamp": time.time()
    }

    await message.reply_text(
        "[INFO] **Batch Processing Setup**\n\n"
        "Step 1: Send me the **first message link** to start from.\n\n"
        "**Supported formats:**\n"
        "• https://t.me/channel/123 (public)\n"
        "• https://t.me/c/123456/789 (private)\n\n"
        "**Note:** Bot will download messages sequentially from this point.\n\n"
        "Send /cancel to abort setup."
    )

@Client.on_message(filters.command("batch_status"))
async def batch_status_command(client: Client, message: Message):
    """Show current batch status."""
    logger.info(f"[HANDLER] /batch_status command received from user {message.from_user.id}")
    user_id = message.from_user.id

    current_batch = await batch_controller.get_progress(user_id)
    if not current_batch:
        await message.reply_text("[INFO] **No active batch operation**\n\nUse /batch to start a new batch process.")
        return

    # Calculate progress percentage
    progress_percent = (current_batch.current / current_batch.total * 100) if current_batch.total > 0 else 0

    # Calculate elapsed time
    elapsed = datetime.now() - current_batch.start_time
    elapsed_str = str(elapsed).split('.')[0]  # Remove microseconds

    status_text = (
        f"[METRICS] **Batch Status**\n\n"
        f"**Progress:** {current_batch.current}/{current_batch.total} ({progress_percent:.1f}%)\n"
        f"**Status:** {current_batch.state.value.title()}\n"
        f"**Elapsed Time:** {elapsed_str}\n"
        f"**Last Processed:** Message {current_batch.last_processed_id}\n\n"
    )

    if current_batch.state == BatchState.RUNNING:
        status_text += "**Controls:**\n• /batch_pause - Pause operation\n• /batch_cancel - Cancel operation"
    elif current_batch.state == BatchState.PAUSED:
        status_text += "**Controls:**\n• /batch_resume - Resume operation\n• /batch_cancel - Cancel operation"
    elif current_batch.state == BatchState.COMPLETED:
        status_text += "[SUCCESS] **Batch completed successfully!**"
        await batch_controller.cleanup_completed(user_id)
    elif current_batch.state == BatchState.CANCELLED:
        status_text += "[WARNING] **Batch was cancelled**"
        await batch_controller.cleanup_completed(user_id)

    await message.reply_text(status_text)

@Client.on_message(filters.command("batch_pause"))
async def batch_pause_command(client: Client, message: Message):
    """Pause current batch operation."""
    logger.info(f"[HANDLER] /batch_pause command received from user {message.from_user.id}")
    user_id = message.from_user.id

    if await batch_controller.pause_batch(user_id):
        await message.reply_text("[OK] **Batch paused**\n\nUse /batch_resume to continue or /batch_cancel to cancel.")
    else:
        await message.reply_text("[WARNING] **No active batch to pause**\n\nUse /batch to start a new batch process.")

@Client.on_message(filters.command("batch_resume"))
async def batch_resume_command(client: Client, message: Message):
    """Resume paused batch operation."""
    logger.info(f"[HANDLER] /batch_resume command received from user {message.from_user.id}")
    user_id = message.from_user.id

    # Get the current batch progress
    progress = await batch_controller.get_progress(user_id)
    if not progress or progress.state != BatchState.PAUSED:
        await message.reply_text("[WARNING] **No paused batch to resume**\n\nUse /batch to start a new batch process.")
        return

    # Resume the batch
    if await batch_controller.resume_batch(user_id):
        await message.reply_text("[OK] **Batch resumed**\n\nUse /batch_status to check progress.")

        # Recalculate remaining messages and the new starting point
        remaining_count = progress.total - progress.current
        new_start_message_id = progress.last_processed_id + 1

        # Restart the batch processing logic
        asyncio.create_task(
            process_batch_messages(
                user_id,
                progress.chat_id,
                new_start_message_id,
                remaining_count,
                progress.destination,
                progress.link_type
            )
        )
    else:
        await message.reply_text("[ERROR] **Failed to resume batch**\n\nPlease try again or start a new batch.")

@Client.on_message(filters.command("batch_cancel"))
async def batch_cancel_command(client: Client, message: Message):
    """Cancel current batch operation."""
    logger.info(f"[HANDLER] /batch_cancel command received from user {message.from_user.id}")
    user_id = message.from_user.id

    if await batch_controller.cancel_batch(user_id):
        await message.reply_text("[OK] **Batch cancelled**\n\nAll operations stopped. Use /batch to start a new batch process.")
        # Clean up user state
        user_states.pop(user_id, None)
        active_downloads.pop(user_id, None)
        await batch_controller.cleanup_completed(user_id)
    else:
        await message.reply_text("[INFO] **No active operation to cancel**")
