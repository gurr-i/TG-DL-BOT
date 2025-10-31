import asyncio
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class BatchState(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

@dataclass
class BatchProgress:
    current: int
    total: int
    state: BatchState
    last_processed_id: int
    start_time: datetime
    chat_id: Any
    start_message_id: int
    link_type: str
    destination: int
    pause_time: Optional[datetime] = None

class BatchController:
    """Manages batch processing operations, including starting, pausing, resuming, and tracking progress."""
    def __init__(self):
        self.batch_operations: Dict[int, BatchProgress] = {}
        self._lock = asyncio.Lock()
    
    async def start_batch(self, user_id: int, total_messages: int, start_message_id: int, chat_id: Any, link_type: str, destination: int) -> bool:
        """Initialize a new batch operation for a user."""
        async with self._lock:
            # Auto-cleanup completed/cancelled batches
            if user_id in self.batch_operations:
                existing = self.batch_operations[user_id]
                if existing.state in [BatchState.COMPLETED, BatchState.CANCELLED]:
                    del self.batch_operations[user_id]
                else:
                    return False  # Active batch exists
            
            self.batch_operations[user_id] = BatchProgress(
                current=0,
                total=total_messages,
                state=BatchState.RUNNING,
                last_processed_id=start_message_id - 1,  # Will be incremented before first process
                start_time=datetime.now(),
                chat_id=chat_id,
                start_message_id=start_message_id,
                link_type=link_type,
                destination=destination
            )
            return True
    
    async def pause_batch(self, user_id: int) -> bool:
        """Pause a running batch operation."""
        async with self._lock:
            if user_id not in self.batch_operations:
                return False
            
            progress = self.batch_operations[user_id]
            if progress.state == BatchState.RUNNING:
                progress.state = BatchState.PAUSED
                progress.pause_time = datetime.now()
                return True
            return False
    
    async def resume_batch(self, user_id: int) -> bool:
        """Resume a paused batch operation."""
        async with self._lock:
            if user_id not in self.batch_operations:
                return False
            
            progress = self.batch_operations[user_id]
            if progress.state == BatchState.PAUSED:
                progress.state = BatchState.RUNNING
                progress.pause_time = None
                return True
            return False
    
    async def cancel_batch(self, user_id: int) -> bool:
        """Cancel a batch operation."""
        async with self._lock:
            if user_id not in self.batch_operations:
                return False
            
            progress = self.batch_operations[user_id]
            if progress.state in [BatchState.RUNNING, BatchState.PAUSED]:
                progress.state = BatchState.CANCELLED
                return True
            return False
    
    async def update_progress(self, user_id: int, message_id: int) -> Optional[BatchProgress]:
        """Update the progress of a batch operation."""
        async with self._lock:
            if user_id not in self.batch_operations:
                return None
            
            progress = self.batch_operations[user_id]
            if progress.state == BatchState.RUNNING:
                progress.current += 1
                progress.last_processed_id = message_id
                
                if progress.current >= progress.total:
                    progress.state = BatchState.COMPLETED
                
            return progress
    
    async def get_progress(self, user_id: int) -> Optional[BatchProgress]:
        """Get the current progress of a batch operation."""
        async with self._lock:
            return self.batch_operations.get(user_id)
    
    async def cleanup_completed(self, user_id: int) -> None:
        """Remove completed or cancelled batch operations."""
        async with self._lock:
            if user_id in self.batch_operations:
                progress = self.batch_operations[user_id]
                if progress.state in [BatchState.COMPLETED, BatchState.CANCELLED]:
                    del self.batch_operations[user_id]