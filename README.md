# Telegram Message Saver Bot

⚡ A powerful Telegram bot that can save and forward messages, media, and files from both public and private channels. Built with Pyrogram, this bot features:

- 🚀 High-speed downloads with multi-threading
- 📊 Detailed progress tracking with speed tests
- 🔒 Secure session management
- ⏱️ Rate limiting to prevent abuse

## Features ✨

- **Media Support**: Save various types of media including photos, videos, documents, stickers, voice messages, and more
- **Progress Tracking**: Real-time progress bars with speed and ETA for downloads/uploads
- **Speed Testing**: Built-in speed test to measure download/upload performance
- **Session Management**: Automatic session validation and renewal
- **Batch Processing**: Process multiple messages at once with a single command
- **Private Channel Access**: Join and save content from private channels
- **Rate Limiting**: Built-in rate limiting to prevent abuse
- **Cancel Support**: Cancel ongoing downloads/uploads

## Prerequisites

1. Python 3.7 or higher
2. Telegram API credentials (API ID and Hash)
3. Bot Token from [@BotFather](https://t.me/BotFather)
4. Session string for userbot functionality (optional)

## Installation

1. Clone the repository or download the source code
2. Install required packages:

   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your credentials:

   ```env
   API_ID=your_api_id
   API_HASH=your_api_hash
   BOT_TOKEN=your_bot_token
   SESSION=your_session_string  # Optional
   ```
4. Start script:

   `python core/bot.py`

## Generating Session String

If you want to access private channels, you'll need a session string. Run:

```bash
python utils/session.py
```

Follow the prompts to generate your session string.

## Usage

### Commands

- `/start` - Start the bot
- `/batch` - Start batch processing messages
- `/join` - Join a private channel
- `/cancel` - Cancel ongoing operations
- `/speed` - Run speed test.

### Batch Processing

1. Start a batch process with `/batch`
2. Send the link to the first message
3. Specify how many messages to process (max 300)

### Private Channel Access

1. Use `/join <invite_link>` to join private channels
2. The userbot must be a member of the private channel to access its content

## Features in Detail 🔍

### ⚡ Speed Testing

- Built-in speed test command `/speed`
- Measures download/upload speeds to Telegram servers
- Helps identify connection issues
- Displays network latency and throughput

### 🔒 Session Management

- Automatic session validation on startup
- Session renewal notifications
- Step-by-step guide for generating new sessions
- Session backup recommendations

### 📊 Progress Tracking

- Real-time progress bar
- Download/Upload speed
- Estimated time remaining
- File size and name display

### Rate Limiting

- Maximum 300 messages per batch
- Built-in cooldown system
- Prevents abuse and server overload

### Media Support

- Photos and Videos
- Documents and Files
- Stickers
- Voice Messages
- Video Notes
- Audio Files

## Error Handling ⚠️

The bot includes comprehensive error handling for:

- Invalid links
- Inaccessible channels
- Download/Upload failures
- Rate limit exceeded
- Session expiration

## Troubleshooting 🛠️

### Common Issues

1. **Session Expired**

   - Run `python util/session.py` to generate new session
   - Update .env file with new session string
2. **Slow Downloads**

   - Check internet connection
   - Use `/speed` to measure performance
   - Try smaller batch sizes
3. **Private Channel Access**

   - Ensure bot/user is member of channel
   - Verify invite link is valid
   - Check channel admin permissions

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.
