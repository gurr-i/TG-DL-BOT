
# Telegram Message Saver Bot

## Overview

A powerful Telegram bot built with Pyrogram that can save and forward messages, media, and files from both public and private channels. The bot features high-speed downloads with multi-threading, detailed progress tracking, secure session management, and robust error handling.

## 🎯 Core Features

### 📥 Message Downloading

- **Single Message Download**: Download individual messages using `/download <link>`
- **Batch Processing**: Save up to 300 messages in one operation
- **Multi-threaded Downloads**: Concurrent downloading for improved performance
- **Retry Logic**: Automatic retry with exponential backoff (1s, 2s, 4s) for network resilience
- **Queue Management**: Separate download and upload queues for efficient processing

### 📤 Message Forwarding

- **Automatic Upload**: Downloaded content is automatically forwarded to the user
- **Retry Mechanism**: Multiple upload attempts with intelligent error handling
- **Session Crash Protection**: Handles Pyrogram session crashes during large file uploads
- **Progress Tracking**: Real-time progress bars with speed, ETA, and file information

### 🔐 Channel Access

- **Public Channels**: Full support without authentication
- **Private Channels**: Access via userbot session
- **Group Topics**: Supports group messages with topic IDs
- **Channel Joining**: `/join <invite_link>` to join private channels
- **Auto-detection**: Automatically detects link type (public/private)

### 📊 Progress & Monitoring

- **Real-time Progress Bars**: Shows download/upload progress with visual indicators
- **Speed Metrics**: Displays current transfer speed
- **ETA Calculation**: Estimates time remaining for operations
- **File Information**: Shows file name and size during transfers
- **Detailed Logging**: Comprehensive logging for debugging and monitoring

### ⚡ Performance Features

- **High-speed Transfers**: Optimized for maximum throughput
- **Multi-threading**: Concurrent operations for better performance
- **Speed Testing**: Built-in `/speed` command to measure bot performance
- **Rate Limiting**: Prevents abuse with 300 message batch limit
- **Cooldown System**: Built-in delays to prevent rate limiting

### 🛡️ Error Handling & Reliability

- **Network Resilience**: Exponential backoff for transient network issues
- **Session Crash Recovery**: Handles Pyrogram crashes (OSError, AttributeError, TimeoutError)
- **Automatic Cleanup**: Guaranteed file cleanup via finally blocks
- **Memory Leak Prevention**: Proper resource management and cleanup
- **Graceful Degradation**: Clear error messages and fallback behavior

### 🎮 Control Features

- **Pause/Resume**: Control batch operations with `/pause` and `/resume`
- **Cancel Operations**: Stop ongoing downloads/uploads with `/cancel`
- **State Management**: Persistent user state tracking across operations
- **Queue Visibility**: Monitor active download and upload queues

### 📁 Media Support

- **Photos**: Full support for photo messages
- **Videos**: Video file downloads and uploads
- **Documents**: All document types including PDFs
- **Audio Files**: Music and voice messages
- **Stickers**: Animated and static stickers
- **Video Notes**: Circular video messages
- **Multiple Media**: Messages with multiple attachments

## 📋 Available Commands

| Command       | Description              | Usage Example                          |
| ------------- | ------------------------ | -------------------------------------- |
| `/start`    | Initialize the bot       | `/start`                             |
| `/download` | Download single message  | `/download https://t.me/channel/123` |
| `/batch`    | Start batch processing   | `/batch` → follow prompts           |
| `/join`     | Join private channel     | `/join https://t.me/joinchat/...`    |
| `/session`  | Setup userbot guide      | `/session`                           |
| `/pause`    | Pause batch operation    | `/pause`                             |
| `/resume`   | Resume paused batch      | `/resume`                            |
| `/cancel`   | Cancel ongoing operation | `/cancel`                            |
| `/speed`    | Run speed test           | `/speed`                             |
| `/help`     | Show help message        | `/help`                              |

## 🏗️ Project Structure

```
.
├── core/
│   ├── __init__.py
│   ├── batch.py          # Batch processing controller with state management
│   ├── bot.py            # Main bot logic and command handlers
│   ├── config.py         # Configuration management and validation
│   ├── server.py         # Health check web server (port 3000)
│   ├── session_string_generator.py  # Session generation utilities
│   └── speed_test.py     # Speed testing functionality
├── utils/
│   ├── __init__.py
│   ├── progress.py       # Progress tracking utilities
│   └── session.py        # Session validation utilities
├── bot_types/            # Type definitions and data classes
│   └── __init__.py       # MessageInfo, UserState, ProgressInfo
├── .env                  # Environment variables (credentials)
├── .env.example          # Example environment configuration
├── requirements.txt      # Python dependencies
├── README.md            # User documentation
└── replit.md            # Development documentation
```

## 🔧 Technical Architecture

### Technologies

- **Language**: Python 3.11
- **Framework**: Pyrogram 2.1.32 (Telegram MTProto API)
- **Web Server**: aiohttp (health check on port 3000)
- **Database**: SQLite (session storage)
- **Concurrency**: asyncio with async/await patterns
- **Environment**: Replit (Linux + Nix)

### Key Components

#### Bot Client (X)

- Main bot instance for user interactions
- Handles commands and user messages
- Manages user state and conversations

#### Userbot Client (Y)

- Optional client for private channel access
- Enables joining and fetching from private channels
- Session-based authentication

#### Queue System

- **Download Queue**: Manages pending downloads
- **Upload Queue**: Handles file uploads
- **Task Workers**: Concurrent queue processors

#### State Management

- **User States**: Tracks conversation flow per user
- **Batch Controller**: Manages batch operation state
- **Progress Info**: Tracks transfer progress and retry counts

### Error Handling Strategy

1. **Network Errors**: Exponential backoff retry (3 attempts)
2. **Session Crashes**: Specific handling for Pyrogram crashes
3. **File Cleanup**: Always executed via finally blocks
4. **User Feedback**: Clear error messages for all failure scenarios
5. **Logging**: Comprehensive logging for debugging

## 🚀 Setup & Configuration

### Environment Variables (.env)

```env
API_ID=your_api_id           # From my.telegram.org
API_HASH=your_api_hash       # From my.telegram.org
BOT_TOKEN=your_bot_token     # From @BotFather
SESSION=your_session_string  # Optional, for private channels
```

### Running the Bot

The bot runs automatically via Replit workflow:

```bash
cd /home/runner/$REPL_SLUG && PYTHONPATH=/home/runner/$REPL_SLUG python core/bot.py
```

### Session String Generation

For private channel access, generate a session string:

```bash
python utils/session.py
```

## 📈 Recent Updates & Bug Fixes

### October 2025 Updates

- ✅ **Import Issues Fixed**: Changed to absolute imports with PYTHONPATH
- ✅ **Port Conflicts Resolved**: Health check server on port 3000
- ✅ **Session Management**: Graceful handling without session string
- ✅ **Batch Processing**: Fixed stopping/missing messages bug
- ✅ **Group Support**: Added support for group topic messages
- ✅ **File Cleanup**: Eliminated orphaned temporary files
- ✅ **Network Resilience**: Exponential backoff for retries
- ✅ **Session Crash Fix**: Handles Pyrogram crashes during uploads
- ✅ **Memory Management**: Proper cleanup prevents memory leaks
- ✅ **Progress Tracking**: Every message logged (success/failed/skipped)
- ✅ **Error Messages**: User-friendly feedback for all scenarios

### Performance Improvements

- Multi-threaded downloads for faster processing
- Optimized queue management
- Reduced server load with smart retry delays
- Better memory utilization with proper cleanup

## 🎯 Usage Workflows

### Single Message Download

1. Send `/download https://t.me/channel/messageid`
2. Bot fetches and downloads the message
3. Progress bar shows download status
4. File is uploaded to your chat
5. Temporary file is cleaned up

### Batch Processing

1. Send `/batch`
2. Send the first message link
3. Enter number of messages (max 300)
4. Bot processes messages sequentially
5. Progress updates for each message
6. Use `/pause`, `/resume`, or `/cancel` as needed

### Private Channel Access

1. Send `/session` to see setup guide
2. Generate session string using `utils/session.py`
3. Add session to `.env` file
4. Restart bot
5. Use `/join <invite_link>` to join channels

## 🔍 Link Format Support

| Format          | Type                       | Example                         |
| --------------- | -------------------------- | ------------------------------- |
| Public Channel  | `t.me/username/id`       | `https://t.me/channel/123`    |
| Private Channel | `t.me/c/chatid/id`       | `https://t.me/c/123456/789`   |
| Group Topic     | `t.me/c/chatid/topic/id` | `https://t.me/c/123456/2/789` |

## 💡 Tips & Best Practices

- **Session Security**: Keep SESSION string private and secure
- **Rate Limiting**: Use smaller batches for faster processing
- **Private Channels**: Ensure bot/user is member before downloading
- **Error Recovery**: Check logs for detailed error information
- **Speed Testing**: Use `/speed` to diagnose performance issues
- **File Management**: Bot automatically cleans up temporary files
- **Network Issues**: Built-in retry handles most transient failures

## 🛠️ Troubleshooting

### Common Issues

**Session Expired**

- Generate new session: `python utils/session.py`
- Update `.env` with new SESSION string
- Restart the bot

**Slow Downloads**

- Check internet connection
- Run `/speed` to measure performance
- Try smaller batch sizes
- Check Replit resource limits

**Private Channel Access Denied**

- Verify SESSION is configured
- Ensure userbot is channel member
- Use `/join` to join the channel
- Check invite link validity

**Upload Failures**

- Check file size limits (2GB for bots)
- Verify network stability
- Review error logs for details
- Bot will retry automatically (3 attempts)

**Batch Stops/Skips Messages**

- Check logs for specific errors
- Network issues trigger automatic retries
- Use `/cancel` and restart if needed
- Reduce batch size for stability

## 📊 Performance Metrics

- **Max Batch Size**: 300 messages
- **Retry Attempts**: 3 per operation
- **Backoff Strategy**: Exponential (1s, 2s, 4s)
- **Queue Workers**: Concurrent processing
- **Health Check**: Port 3000
- **File Cleanup**: Guaranteed via finally blocks

## 🔒 Security Features

- **Environment Variables**: Credentials stored securely in .env
- **Session Validation**: Automatic session health checks
- **Database Locking**: Prevents session corruption
- **Error Sanitization**: No sensitive data in error messages
- **Cleanup Guarantee**: Files always removed after processing

## 📝 Development Notes

### Architecture Decisions

- **Async/Await**: All I/O operations are asynchronous
- **Queue Pattern**: Separation of concerns for downloads/uploads
- **State Machine**: User conversation flow management
- **Retry Logic**: Network resilience with exponential backoff
- **Resource Cleanup**: Finally blocks ensure no orphaned files

### Code Organization

- **core/**: Main application logic
- **utils/**: Reusable utility functions
- **bot_types/**: Type definitions and data classes
- **Modular Design**: Separation of concerns for maintainability

## 🤝 Support & Contact

For issues, questions, or feature requests:

- Telegram: @unknown_5145
- Check logs for detailed error information
- Review this documentation for common solutions

## 📜 Version History

**v2.0 (October 2025)**

- Complete rewrite with improved architecture
- Batch processing with pause/resume/cancel
- Session crash protection
- Guaranteed file cleanup
- Enhanced error handling

**v1.0 (Initial Release)**

- Basic message downloading
- Public/private channel support
- Session string authentication

---

**Last Updated**: October 18, 2025
**Status**: Production Ready ✅
**Replit Deployment**: Fully Operational
