# Product Overview

## Telegram Message Saver Bot

A high-performance Telegram bot built with Pyrogram that downloads and forwards messages, media, and files from both public and private channels. The bot features multi-threaded downloads, batch processing (up to 300 messages), real-time progress tracking, and robust error handling with exponential backoff retry logic.

## Key Capabilities

- **Message Processing**: Single message downloads and batch operations
- **Channel Access**: Supports both public channels and private channels via userbot session
- **Media Support**: All Telegram media types (photos, videos, documents, audio, stickers)
- **Performance**: Multi-threaded downloads with concurrent queue processing
- **Reliability**: Session crash protection, automatic retries, and guaranteed file cleanup
- **User Control**: Pause/resume/cancel operations with persistent state management

## Target Users

Telegram users who need to save content from channels they have access to, particularly useful for archiving, content curation, and offline access to channel materials.