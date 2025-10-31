#!/usr/bin/env python3
"""
Fixed Telegram Message Saver Bot with complete functionality
"""

import os
import re
import time
import logging
import asyncio
import atexit
from typing import Optional, Dict, Any, List
from datetime import datetime
from mimetypes import guess_type
from concurrent.futures import ThreadPoolExecutor

# Third-party imports
from pyrogram import Client, filters
from pyrogram.types import Message
from dotenv import load_dotenv

# Local imports
from .server import start_server
from .batch import BatchController, BatchState
from .speed_test import run_speedtest
from .config import config
from .performance import performance_optimizer
from .managers.download_manager import download_manager, DownloadTask

# Optional Redis state management and file manager
try:
    from .redis_state import redis_state
    from .managers.file_manager import file_manager
    REDIS_AVAILABLE = True
except Exception:
    # Logger not available yet, will log later
    redis_state = None
    file_manager = None
    REDIS_AVAILABLE = False

# Performance optimization
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass

# Configure logging with Windows-compatible encoding
import sys

class SafeFormatter(logging.Formatter):
    def format(self, record):
        msg = super().format(record)
        emoji_replacements = {
            '✅': '[OK]', '❌': '[ERROR]', '⚠️': '[WARNING]', '🚀': '[START]',
            '🤖': '[BOT]', '🌐': '[SERVER]', '📊': '[METRICS]', '🔍': '[SEARCH]',
            '📥': '[DOWNLOAD]', '📤': '[UPLOAD]', '⚡': '[FAST]', '🎉': '[SUCCESS]'
        }
        for emoji, replacement in emoji_replacements.items():
            msg = msg.replace(emoji, replacement)
        return msg

# Setup logging handlers
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(SafeFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

file_handler = logging.FileHandler('bot.log', mode='a', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logging.basicConfig(level=logging.INFO, handlers=[console_handler, file_handler], force=True)
logger = logging.getLogger(__name__)

# Log Redis availability
if not REDIS_AVAILABLE:
    logger.info("[INFO] Redis state management not available - using in-memory state only")

# Load environment variables
load_dotenv()

# Validate credentials
if not config.validate():
    logger.error("Missing API credentials! Check your .env file.")
    exit(1)
logger.info("[OK] Credentials validated successfully")

# Initialize clients with optimized settings
bot_client = Client(
    "bot_session",
    api_id=config.api_id,
    api_hash=config.api_hash,
    bot_token=config.bot_token,
    workers=8,
    workdir="./sessions"
)

userbot_client = None
if config.session:
    try:
        userbot_client = Client(
            "userbot_session",
            api_id=config.api_id,
            api_hash=config.api_hash,
            session_string=config.session,
            workers=4,
            workdir="./sessions"
        )
        logger.info("[OK] Userbot configured - Private channel access enabled")
    except Exception as e:
        logger.warning(f"[WARNING] Could not configure userbot: {e}")
        logger.warning("[WARNING] Bot will work for public channels only")
        userbot_client = None
else:
    logger.warning("[WARNING] No session string found. Bot will work for public channels only")
    logger.info("[INFO] Use /session command to generate a session string for private channels")

# Enhanced state management
user_states: Dict[int, Dict[str, Any]] = {}
progress_info: Dict[int, Dict[str, Any]] = {}
active_downloads: Dict[int, bool] = {}
rate_limits: Dict[int, Dict[str, Any]] = {}

# Batch operation controller
batch_controller = BatchController()

# Thread pool for CPU-intensive operations
thread_pool = ThreadPoolExecutor(max_workers=4)

# Optimized constants
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]
RATE_LIMIT_WINDOW = 60
MAX_REQUESTS = 30
MAX_FILE_SIZE = 2000 * 1024 * 1024  # 2GB
CONCURRENT_DOWNLOADS = 5

# Cleanup function
async def cleanup_resources():
    """Enhanced cleanup function with proper resource management."""
    try:
        if userbot_client and userbot_client.is_connected:
            await userbot_client.stop()
            logger.info("[OK] Userbot stopped successfully")
        
        if bot_client.is_connected:
            await bot_client.stop()
            logger.info("[OK] Bot client stopped successfully")
        
        thread_pool.shutdown(wait=True)
        logger.info("[OK] Thread pool shutdown complete")
        
        user_states.clear()
        progress_info.clear()
        active_downloads.clear()
        rate_limits.clear()
        
        session_dir = "./sessions"
        if os.path.exists(session_dir):
            for file in os.listdir(session_dir):
                if file.endswith(('.session', '.session-journal')):
                    try:
                        os.remove(os.path.join(session_dir, file))
                    except Exception as e:
                        logger.warning(f"Could not remove session file {file}: {e}")
        
        logger.info("[OK] Cleanup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

def sync_cleanup():
    """Synchronous wrapper for cleanup."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(cleanup_resources())
        else:
            loop.run_until_complete(cleanup_resources())
    except Exception as e:
        logger.error(f"Error in sync cleanup: {e}")

atexit.register(sync_cleanup)

# Core utility functions
def parse_link(link: str) -> tuple[Optional[str], Optional[int], Optional[str]]:
    """
    Parses a Telegram message link and extracts the chat ID, message ID, and link type.

    Args:
        link: The Telegram message link to parse.

    Returns:
        A tuple containing the chat ID, message ID, and link type ('public' or 'private').
        Returns (None, None, None) if the link is invalid.
    """
    if not link or not isinstance(link, str):
        return None, None, None
    
    link = link.strip()
    
    # Handle links without protocol
    if not link.startswith(('http://', 'https://')):
        if link.startswith('t.me/'):
            link = f"https://{link}"
        elif 't.me/' in link:
            link = f"https://{link}"
        else:
            return None, None, None
    
    try:
        # Private channel patterns
        private_patterns = [
            r"https://t\.me/c/(\d+)/(\d+)/?(?:\?[^/]*)?$",  # Standard private link
            r"https://t\.me/c/(\d+)/\d+/(\d+)/?(?:\?[^/]*)?$",  # Thread message in private channel
        ]
        
        for pattern in private_patterns:
            match = re.match(pattern, link)
            if match:
                chat_id = int(f"-100{match.group(1)}")
                message_id = int(match.group(2))
                logger.debug(f"Parsed private link: chat_id={chat_id}, message_id={message_id}")
                return chat_id, message_id, "private"
        
        # Public channel pattern - more flexible username validation
        public_match = re.match(r"https://t\.me/([^/?]+)/(\d+)/?(?:\?[^/]*)?$", link)
        if public_match:
            username = public_match.group(1)
            message_id = int(public_match.group(2))
            
            # Telegram username validation: 5-32 chars, alphanumeric + underscore, can't start/end with underscore
            # But allow some flexibility for edge cases and bots
            if (len(username) >= 3 and len(username) <= 32 and 
                re.match(r"^[a-zA-Z0-9][a-zA-Z0-9_]*[a-zA-Z0-9]$", username) or
                re.match(r"^[a-zA-Z0-9]{3,32}$", username)):  # Handle usernames without underscores
                logger.debug(f"Parsed public link: username={username}, message_id={message_id}")
                return username, message_id, "public"
            else:
                logger.warning(f"Invalid username format: {username}")
        
        logger.warning(f"Unsupported link format: {link}")
        return None, None, None
        
    except (ValueError, AttributeError) as e:
        logger.error(f"Error parsing link {link}: {e}")
        return None, None, None

async def fetch_message(client: Client, userbot: Optional[Client], chat_id: Any, message_id: int, link_type: str) -> Optional[Message]:
    """
    Fetches a message from a public or private channel with retry logic.

    Args:
        client: The bot's Pyrogram client.
        userbot: The user's Pyrogram client for private channels.
        chat_id: The ID of the chat where the message is located.
        message_id: The ID of the message to fetch.
        link_type: The type of link ('public' or 'private').

    Returns:
        The fetched message object, or None if the message could not be fetched.
    """
    target_client = client if link_type == "public" else userbot
    
    if not target_client:
        logger.error(f"No client available for {link_type} channel access")
        return None
    
    for attempt in range(MAX_RETRIES):
        try:
            logger.debug(f"Fetching message {message_id} from {chat_id} (attempt {attempt + 1})")
            
            message = await asyncio.wait_for(
                target_client.get_messages(chat_id, message_id),
                timeout=30.0
            )
            
            if message and not message.empty:
                logger.debug(f"Successfully fetched message {message_id}")
                return message
            else:
                logger.warning(f"Message {message_id} is empty or deleted")
                return None
                
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching message {message_id} (attempt {attempt + 1})")
        except Exception as e:
            error_msg = str(e).lower()
            
            if "message not found" in error_msg or "chat not found" in error_msg:
                logger.warning(f"Message {message_id} not found or inaccessible")
                return None
            elif "flood wait" in error_msg:
                wait_time = min(int(re.search(r'\d+', str(e)).group()) if re.search(r'\d+', str(e)) else 5, 60)
                logger.warning(f"Flood wait: sleeping for {wait_time}s")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Error fetching message {message_id} (attempt {attempt + 1}): {e}")
            
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAYS[attempt])
    
    logger.error(f"Failed to fetch message {message_id} after {MAX_RETRIES} attempts")
    return None

async def safe_remove_file(file_path: str) -> bool:
    """
    Safely removes a file from the local filesystem.

    Args:
        file_path: The path to the file to remove.

    Returns:
        True if the file was successfully removed, False otherwise.
    """
    if not file_path or not isinstance(file_path, str):
        return False
    
    try:
        if os.path.exists(file_path):
            await asyncio.get_event_loop().run_in_executor(thread_pool, os.remove, file_path)
            logger.debug(f"Removed file: {os.path.basename(file_path)}")
            return True
        return False
    except Exception as e:
        logger.warning(f"Could not remove file {os.path.basename(file_path)}: {e}")
        return False

async def validate_file(file_path: str) -> tuple[bool, str]:
    """
    Validates a file to ensure it exists, is a file, and is not empty or too large.

    Args:
        file_path: The path to the file to validate.

    Returns:
        A tuple containing a boolean indicating whether the file is valid and a message.
    """
    if not file_path or not isinstance(file_path, str):
        return False, "Invalid file path"
    
    try:
        def check_file():
            if not os.path.exists(file_path):
                return False, "File does not exist"
            
            if not os.path.isfile(file_path):
                return False, "Path is not a file"
            
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False, "File is empty"
            
            if file_size > MAX_FILE_SIZE:
                return False, f"File size ({file_size/1024/1024:.1f}MB) exceeds 2GB limit"
            
            try:
                with open(file_path, 'rb') as f:
                    f.read(1024)
            except Exception:
                return False, "File is not readable"
            
            return True, f"Valid file ({file_size/1024/1024:.1f}MB)"
        
        return await asyncio.get_event_loop().run_in_executor(thread_pool, check_file)
        
    except Exception as e:
        return False, f"Validation error: {str(e)}"

async def process_message(bot_client: Client, userbot: Optional[Client], message: Message, 
                        destination: int, link_type: str, user_id: int) -> str:
    """
    Processes a fetched message, downloading and forwarding media or copying text.

    Args:
        bot_client: The bot's Pyrogram client.
        userbot: The user's Pyrogram client for private channels.
        message: The message to process.
        destination: The chat ID where the message should be sent.
        link_type: The type of link ('public' or 'private').
        user_id: The ID of the user who initiated the request.

    Returns:
        A string indicating the result of the operation.
    """
    if not message:
        return "[ERROR] Message not found"
    
    try:
        # Log message details
        logger.info(f"[PROCESS] Message ID: {message.id}, Has media: {bool(message.media)}, Has text: {bool(message.text)}")
        
        if message.media:
            media_type = None
            if message.photo:
                media_type = "photo"
            elif message.video:
                media_type = "video"
            elif message.document:
                media_type = "document"
            elif message.audio:
                media_type = "audio"
            elif message.voice:
                media_type = "voice"
            elif message.video_note:
                media_type = "video_note"
            elif message.sticker:
                media_type = "sticker"
            elif message.animation:
                media_type = "animation"
            else:
                media_type = "unknown"
            
            logger.info(f"[PROCESS] Media type detected: {media_type}")
        
        # Handle media messages
        if message.media:
            # Try simple copy first for public channels
            if link_type == "public":
                try:
                    logger.info(f"[PROCESS] Attempting simple copy for public channel media")
                    await message.copy(chat_id=destination)
                    return "[OK] Media sent (copied)"
                except Exception as copy_error:
                    logger.warning(f"[PROCESS] Copy failed, falling back to download/upload: {copy_error}")
            
            # Use download/upload method for private channels or if copy failed
            return await process_media_message(bot_client, userbot, message, destination, link_type, user_id)
        
        # Handle text messages
        elif message.text:
            try:
                logger.info(f"[PROCESS] Processing text message")
                if link_type == "private" and userbot:
                    await bot_client.send_message(destination, text=message.text)
                else:
                    await message.copy(chat_id=destination)
                return "[OK] Text sent"
            except Exception as e:
                logger.error(f"Error sending text message: {e}")
                return f"[ERROR] Text failed: {str(e)[:50]}"
        
        else:
            logger.warning(f"[PROCESS] Unsupported message type - no media or text")
            return "[ERROR] Unsupported message type"
            
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return f"[ERROR] Error: {str(e)[:50]}"

async def process_media_message(bot_client: Client, userbot: Optional[Client], message: Message, 
                               destination: int, link_type: str, user_id: int) -> str:
    """
    Downloads, uploads, and forwards a media message with progress updates.

    Args:
        bot_client: The bot's Pyrogram client.
        userbot: The user's Pyrogram client for private channels.
        message: The message containing the media to process.
        destination: The chat ID where the media should be sent.
        link_type: The type of link ('public' or 'private').
        user_id: The ID of the user who initiated the request.

    Returns:
        A string indicating the result of the operation.
    """
    target_client = userbot if link_type == "private" and userbot else bot_client
    downloaded_file = None
    status_msg = None
    
    # Progress callback for downloads (optimized)
    async def download_progress(current, total):
        try:
            if status_msg:
                percentage = int((current / total) * 100) if total > 0 else 0
                
                # Initialize timing
                if not hasattr(download_progress, 'start_time'):
                    download_progress.start_time = time.time()
                    download_progress.last_update = 0
                    download_progress.last_percentage = -1
                
                elapsed = time.time() - download_progress.start_time
                
                # Use performance optimizer for intelligent throttling
                if not performance_optimizer.should_update_progress(
                    current, total, download_progress.last_update, download_progress.last_percentage
                ):
                    return
                
                # Calculate speed
                if elapsed > 0:
                    speed = current / elapsed / (1024 * 1024)  # MB/s
                    eta = performance_optimizer.calculate_eta(current, total, elapsed)
                else:
                    speed = 0
                    eta = "calculating..."
                
                # Create progress bar
                filled = int(percentage / 5)  # 20 blocks
                bar = "█" * filled + "░" * (20 - filled)
                
                progress_text = (
                    f"📥 **Downloading** (Optimized)\n\n"
                    f"`{bar}` {percentage}%\n\n"
                    f"🚀 Speed: {speed:.1f} MB/s\n"
                    f"⏱️ ETA: {eta}\n"
                    f"📦 {current/(1024*1024):.1f}/{total/(1024*1024):.1f} MB"
                )
                
                try:
                    await status_msg.edit(progress_text)
                    download_progress.last_update = time.time()
                    download_progress.last_percentage = percentage
                except Exception:
                    pass  # Ignore edit errors
        except Exception as e:
            logger.debug(f"Progress update error: {e}")
    
    # Progress callback for uploads (optimized)
    async def upload_progress(current, total):
        try:
            if status_msg:
                percentage = int((current / total) * 100) if total > 0 else 0
                
                # Initialize timing
                if not hasattr(upload_progress, 'start_time'):
                    upload_progress.start_time = time.time()
                    upload_progress.last_update = 0
                    upload_progress.last_percentage = -1
                
                elapsed = time.time() - upload_progress.start_time
                
                # Use performance optimizer for intelligent throttling
                if not performance_optimizer.should_update_progress(
                    current, total, upload_progress.last_update, upload_progress.last_percentage
                ):
                    return
                
                # Calculate speed
                if elapsed > 0:
                    speed = current / elapsed / (1024 * 1024)  # MB/s
                    eta = performance_optimizer.calculate_eta(current, total, elapsed)
                else:
                    speed = 0
                    eta = "calculating..."
                
                # Create progress bar
                filled = int(percentage / 5)  # 20 blocks
                bar = "█" * filled + "░" * (20 - filled)
                
                progress_text = (
                    f"📤 **Uploading** (Optimized)\n\n"
                    f"`{bar}` {percentage}%\n\n"
                    f"🚀 Speed: {speed:.1f} MB/s\n"
                    f"⏱️ ETA: {eta}\n"
                    f"📦 {current/(1024*1024):.1f}/{total/(1024*1024):.1f} MB"
                )
                
                try:
                    await status_msg.edit(progress_text)
                    upload_progress.last_update = time.time()
                    upload_progress.last_percentage = percentage
                except Exception:
                    pass  # Ignore edit errors
        except Exception as e:
            logger.debug(f"Progress update error: {e}")
    
    try:
        # Ensure downloads directory exists
        os.makedirs("downloads", exist_ok=True)
        
        # Send initial status
        status_msg = await bot_client.send_message(destination, "📥 **Starting download...**")
        
        # Download media
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"[DOWNLOAD] Attempt {attempt + 1} to download media from message {message.id}")
                
                downloaded_file = await asyncio.wait_for(
                    target_client.download_media(
                        message, 
                        file_name="downloads/",
                        progress=download_progress
                    ),
                    timeout=300.0
                )
                
                logger.info(f"[DOWNLOAD] Downloaded file: {downloaded_file}")
                
                if downloaded_file:
                    is_valid, validation_msg = await validate_file(downloaded_file)
                    if is_valid:
                        break
                    else:
                        await safe_remove_file(downloaded_file)
                        downloaded_file = None
                        raise Exception(f"File validation failed: {validation_msg}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"Download timeout (attempt {attempt + 1})")
                performance_optimizer.record_retry()
                if attempt < MAX_RETRIES - 1:
                    retry_delay = performance_optimizer.get_retry_delay(attempt, jitter=True)
                    logger.debug(f"Retrying after {retry_delay:.2f}s with jitter")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    raise Exception("Download timeout after retries")
                    
            except Exception as e:
                logger.warning(f"Download attempt {attempt + 1} failed: {e}")
                performance_optimizer.record_retry()
                if attempt < MAX_RETRIES - 1:
                    retry_delay = performance_optimizer.get_retry_delay(attempt, jitter=True)
                    logger.debug(f"Retrying after {retry_delay:.2f}s with jitter")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    raise
        
        if not downloaded_file:
            raise Exception("Download failed after all retries")
        
        # Upload media
        for attempt in range(MAX_RETRIES):
            try:
                caption = message.caption if message.caption else ""
                
                # Update status for upload
                try:
                    await status_msg.edit("📤 **Starting upload...**")
                except Exception:
                    pass
                
                # Choose appropriate upload method with progress
                if message.photo:
                    await bot_client.send_photo(
                        destination, 
                        photo=downloaded_file, 
                        caption=caption,
                        progress=upload_progress
                    )
                elif message.video:
                    await bot_client.send_video(
                        destination, 
                        video=downloaded_file, 
                        caption=caption,
                        progress=upload_progress
                    )
                elif message.document:
                    await bot_client.send_document(
                        destination, 
                        document=downloaded_file, 
                        caption=caption,
                        progress=upload_progress
                    )
                elif message.audio:
                    await bot_client.send_audio(
                        destination, 
                        audio=downloaded_file, 
                        caption=caption,
                        progress=upload_progress
                    )
                elif message.voice:
                    await bot_client.send_voice(
                        destination, 
                        voice=downloaded_file,
                        progress=upload_progress
                    )
                elif message.video_note:
                    await bot_client.send_video_note(
                        destination, 
                        video_note=downloaded_file,
                        progress=upload_progress
                    )
                elif message.sticker:
                    await bot_client.send_sticker(
                        destination, 
                        sticker=downloaded_file,
                        progress=upload_progress
                    )
                elif message.animation:
                    await bot_client.send_animation(
                        destination, 
                        animation=downloaded_file, 
                        caption=caption,
                        progress=upload_progress
                    )
                else:
                    await bot_client.send_document(
                        destination, 
                        document=downloaded_file, 
                        caption=caption,
                        progress=upload_progress
                    )
                
                # Success - record performance metrics
                if hasattr(download_progress, 'start_time'):
                    download_duration = time.time() - download_progress.start_time
                    performance_optimizer.record_download(
                        message.document.file_size if message.document else 0,
                        download_duration
                    )
                
                if hasattr(upload_progress, 'start_time'):
                    upload_duration = time.time() - upload_progress.start_time
                    performance_optimizer.record_upload(
                        message.document.file_size if message.document else 0,
                        upload_duration
                    )
                
                # Cleanup and return
                await safe_remove_file(downloaded_file)
                downloaded_file = None
                
                try:
                    await status_msg.delete()
                except Exception:
                    pass
                
                return "[OK] Media sent"
                
            except Exception as e:
                error_msg = str(e).lower()
                performance_optimizer.record_retry()
                if "flood wait" in error_msg:
                    wait_time = min(int(re.search(r'\d+', str(e)).group()) if re.search(r'\d+', str(e)) else 5, 60)
                    logger.warning(f"Flood wait during upload: {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                elif attempt < MAX_RETRIES - 1:
                    logger.warning(f"Upload attempt {attempt + 1} failed: {e}")
                    retry_delay = performance_optimizer.get_retry_delay(attempt, jitter=True)
                    logger.debug(f"Retrying upload after {retry_delay:.2f}s with jitter")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    raise
        
        raise Exception("Upload failed after all retries")
        
    except Exception as e:
        logger.error(f"Media processing error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        try:
            if status_msg:
                await status_msg.edit(f"[ERROR] Failed: {str(e)[:100]}")
        except Exception as edit_error:
            logger.error(f"Could not edit status message: {edit_error}")
        
        return f"[ERROR] Failed: {str(e)[:50]}"
        
    finally:
        if downloaded_file:
            await safe_remove_file(downloaded_file)

# Bot handlers









@bot_client.on_message(filters.text & ~filters.command(["start", "test", "download", "help", "speed", "stats", "cleanup", "batch", "batch_status", "batch_pause", "batch_resume", "batch_cancel", "cancel"]))
async def handle_text_message(_: Client, m: Message) -> None:
    """Handle text messages for download links and batch setup."""
    user_id = m.from_user.id
    
    # Check if user is in download state
    if user_id in user_states and user_states[user_id].get("step") == "download":
        await process_download_link(m, m.text)
        return
    
    # Check if user is in batch setup state
    if user_id in user_states and user_states[user_id].get("step") == "batch_link":
        await process_batch_setup(m, m.text)
        return
    
    # Check if user is in batch count state
    if user_id in user_states and user_states[user_id].get("step") == "batch_count":
        await process_batch_count(m, m.text)
        return
    
    # Otherwise, treat as potential download link
    if "t.me/" in m.text:
        logger.info(f"[HANDLER] Potential download link received from user {user_id}")
        await process_download_link(m, m.text)
    else:
        # Echo for testing
        await m.reply_text(f"[INFO] **Echo:** {m.text}\n\n[OK] Bot is receiving messages correctly!")

async def process_batch_setup(m: Message, link: str) -> None:
    """Process batch setup with the starting link."""
    user_id = m.from_user.id
    
    try:
        # Parse the link
        chat_id, message_id, link_type = parse_link(link)
        
        if not chat_id or not message_id:
            await m.reply_text(
                "[ERROR] **Invalid link format**\n\n"
                "Please send a valid Telegram message link.\n\n"
                "**Examples:**\n"
                "• https://t.me/channel/123\n"
                "• https://t.me/c/123456/789\n\n"
                "Send /cancel to abort."
            )
            return
        
        # Check private channel access
        if link_type == "private" and not userbot_client:
            await m.reply_text(
                "[WARNING] **Private Channel Access Required**\n\n"
                "This is a private channel, but userbot is not configured.\n\n"
                "Use /cancel to abort or contact admin for help."
            )
            return
        
        # Store batch info and ask for count
        user_states[user_id].update({
            "step": "batch_count",
            "chat_id_target": chat_id,
            "start_message_id": message_id,
            "link_type": link_type
        })
        
        await m.reply_text(
            "[OK] **Link validated successfully!**\n\n"
            f"**Channel:** {chat_id}\n"
            f"**Starting from:** Message {message_id}\n"
            f"**Type:** {link_type.title()}\n\n"
            "Step 2: How many messages to download?\n\n"
            "**Examples:**\n"
            "• 10 (download 10 messages)\n"
            "• 50 (download 50 messages)\n"
            "• 300 (maximum allowed)\n\n"
            "Send /cancel to abort."
        )
        
    except Exception as e:
        logger.error(f"Batch setup error: {e}")
        await m.reply_text(f"[ERROR] **Setup failed**: {str(e)[:100]}")

async def process_batch_count(m: Message, count_text: str) -> None:
    """Process batch count and start the batch operation."""
    user_id = m.from_user.id
    
    try:
        # Parse count
        try:
            count = int(count_text.strip())
        except ValueError:
            await m.reply_text(
                "[ERROR] **Invalid number**\n\n"
                "Please send a valid number (1-300).\n\n"
                "Send /cancel to abort."
            )
            return
        
        # Validate count
        if count < 1 or count > 300:
            await m.reply_text(
                "[ERROR] **Invalid range**\n\n"
                "Please send a number between 1 and 300.\n\n"
                "Send /cancel to abort."
            )
            return
        
        # Get batch info from state
        state = user_states[user_id]
        chat_id_target = state["chat_id_target"]
        start_message_id = state["start_message_id"]
        link_type = state["link_type"]
        destination = state["chat_id"]
        
        # Clean up any previous completed batches
        await batch_controller.cleanup_completed(user_id)
        
        # Initialize batch operation
        success = await batch_controller.start_batch(user_id, count, start_message_id, chat_id_target, link_type, destination)
        if not success:
            await m.reply_text("[ERROR] **Batch initialization failed**\n\nYou may have an active batch. Use /batch_cancel first.")
            return
        
        # Persist batch state to Redis for recovery (if available)
        if REDIS_AVAILABLE and redis_state:
            try:
                await redis_state.save_batch_state(user_id, {
                    "chat_id_target": chat_id_target,
                    "start_message_id": start_message_id,
                    "count": count,
                    "link_type": link_type,
                    "destination": destination,
                    "started_at": datetime.now().isoformat()
                })
            except Exception as e:
                logger.warning(f"Could not save batch state to Redis: {e}")
        
        # Clean up user state
        user_states.pop(user_id, None)
        
        # Start batch processing
        await m.reply_text(
            f"[SUCCESS] **Batch started!**\n\n"
            f"**Messages to download:** {count}\n"
            f"**Starting from:** Message {start_message_id}\n\n"
            f"Use /batch_status to check progress.\n"
            f"Use /batch_pause to pause operation.\n"
            f"Use /batch_cancel to cancel."
        )
        
        # Start the actual batch processing
        asyncio.create_task(
            process_batch_messages(user_id, chat_id_target, start_message_id, count, destination, link_type)
        )
        
    except Exception as e:
        logger.error(f"Batch count processing error: {e}")
        await m.reply_text(f"[ERROR] **Processing failed**: {str(e)[:100]}")

async def process_batch_messages(user_id: int, chat_id: Any, start_message_id: int, 
                               count: int, destination: int, link_type: str) -> None:
    """Process batch messages with parallel downloads for better performance."""
    logger.info(f"[BATCH] Starting PARALLEL batch processing for user {user_id}: {count} messages from {start_message_id}")
    
    try:
        # Create download tasks
        tasks = [
            DownloadTask(
                chat_id=chat_id,
                message_id=start_message_id + i,
                link_type=link_type,
                destination=destination,
                user_id=user_id
            )
            for i in range(count)
        ]
        
        # Progress callback for batch
        async def batch_progress_callback(completed: int, total: int, message_id: int):
            progress = await batch_controller.get_progress(user_id)
            if progress and progress.state == BatchState.RUNNING:
                # Update progress with the actual message ID of the completed task
                if completed > 0:
                    await batch_controller.update_progress(user_id, message_id)
        
        # Use parallel download manager (3 concurrent downloads)
        logger.info(f"[BATCH] Using parallel download manager with 3 concurrent downloads")
        results = await download_manager.download_batch_parallel(
            bot_client,
            userbot_client,
            tasks,
            fetch_message,
            process_message,
            progress_callback=batch_progress_callback
        )
        
        # Count successes and failures
        successes = sum(1 for _, result in results if "[OK]" in result or "[SUCCESS]" in result)
        failures = len(results) - successes
        
        # Check final status
        final_progress = await batch_controller.get_progress(user_id)
        if final_progress:
            elapsed = datetime.now() - final_progress.start_time
            elapsed_str = str(elapsed).split('.')[0]
            
            try:
                await bot_client.send_message(
                    destination,
                    f"[SUCCESS] **Batch completed!**\n\n"
                    f"**Total:** {len(results)} messages\n"
                    f"**Successful:** {successes}\n"
                    f"**Failed:** {failures}\n"
                    f"**Elapsed time:** {elapsed_str}\n"
                    f"**Mode:** Parallel (3 concurrent)\n\n"
                    f"Performance: {len(results)/elapsed.total_seconds():.2f} msg/sec"
                )
            except Exception as e:
                logger.error(f"[BATCH] Error sending completion message: {e}")
        
    except Exception as e:
        logger.error(f"[BATCH] Fatal error in batch processing: {e}")
        performance_optimizer.record_failure()
        try:
            await bot_client.send_message(
                destination,
                f"[ERROR] **Batch failed**\n\nError: {str(e)[:100]}"
            )
        except Exception:
            pass
    
    logger.info(f"[BATCH] Batch processing completed for user {user_id}")

import importlib
import pkgutil

def load_handlers():
    """Dynamically load all handlers from the 'handlers' directory."""
    handlers_dir = os.path.join(os.path.dirname(__file__), "handlers")
    for _, name, _ in pkgutil.iter_modules([handlers_dir]):
        try:
            importlib.import_module(f".handlers.{name}", __package__)
            logger.info(f"Successfully loaded handler: {name}")
        except Exception as e:
            logger.error(f"Failed to load handler {name}: {e}")

def main():
    """Main function to start the bot."""
    try:
        os.makedirs("./sessions", exist_ok=True)
        
        load_handlers()

        start_server()
        logger.info("[OK] Health check server started")
        
        if userbot_client:
            logger.info("[INFO] Starting userbot...")
            userbot_client.start()
            logger.info("[OK] Userbot started successfully")
        
        logger.info("[INFO] Starting bot client...")
        logger.info("[OK] Bot is ready and listening for messages...")
        logger.info("[INFO] Send /start or /test to the bot to verify it's working")
        
        bot_client.run()
        
    except KeyboardInterrupt:
        logger.info("[STOP] Bot stopped by user")
    except Exception as e:
        logger.error(f"[ERROR] Bot startup error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("[STOP] Bot shutdown complete")