"""
Telegram Message Saver Bot - Core Module

High-performance Telegram bot for downloading and forwarding messages
from public and private channels with advanced features.
"""

__version__ = "2.0.0"
__author__ = "Telegram Saver Bot Team"

# Core components
from .config import config
from .batch import BatchController, BatchState

__all__ = [
    "config",
    "BatchController", 
    "BatchState",
]