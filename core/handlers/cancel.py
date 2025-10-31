from pyrogram import Client, filters
from pyrogram.types import Message
import logging
from ..bot import user_states, active_downloads

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("cancel"))
async def cancel_command(client: Client, message: Message):
    """Cancel current operation."""
    logger.info(f"[HANDLER] /cancel command received from user {message.from_user.id}")
    user_id = message.from_user.id

    # Clean up any active state
    user_states.pop(user_id, None)
    active_downloads.pop(user_id, None)

    await message.reply_text("[OK] **Operation cancelled**\n\nAll current operations have been stopped.")
