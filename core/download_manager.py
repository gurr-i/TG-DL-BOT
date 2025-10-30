"""
Download manager for parallel and optimized downloads.
Handles concurrent downloads with semaphore-based rate limiting.
"""

import asyncio
import logging
from typing import Optional, List, Tuple, Any, Callable
from dataclasses import dataclass
from pyrogram import Client
from pyrogram.types import Message

from .performance import performance_optimizer

logger = logging.getLogger(__name__)


@dataclass
class DownloadTask:
    """Represents a download task."""
    chat_id: Any
    message_id: int
    link_type: str
    destination: int
    user_id: int


class DownloadManager:
    """Manages parallel downloads with rate limiting."""
    
    def __init__(self, max_concurrent: int = 3):
        """
        Initialize download manager.
        
        Args:
            max_concurrent: Maximum number of concurrent downloads (default: 3)
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_tasks: List[asyncio.Task] = []
        logger.info(f"[DOWNLOAD_MANAGER] Initialized with max_concurrent={max_concurrent}")
    
    async def download_single(
        self,
        bot_client: Client,
        userbot_client: Optional[Client],
        task: DownloadTask,
        fetch_func: Callable,
        process_func: Callable
    ) -> Tuple[int, str]:
        """
        Download a single message with semaphore control.
        
        Returns:
            Tuple of (message_id, result_string)
        """
        task_coro = asyncio.current_task()
        async with self.semaphore:
            self.active_tasks.append(task_coro)
            try:
                logger.debug(f"[DOWNLOAD_MANAGER] Starting download for message {task.message_id}")
                
                # Fetch message
                msg = await fetch_func(
                    bot_client, 
                    userbot_client, 
                    task.chat_id, 
                    task.message_id, 
                    task.link_type
                )
                
                if not msg:
                    logger.warning(f"[DOWNLOAD_MANAGER] Message {task.message_id} not found")
                    return task.message_id, "[ERROR] Message not found"
                
                # Process message
                result = await process_func(
                    bot_client,
                    userbot_client,
                    msg,
                    task.destination,
                    task.link_type,
                    task.user_id
                )
                
                logger.debug(f"[DOWNLOAD_MANAGER] Completed message {task.message_id}: {result}")
                return task.message_id, result
                
            except Exception as e:
                logger.error(f"[DOWNLOAD_MANAGER] Error downloading message {task.message_id}: {e}")
                performance_optimizer.record_failure()
                return task.message_id, f"[ERROR] {str(e)[:50]}"
            finally:
                self.active_tasks.remove(task_coro)
    
    async def download_batch_parallel(
        self,
        bot_client: Client,
        userbot_client: Optional[Client],
        tasks: List[DownloadTask],
        fetch_func: Callable,
        process_func: Callable,
        progress_callback: Optional[Callable] = None
    ) -> List[Tuple[int, str]]:
        """
        Download multiple messages in parallel with rate limiting.
        
        Args:
            bot_client: Bot client instance
            userbot_client: Optional userbot client
            tasks: List of download tasks
            fetch_func: Function to fetch messages
            process_func: Function to process messages
            progress_callback: Optional callback for progress updates
        
        Returns:
            List of (message_id, result) tuples
        """
        logger.info(f"[DOWNLOAD_MANAGER] Starting parallel batch download: {len(tasks)} tasks")
        
        results = []
        completed = 0
        total = len(tasks)
        
        # Create coroutines for all tasks
        download_coroutines = [
            self.download_single(
                bot_client,
                userbot_client,
                task,
                fetch_func,
                process_func
            )
            for task in tasks
        ]
        
        # Process with progress tracking
        for coro in asyncio.as_completed(download_coroutines):
            try:
                result = await coro
                results.append(result)
                completed += 1
                
                # Call progress callback if provided
                if progress_callback:
                    try:
                        await progress_callback(completed, total)
                    except Exception as e:
                        logger.debug(f"Progress callback error: {e}")
                
                logger.debug(f"[DOWNLOAD_MANAGER] Progress: {completed}/{total}")
                
            except Exception as e:
                logger.error(f"[DOWNLOAD_MANAGER] Task failed: {e}")
                completed += 1
        
        logger.info(f"[DOWNLOAD_MANAGER] Batch download completed: {len(results)}/{total} successful")
        return results
    
    async def download_batch_sequential(
        self,
        bot_client: Client,
        userbot_client: Optional[Client],
        tasks: List[DownloadTask],
        fetch_func: Callable,
        process_func: Callable,
        progress_callback: Optional[Callable] = None,
        delay: float = 1.0
    ) -> List[Tuple[int, str]]:
        """
        Download messages sequentially with delay between each.
        Useful for rate-limited scenarios.
        
        Args:
            delay: Delay in seconds between downloads
        """
        logger.info(f"[DOWNLOAD_MANAGER] Starting sequential batch download: {len(tasks)} tasks")
        
        results = []
        
        for idx, task in enumerate(tasks, 1):
            try:
                result = await self.download_single(
                    bot_client,
                    userbot_client,
                    task,
                    fetch_func,
                    process_func
                )
                results.append(result)
                
                # Call progress callback
                if progress_callback:
                    try:
                        await progress_callback(idx, len(tasks))
                    except Exception as e:
                        logger.debug(f"Progress callback error: {e}")
                
                # Add delay between downloads (except for last one)
                if idx < len(tasks):
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                logger.error(f"[DOWNLOAD_MANAGER] Sequential task failed: {e}")
                results.append((task.message_id, f"[ERROR] {str(e)[:50]}"))
        
        logger.info(f"[DOWNLOAD_MANAGER] Sequential batch completed: {len(results)} tasks")
        return results
    
    def get_stats(self) -> dict:
        """Get download manager statistics."""
        return {
            "max_concurrent": self.max_concurrent,
            "active_tasks": len(self.active_tasks),
            "available_slots": self.semaphore._value
        }


# Global instance with 3 concurrent downloads (safe for most scenarios)
download_manager = DownloadManager(max_concurrent=3)
