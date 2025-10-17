# Telegram Message Saver Bot

## Overview
A powerful Telegram bot built with Pyrogram that can save and forward messages, media, and files from both public and private channels. The bot features high-speed downloads with multi-threading, detailed progress tracking, and secure session management.

## Recent Changes (Oct 17, 2025)
- ✅ Fixed import issues (changed relative imports to absolute imports with PYTHONPATH)
- ✅ Added new `/download` command for single message downloads
- ✅ Added `/session` command to guide users on setting up userbot
- ✅ Fixed port conflicts (health check server now on port 3000)
- ✅ Resolved session database lock issues
- ✅ Improved session handling - bot now runs in public-only mode without session string
- ✅ Added graceful fallbacks with clear error messages when userbot is unavailable
- ✅ Set up Replit workflow with proper Python path configuration
- ✅ Bot is now fully operational for both public and private channels

## Project Structure
```
.
├── core/
│   ├── __init__.py
│   ├── batch.py          # Batch processing controller
│   ├── bot.py            # Main bot logic and command handlers
│   ├── config.py         # Configuration management
│   ├── server.py         # Health check web server
│   ├── session_string_generator.py  # Session generation utilities
│   └── speed_test.py     # Speed testing functionality
├── utils/
│   ├── __init__.py
│   ├── progress.py       # Progress tracking utilities
│   └── session.py        # Session validation utilities
├── bot_types/            # Type definitions
├── .env                  # Environment variables (credentials)
├── requirements.txt      # Python dependencies
└── README.md            # Project documentation
```

## Features
- 📥 **Single Download**: Use `/download <link>` to save a single message/media
- 📦 **Batch Processing**: Save multiple messages at once (up to 300)
- 🚀 **High-speed downloads**: Multi-threaded with retry logic
- 📊 **Progress tracking**: Real-time progress bars with speed and ETA
- 🔒 **Session management**: Automatic session validation and renewal
- 🔐 **Private channel support**: Join and save content from private channels
- ⏸️ **Pause/Resume**: Control batch operations with pause/resume
- 🚫 **Cancel support**: Cancel ongoing downloads/uploads
- ⚡ **Speed test**: Built-in speed test to measure performance

## Available Commands
- `/start` - Start the bot
- `/download <link>` - Download a single message/media from a link
- `/batch` - Start batch processing messages
- `/join <invite_link>` - Join a private channel (requires userbot)
- `/session` - Set up userbot for private channel access
- `/pause` - Pause ongoing batch operation
- `/resume` - Resume paused batch operation
- `/cancel` - Cancel ongoing operations
- `/speed` - Check bot speed
- `/help` - Show help message

## Configuration
Environment variables in `.env`:
- `API_ID` - Telegram API ID
- `API_HASH` - Telegram API Hash
- `BOT_TOKEN` - Bot token from @BotFather
- `SESSION` - Session string for userbot functionality (optional)

## Technical Details
- **Language**: Python 3.11
- **Framework**: Pyrogram 2.0.106
- **Web Server**: aiohttp (health check on port 3000)
- **Database**: SQLite (for sessions)
- **Architecture**: Async/await with asyncio

## Running the Bot
The bot runs automatically via Replit workflow:
```bash
cd /home/runner/$REPL_SLUG && PYTHONPATH=/home/runner/$REPL_SLUG python core/bot.py
```

## User Preferences
- Bot is configured for console output (not a web frontend)
- Health check server runs on port 3000 (localhost)
- Main bot logic runs on Telegram's API
- Bot works for public channels without session string
- Private channel access requires SESSION configuration
