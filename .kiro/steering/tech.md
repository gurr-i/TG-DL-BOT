# Technology Stack

## Core Technologies

- **Language**: Python 3.11+
- **Framework**: Pyrogram 2.0.106+ (Telegram MTProto API)
- **Web Server**: aiohttp (health check server on port 3000)
- **Database**: SQLite (session storage)
- **Concurrency**: asyncio with async/await patterns
- **Performance**: uvloop for enhanced async performance (optional)

## Key Dependencies

```
pyrogram>=2.0.106      # Telegram API client
tgcrypto>=1.2.5        # Cryptographic functions
python-dotenv>=1.0.0   # Environment variable management
aiohttp>=3.8.0         # Async HTTP server
aiofiles>=23.0.0       # Async file operations
speedtest-cli>=2.1.3   # Network speed testing
uvloop>=0.19.0         # Performance optimization
```

## Build & Development Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Generate session string (for private channels)
python utils/session.py

# Create environment configuration
cp .env.example .env
# Edit .env with your credentials
```

### Running
```bash
# Start the bot locally
python core/bot.py

# Run speed test
python core/speed_test.py
```

### Deployment
```bash
# Render.com deployment (configured in render.yaml)
# Heroku deployment (configured in Procfile)
```

## Configuration

Environment variables are managed through `.env` file:
- `API_ID`: Telegram API ID from my.telegram.org
- `API_HASH`: Telegram API Hash
- `BOT_TOKEN`: Bot token from @BotFather
- `SESSION`: Optional session string for private channel access