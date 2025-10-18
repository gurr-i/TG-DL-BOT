import os as O
import re as R
import time
import logging
from typing import Optional, Dict, Any
import atexit
from pyrogram import Client as C, filters as F
from pyrogram.types import Message as M
from dotenv import load_dotenv
from datetime import datetime
from core.server import start_server
from asyncio import Lock, Queue, create_task
from aiofiles import os as aios
from mimetypes import guess_type
import asyncio
from core.batch import BatchController, BatchState
from core.speed_test import run_speedtest


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import configuration
from core.config import config

# Validate credentials
if not config.validate():
    logger.error("Missing API credentials! Check your .env file.")
    exit(1)
logger.info("Credentials found!")

# Assign credentials to shorter variables for convenience
A = config.api_id
H = config.api_hash
T = config.bot_token
S = config.session

# Initialize clients
X = C("X", api_id=A, api_hash=H, bot_token=T)
Y = None
if S:
    try:
        Y = C("Y", api_id=A, api_hash=H, session_string=S)
        Y.start()
        logger.info("✅ Userbot started successfully - Private channel access enabled")
    except Exception as e:
        logger.warning(f"⚠️ Could not start userbot: {e}")
        logger.warning("⚠️ Bot will work for public channels only. Use /session command to set up userbot for private channels.")
        Y = None
else:
    logger.warning("⚠️ No session string found. Bot will work for public channels only.")
    logger.info("💡 To access private channels, use /session command to generate a session string.")

# State management
user_states: Dict[int, Dict[str, Any]] = {}
progress_info: Dict[int, Dict[str, Any]] = {}

# Rate limiting and queues
rate_limits: Dict[int, Dict[str, Any]] = {}
download_queue: Queue = Queue()
upload_queue: Queue = Queue()
queue_lock = Lock()

# Batch operation controller
batch_controller = BatchController()

# Constants
MAX_RETRIES = 3
RATE_LIMIT_WINDOW = 60  # seconds
MAX_REQUESTS = 20  # per window
MAX_FILE_SIZE = 2000 * 1024 * 1024  # 2GB in bytes

def cleanup():
    """Cleanup function to stop userbot on exit."""
    if Y and Y.is_connected:
        try:
            Y.stop()
            logger.info(" 🪸  Userbot stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping userbot: {e}")
atexit.register(cleanup)

def parse_link(link: str) -> tuple[Optional[str], Optional[int], Optional[str]]:
    """Parse Telegram link to extract chat ID, message ID, and link type.
    
    Supports formats:
    - Private channel: https://t.me/c/chatid/messageid
    - Group with topics: https://t.me/c/chatid/topicid/messageid
    - Public channel: https://t.me/username/messageid
    """
    # Match private channel/group (with optional topic ID)
    # Format: https://t.me/c/123456/789 or https://t.me/c/123456/2/789
    private_match = R.match(r"https://t\.me/c/(\d+)/(?:\d+/)?(\d+)", link)
    
    # Match public channel
    public_match = R.match(r"https://t\.me/([^/]+)/(\d+)", link)
    
    if private_match:
        chat_id = int(f"-100{private_match.group(1)}")
        message_id = int(private_match.group(2))
        logger.info(f"Parsed private link: chat_id={chat_id}, message_id={message_id}")
        return chat_id, message_id, "private"
    elif public_match:
        username = public_match.group(1)
        message_id = int(public_match.group(2))
        logger.info(f"Parsed public link: username={username}, message_id={message_id}")
        return username, message_id, "public"
    
    logger.error(f"Failed to parse link: {link}")
    return None, None, None

async def fetch_message(client: C, userbot: Optional[C], chat_id: Any, message_id: int, link_type: str) -> Optional[M]:
    """Fetch a message from the specified chat and ID with retry logic."""
    target_client = client if link_type == "public" else userbot
    
    if not target_client:
        logger.error(f"No client available for {link_type} channel access")
        return None
    
    retry_count = 0
    max_retries = 2  # Retry twice for transient network issues
    
    while retry_count <= max_retries:
        try:
            logger.info(f"Fetching message from 🪼 {chat_id}, Message ID: {message_id}, Type: {link_type} (attempt {retry_count + 1})")
            message = await target_client.get_messages(chat_id, message_id)
            
            if message:
                logger.info(f"Successfully fetched message {message_id}")
                return message
            else:
                logger.warning(f"Message {message_id} returned None")
                return None
                
        except Exception as e:
            retry_count += 1
            logger.error(f"Error fetching message {message_id} (attempt {retry_count}/{max_retries + 1}): {e}")
            
            if retry_count <= max_retries:
                # Exponential backoff: 1s, 2s, 4s
                await asyncio.sleep(2 ** (retry_count - 1))
            else:
                logger.error(f"Failed to fetch message {message_id} after {max_retries + 1} attempts")
                return None
    
    return None

async def progress_update(current: int, total: int, user_data: Dict[str, Any]) -> None:
    """Update progress for download/upload with percentage, speed, and ETA."""
    user_id = user_data.get("user_id")
    progress_percentage = (current / total) * 100
    progress_step = int(progress_percentage // 10) * 10

    if (user_id not in progress_info or 
        progress_info[user_id].get("last_step", 0) != progress_step or 
        progress_percentage >= 100):
        
        progress_info[user_id]["last_step"] = progress_step
        completed_blocks = int(progress_percentage / 10)
        progress_bar = "🔥" * completed_blocks + "🪵" * (10 - completed_blocks)

        elapsed_time = time.time() - user_data["start_time"]
        speed = (current / elapsed_time) / (1024 * 1024) if elapsed_time > 0 else 0
        eta = time.strftime("%M:%S", time.gmtime((total - current) / (speed * 1024 * 1024))) if speed > 0 else "00:00"

        action = "Downloading" if user_data["phase"] == "download" else "Uploading"
        file_info = user_data.get("file_data", {})
        action_message = (f"**{action} - {file_info.get('file_name', '')} ({file_info.get('file_size', 0):.2f} MB)**"
                         if file_info else f"**{action}.. Hang tight**")

        message_text = f"{action_message}\n\n{progress_bar}\n\n📊 **Completed**: {progress_percentage:.2f}%\n🚀 **Speed**: {speed:.2f} MB/sec\n⏳ **ETA**: {eta}\n\n**Powered by @unknown_5145**"

        try:
            await user_data["client"].edit_message_text(user_data["chat_id"], user_data["message_id"], message_text)
        except Exception as e:
            logger.warning(f"Failed to update progress: {e}")

        if progress_percentage >= 100 and user_id in progress_info:
            del progress_info[user_id]["last_step"]

async def safe_remove_file(file_path: str) -> None:
    """Safely remove a file if it exists."""
    try:
        if O.path.exists(file_path):
            O.remove(file_path)
            logger.info(f"Removed file: {file_path}")
    except OSError as e:
        logger.warning(f"Could not remove file {file_path}: {e}")

async def validate_file(file_path: str) -> tuple[bool, str]:
    """Validate file size and type before processing."""
    try:
        if not O.path.exists(file_path):
            return False, "File does not exist"
        
        file_size = O.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            return False, f"File size ({file_size/1024/1024:.2f}MB) exceeds limit (2GB)"
            
        mime_type = guess_type(file_path)[0]
        if not mime_type:
            return False, "Unknown file type"
            
        return True, ""
    except Exception as e:
        return False, f"Validation error: {str(e)}"

async def check_rate_limit(user_id: int) -> bool:
    """Check if user has exceeded rate limits."""
    now = time.time()
    if user_id not in rate_limits:
        rate_limits[user_id] = {"count": 0, "window_start": now}
    
    user_limit = rate_limits[user_id]
    if now - user_limit["window_start"] > RATE_LIMIT_WINDOW:
        user_limit["count"] = 0
        user_limit["window_start"] = now
    
    if user_limit["count"] >= MAX_REQUESTS:
        return False
    
    user_limit["count"] += 1
    return True

async def process_message(bot_client: C, userbot: Optional[C], message: M, destination: int, 
                        link_type: str, user_id: int) -> str:
    """Process and forward media or text messages with enhanced error handling and queuing."""
    if not message:
        return "Message not found"
        
    # Check rate limits
    if not await check_rate_limit(user_id):
        return "Rate limit exceeded. Please wait a minute."
        
    # Add request to queue
    async with queue_lock:
        task_id = f"{user_id}_{int(time.time())}"
        await download_queue.put((task_id, message))
        logger.info(f"Added task {task_id} to download queue")

    retry_count = 0
    downloaded_file = None  # Track downloaded file for cleanup
    
    try:
        if message.media:
            start_time = time.time()
            if link_type == "private" and userbot:
                try:
                    while retry_count < MAX_RETRIES:
                        try:
                            download_msg = await bot_client.send_message(destination, "⚡Starting Download⚡")
                            progress_info[user_id] = {"cancel": False, "last_step": 0, "user_id": user_id, "retry_count": retry_count}
                            
                            # Log download attempt
                            logger.info(f"Download attempt {retry_count + 1} for user {user_id}")

                            user_data_download = {
                                "client": bot_client, "chat_id": destination, "message_id": download_msg.id,
                                "start_time": start_time, "phase": "download", "user_id": user_id
                            }
                            downloaded_file = await userbot.download_media(
                                message, progress=progress_update, progress_args=(user_data_download,)
                            )
                            
                            # Validate downloaded file
                            is_valid, error_msg = await validate_file(downloaded_file)
                            if not is_valid:
                                raise Exception(error_msg)
                                
                            break  # Success, exit retry loop
                        except Exception as e:
                            retry_count += 1
                            if retry_count >= MAX_RETRIES:
                                logger.error(f"Max retries reached for download: {e}")
                                raise
                            logger.warning(f"Download attempt {retry_count} failed: {e}. Retrying...")
                            await asyncio.sleep(2 ** retry_count)  # Exponential backoff

                    if progress_info.get(user_id, {}).get("cancel"):
                        await bot_client.edit_message_text(destination, download_msg.id, "Canceled.")
                        await safe_remove_file(downloaded_file)
                        del progress_info[user_id]
                        return "Canceled."

                    if not downloaded_file:
                        await bot_client.edit_message_text(destination, download_msg.id, "Failed.")
                        del progress_info[user_id]
                        return "Failed."

                    try:
                        await bot_client.delete_messages(destination, download_msg.id)
                    except Exception:
                        logger.warning(f"Failed to delete download message {download_msg.id}")

                    file_name = O.path.basename(downloaded_file)
                    file_size = O.path.getsize(downloaded_file) / (1024 * 1024)
                    upload_msg = await bot_client.send_message(destination, f"Uploading {file_name} ({file_size:.2f} MB)...")
                    progress_info[user_id] = {"cancel": False, "last_step": 0, "user_id": user_id}

                    user_data_upload = {
                        "client": bot_client, "chat_id": destination, "message_id": upload_msg.id,
                        "start_time": start_time, "phase": "upload", "user_id": user_id,
                        "file_data": {"file_name": file_name, "file_size": file_size}
                    }

                    retry_count = 0
                    while retry_count < MAX_RETRIES:
                        try:
                            # Add to upload queue
                            async with queue_lock:
                                await upload_queue.put((task_id, downloaded_file))
                                logger.info(f"Added task {task_id} to upload queue")

                            if message.sticker:
                                await bot_client.send_photo(destination, photo=downloaded_file, caption=message.caption.markdown if message.caption else "", progress=progress_update, progress_args=(user_data_upload, ))
                            elif message.video:
                                width, height, duration = message.video.width, message.video.height, message.video.duration
                                await bot_client.send_video(destination, video=downloaded_file, caption=message.caption.markdown if message.caption else "", thumb="Thumb.jpg", width=width, height=height, duration=duration, progress=progress_update, progress_args=(user_data_upload, ))
                            elif message.video_note:
                                await bot_client.send_video_note(destination, video_note=downloaded_file, progress=progress_update, progress_args=(user_data_upload, ))
                            elif message.voice:
                                await bot_client.send_voice(destination, voice=downloaded_file, progress=progress_update, progress_args=(user_data_upload, ))
                            elif message.audio:
                                await bot_client.send_audio(destination, audio=downloaded_file, caption=message.caption.markdown if message.caption else "", thumb="Thumb.jpg", progress=progress_update, progress_args=(user_data_upload, ))
                            elif message.photo:
                                await bot_client.send_photo(destination, photo=downloaded_file, caption=message.caption.markdown if message.caption else "", progress=progress_update, progress_args=(user_data_upload, ))
                            elif message.document:
                                await bot_client.send_document(destination, document=downloaded_file, caption=message.caption.markdown if message.caption else "", progress=progress_update, progress_args=(user_data_upload, ))
                            elif message.animation:
                                await bot_client.send_animation(destination, animation=downloaded_file, caption=message.caption.markdown if message.caption else "", progress=progress_update, progress_args=(user_data_upload, ))
                            
                            # Cleanup after successful upload
                            await safe_remove_file(downloaded_file)
                            downloaded_file = None  # Mark as cleaned up
                            try:
                                await bot_client.delete_messages(destination, upload_msg.id)
                            except Exception as e:
                                logger.warning(f"Failed to delete upload message {upload_msg.id}: {e}")
                            
                            # Clear progress info
                            if user_id in progress_info:
                                del progress_info[user_id]
                            
                            # Log success
                            logger.info(f"Successfully processed task {task_id}")
                            return "Done."
                            
                        except (OSError, AttributeError, TimeoutError) as e:
                            # Handle Pyrogram session crashes and timeouts
                            retry_count += 1
                            error_type = type(e).__name__
                            logger.error(f"Pyrogram error during upload (attempt {retry_count}/{MAX_RETRIES}): {error_type} - {e}")
                            
                            if retry_count >= MAX_RETRIES:
                                error_msg = f"Upload failed after {MAX_RETRIES} attempts. Network or session issue."
                                logger.error(f"Max retries reached: {error_msg}")
                                try:
                                    await bot_client.edit_message_text(destination, upload_msg.id, f"❌ {error_msg}")
                                except Exception:
                                    pass
                                raise Exception(error_msg)
                            
                            logger.warning(f"Retrying upload after {error_type}...")
                            await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                            
                        except Exception as e:
                            retry_count += 1
                            if retry_count >= MAX_RETRIES:
                                logger.error(f"Max retries reached for upload: {e}")
                                try:
                                    await bot_client.edit_message_text(destination, upload_msg.id, f"❌ Upload failed: {str(e)[:100]}")
                                except Exception:
                                    pass
                                raise
                            logger.warning(f"Upload attempt {retry_count} failed: {e}. Retrying...")
                            await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                
                finally:
                    # Ensure cleanup of downloaded file on any error
                    if downloaded_file:
                        await safe_remove_file(downloaded_file)
                        if user_id in progress_info:
                            del progress_info[user_id]
            else:
                try:
                    await message.copy(chat_id=destination)
                    return "Copied."
                except Exception as e:
                    logger.error(f"Error copying message: {e}")
                    return f"Copy failed: {str(e)}"
        elif message.text:
            try:
                await (bot_client.send_message(destination, text=message.text.markdown) 
                      if link_type == "private" else message.copy(chat_id=destination))
                return "Sent."
            except Exception as e:
                logger.error(f"Error sending text message: {e}")
                return f"Send failed: {str(e)}"
        else:
            return "Unsupported message type"
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return f"Error: {str(e)}"

@X.on_message(F.command("help"))
async def help_command(_: C, m: M) -> None:
    help_text = (
        "📚 **Available Commands**\n\n"
        "• /start - Start the bot\n"
        "• /download <link> - Download a single message/media\n"
        "• /batch - Start batch processing messages\n"
        "• /join <invite_link> - Join a private channel\n"
        "• /session - Set up userbot for private channels\n"
        "• /pause - Pause ongoing batch operation\n"
        "• /resume - Resume paused batch operation\n"
        "• /cancel - Cancel ongoing operations\n"
        "• /speed - Check Bot speed\n"
        "• /help - Show this help message\n\n"
        "📝 **Usage Examples**:\n"
        "1. To download a single message:\n"
        "   `/download https://t.me/channel/123`\n\n"
        "2. To join a private channel:\n"
        "   `/join https://t.me/joinchat/...`\n\n"
        "3. To start batch saving:\n"
        "   1. Send /batch\n"
        "   2. Send the first message link\n"
        "   3. Enter number of messages to save (max 300)\n\n"
        "⚡ **Tips**:\n"
        "• Use /session to set up private channel access\n"
        "• Use /pause and /resume to control batch operations\n"
        "• Use /cancel to stop any ongoing operation\n"
        "\n💡 For more help, contact @unknown_5145"
    )
    await m.reply_text(help_text)

@X.on_message(F.command("start"))
async def start(_: C, m: M) -> None:
    await m.reply_text("Welcome to bot. Use /download to save a single message, /batch to save multiple messages, /join to join a private channel, or /help to see all commands.")

@X.on_message(F.command("join"))
async def join_channel(_: C, m: M) -> None:
    if not Y:
        await m.reply_text("⚠️ Userbot is not available. Use /session to set up userbot for private channel access.")
        return
    
    if len(m.command) < 2:
        await m.reply_text("Please provide an invite link. Usage: /join <invite_link>")
        return
    try:
        await Y.join_chat(m.command[1])
        await m.reply_text("✅ Successfully joined the private channel!")
    except Exception as e:
        await m.reply_text(f"❌ Failed to join the channel: {e}")

@X.on_message(F.command("batch"))
async def batch(_: C, m: M) -> None:
    user_id = m.from_user.id
    user_states[user_id] = {"step": "start", "chat_id": int(m.chat.id), "timestamp": time.time()}
    await m.reply_text("Send start link.")

@X.on_message(F.command("download"))
async def download_single(_: C, m: M) -> None:
    """Download a single message from a link."""
    user_id = m.from_user.id
    
    # Check if link is provided with the command
    if len(m.command) > 1:
        link = m.command[1]
    else:
        user_states[user_id] = {"step": "download", "chat_id": int(m.chat.id), "timestamp": time.time()}
        await m.reply_text("📥 Send me the message link to download.")
        return
    
    # Process the link immediately
    await process_download_link(m, link)

async def process_download_link(m: M, link: str) -> None:
    """Process a single download link."""
    user_id = m.from_user.id
    destination = int(m.chat.id)
    
    chat_id, message_id, link_type = parse_link(link)
    if not chat_id or not message_id:
        await m.reply_text("❌ Invalid link. Please check the format.\n\nSupported formats:\n• https://t.me/channel/123\n• https://t.me/c/123456/789")
        if user_id in user_states:
            del user_states[user_id]
        return
    
    # Check access for private channels
    if link_type == "private":
        if not Y:
            await m.reply_text("⚠️ This is a private channel link, but userbot is not configured.\n\nTo access private channels:\n1. Use /session to generate a session string\n2. Add it to your .env file as SESSION=...\n3. Restart the bot")
            if user_id in user_states:
                del user_states[user_id]
            return
        try:
            await Y.get_messages(chat_id, message_id)
        except Exception as e:
            await m.reply_text(f"❌ Cannot access this private channel.\nUse /join <invite_link> first.\n\nError: {e}")
            if user_id in user_states:
                del user_states[user_id]
            return
    
    # Fetch and process the message
    status_msg = await m.reply_text("⚡ Fetching message...")
    msg = await fetch_message(X, Y, chat_id, message_id, link_type)
    
    if not msg:
        await status_msg.edit("❌ Message not found or inaccessible.")
        if user_id in user_states:
            del user_states[user_id]
        return
    
    # Process the message
    result = await process_message(X, Y, msg, destination, link_type, user_id)
    
    if "Done" in result or "Sent" in result or "Copied" in result:
        await status_msg.edit(f"✅ Download complete!")
    else:
        await status_msg.edit(f"❌ {result}")
    
    # Clean up user state
    if user_id in user_states:
        del user_states[user_id]

@X.on_message(F.command("session"))
async def session_command(_: C, m: M) -> None:
    """Guide user to generate a session string."""
    session_help = (
        "🔐 **Session String Setup**\n\n"
        "To access private channels, you need a session string. Here's how:\n\n"
        "**Option 1: Using utils/session.py (Recommended)**\n"
        "1. Run: `python utils/session.py`\n"
        "2. Follow the prompts to authenticate\n"
        "3. Copy the generated session string\n"
        "4. Add it to .env file as: `SESSION=your_session_string`\n"
        "5. Restart the bot\n\n"
        "**Option 2: Manual Setup**\n"
        "You can generate a session string using the Pyrogram library\n\n"
        "**Current Status:**\n"
    )
    
    if Y:
        session_help += "✅ Userbot is active - Private channel access enabled"
    else:
        session_help += "⚠️ Userbot is not active - Only public channels accessible"
    
    await m.reply_text(session_help)

@X.on_message(F.command("speed"))
async def speed_command(client: C, message: M):
    """Handle /speed command to test bot performance."""
    try:
        # Send initial message
        status_msg = await message.reply_text("🕸️")
        
        # Run speed test
        results = await run_speedtest(client, message)
        
        # Update message with results
        print("🚀 Speed test completed...",results)
        await status_msg.edit_text(results)
        
    except Exception as e:
        logger.error(f"Error during speed test: {e}")
        await message.reply_text("❌ Failed to complete speed test. Please try again later.")


@X.on_message(F.command(["pause", "resume", "cancel"]))
async def batch_control(_: C, m: M) -> None:
    user_id = m.from_user.id
    command = m.command[0]

    if command == "pause":
        if await batch_controller.pause_batch(user_id):
            await m.reply_text("⏸ Batch operation paused. Use /resume to continue.")
        else:
            await m.reply_text("No active batch operation to pause.")
    
    elif command == "resume":
        if await batch_controller.resume_batch(user_id):
            await m.reply_text("▶️ Batch operation resumed.")
        else:
            await m.reply_text("No paused batch operation to resume.")
    
    elif command == "cancel":
        if await batch_controller.cancel_batch(user_id):
            if user_id in progress_info:
                progress_info[user_id]["cancel"] = True
            await m.reply_text("❌ Batch operation cancelled.")
        else:
            await m.reply_text("No active batch operation to cancel.")

@X.on_message(F.text & ~F.command(["start", "batch", "download", "cancel", "join", "session", "speed", "pause", "resume", "help"]))
async def handle_message(_: C, m: M) -> None:
    user_id = m.from_user.id
    if user_id not in user_states or time.time() - user_states[user_id]["timestamp"] > 3600:  # 1 hour timeout
        if user_id in user_states:
            del user_states[user_id]
        return

    step = user_states[user_id]["step"]
    destination = int(user_states[user_id]["chat_id"])
    
    if step == "download":
        # Handle download link
        await process_download_link(m, m.text)
        return
    
    if step == "start":
        chat_id, message_id, link_type = parse_link(m.text)
        if not chat_id or not message_id:
            await m.reply_text("Invalid link. Please check the format.")
            del user_states[user_id]
            return
        if link_type == "private":
            if not Y:
                await m.reply_text("⚠️ This is a private channel link, but userbot is not configured.\n\nTo access private channels:\n1. Use /session to generate a session string\n2. Add it to your .env file as SESSION=...\n3. Restart the bot")
                del user_states[user_id]
                return
            try:
                await Y.get_messages(chat_id, message_id)
            except Exception as e:
                await m.reply_text(f"❌ Userbot cannot access this private channel. Use /join <invite_link>. Error: {e}")
                del user_states[user_id]
                return
        user_states[user_id].update({"step": "count", "cid": chat_id, "sid": message_id, "lt": link_type})
        await m.reply_text("How many messages? (max 100)")
    
    elif step == "count":
        if not m.text.isdigit() or int(m.text) > 300:
            await m.reply_text("Enter a valid number (1-300).")
            return
        count = int(m.text)
        user_states[user_id].update({"step": "process", "num": count})
        
        chat_id, start_msg, link_type = [user_states[user_id][k] for k in ["cid", "sid", "lt"]]
        success_count = 0
        pt = await m.reply_text("⚡")
        
        # Initialize batch operation
        await batch_controller.start_batch(user_id, count, start_msg)
        
        for i in range(count):
            # Check batch state before processing each message
            progress = await batch_controller.get_progress(user_id)
            if not progress or progress.state == BatchState.CANCELLED:
                await pt.edit("Batch operation cancelled.")
                await batch_controller.cleanup_completed(user_id)
                break
            elif progress.state == BatchState.PAUSED:
                await pt.edit(f"⏸ Batch operation paused at {i}/{count}. Use /resume to continue.")
                while True:
                    await asyncio.sleep(1)
                    progress = await batch_controller.get_progress(user_id)
                    if not progress or progress.state == BatchState.CANCELLED:
                        await pt.edit("Batch operation cancelled.")
                        await batch_controller.cleanup_completed(user_id)
                        return
                    elif progress.state == BatchState.RUNNING:
                        await pt.edit(f"▶️ Resuming from {i}/{count}...")
                        break
            
            # Fetch message with error handling
            current_msg_id = start_msg + i
            msg = await fetch_message(X, Y, chat_id, current_msg_id, link_type)
            
            if not msg:
                logger.warning(f"Failed to fetch message {current_msg_id}, skipping...")
                await pt.edit(f"{i+1}/{count}: ❌ Message not found, skipping...")
                
                # Update progress even for skipped messages to keep count accurate
                await batch_controller.update_progress(user_id, current_msg_id)
                await asyncio.sleep(0.5)  # Brief pause to show error
                continue
            
            # Process message with error handling
            try:
                result = await process_message(X, Y, msg, destination, link_type, user_id)
                
                # Update batch controller progress after successful processing
                await batch_controller.update_progress(user_id, current_msg_id)
                
                # Update progress message more frequently for better feedback
                if i % 3 == 0 or i == count - 1:
                    await pt.edit(f"{i+1}/{count}: {result}")
                
                if "Done" in result or "Sent" in result or "Copied" in result:
                    success_count += 1
                
                # Small delay between messages to prevent rate limiting
                if i < count - 1:  # Don't delay after the last message
                    await asyncio.sleep(0.3)
                    
            except Exception as e:
                logger.error(f"Error processing message {current_msg_id}: {e}")
                await pt.edit(f"{i+1}/{count}: ❌ Error - {str(e)[:50]}")
                
                # Update progress even for failed messages
                await batch_controller.update_progress(user_id, current_msg_id)
                await asyncio.sleep(0.5)  # Brief pause to show error
                continue
        
        # Cleanup and completion
        await batch_controller.cleanup_completed(user_id)
        await m.reply_text(f"Batch Completed ✅, {success_count}/{count} messages processed successfully")
        if user_id in user_states:
            del user_states[user_id]

logger.info("✅ Bot has been started successfully!")
# Start the health check server
start_server()
# Run the bot
X.run()

