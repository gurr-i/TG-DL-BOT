# Project Structure & Architecture

## Directory Organization

```
.
├── core/                    # Core bot functionality
│   ├── bot.py              # Main bot logic and command handlers
│   ├── batch.py            # Batch processing with state management
│   ├── config.py           # Configuration management and validation
│   ├── server.py           # Health check web server (port 3000)
│   ├── session_string_generator.py  # Session generation utilities
│   └── speed_test.py       # Network speed testing functionality
├── utils/                   # Utility modules
│   ├── progress.py         # Progress tracking for downloads/uploads
│   └── session.py          # Session validation and generation
├── bot_types/              # Type definitions and data classes
│   └── __init__.py         # MessageInfo, UserState, ProgressInfo
├── attached_assets/        # Runtime file storage
└── .env                    # Environment configuration
```

## Architecture Patterns

### Import Strategy
- Use absolute imports with PYTHONPATH configuration
- Local imports follow pattern: `from .module import Class`
- Third-party imports grouped separately from local imports

### Async/Await Patterns
- All I/O operations use async/await
- Concurrent processing with asyncio queues
- ThreadPoolExecutor for CPU-bound operations

### Error Handling
- Exponential backoff retry logic (1s, 2s, 4s)
- Session crash protection with graceful recovery
- Guaranteed resource cleanup using finally blocks
- User-friendly error messages without exposing internals

### State Management
- User conversation state tracked in memory
- Batch operations use enum-based state machine
- Progress tracking with real-time updates

### Configuration Management
- Environment variables loaded via python-dotenv
- Centralized config validation in `core/config.py`
- Graceful degradation when optional configs missing

## Code Conventions

### Class Structure
- Use dataclasses for simple data containers
- Enum classes for state definitions
- Async context managers for resource management

### Logging
- Structured logging with timestamps and levels
- INFO level for user actions and progress
- ERROR level for failures requiring attention

### File Operations
- Temporary files always cleaned up in finally blocks
- Async file operations using aiofiles
- Progress callbacks for large file transfers