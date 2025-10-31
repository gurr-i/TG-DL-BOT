"""Enhanced progress tracking utilities with better performance."""

import time
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ProgressState:
    """Progress state for a specific operation."""
    current: int = 0
    total: int = 0
    start_time: float = 0
    last_update: float = 0
    last_percentage: int = -1
    speed_samples: list = None
    
    def __post_init__(self):
        if self.speed_samples is None:
            self.speed_samples = []

class EnhancedProgressTracker:
    """High-performance progress tracker with advanced features."""
    
    def __init__(self):
        self.progress_states: Dict[int, ProgressState] = {}
        self.update_lock = asyncio.Lock()
        self.min_update_interval = 3.0  # Minimum seconds between updates (optimized from 1.0)
        
    async def start_progress(self, message_id: int, total: int) -> None:
        """Initialize progress tracking for a message."""
        async with self.update_lock:
            self.progress_states[message_id] = ProgressState(
                total=total,
                start_time=time.time()
            )
    
    async def update_progress(self, current: int, total: int, user_data: Dict[str, Any]) -> None:
        """Enhanced progress update with intelligent throttling."""
        message_id = user_data.get("message_id")
        if not message_id:
            return
            
        current_time = time.time()
        progress_percentage = int((current / total) * 100) if total > 0 else 0
        
        # Get or create progress state
        if message_id not in self.progress_states:
            self.progress_states[message_id] = ProgressState(
                total=total,
                start_time=current_time
            )
        
        state = self.progress_states[message_id]
        state.current = current
        
        # Optimized throttling - update every 5% or 3 seconds for better performance
        should_update = (
            (progress_percentage != state.last_percentage and progress_percentage % 5 == 0) or
            current_time - state.last_update >= self.min_update_interval or
            progress_percentage >= 100 or
            current == 0  # Always update on start
        )
        
        if not should_update:
            return
            
        state.last_update = current_time
        state.last_percentage = progress_percentage
        
        # Calculate speed with smoothing
        elapsed = current_time - state.start_time
        if elapsed > 0:
            current_speed = current / elapsed
            state.speed_samples.append(current_speed)
            
            # Keep only recent samples for smoothing
            if len(state.speed_samples) > 10:
                state.speed_samples = state.speed_samples[-10:]
            
            # Use average of recent samples
            avg_speed = sum(state.speed_samples) / len(state.speed_samples)
            speed_mbps = avg_speed / (1024 * 1024)
        else:
            speed_mbps = 0
        
        # Calculate ETA
        if speed_mbps > 0 and current < total:
            remaining_mb = (total - current) / (1024 * 1024)
            eta_seconds = remaining_mb / speed_mbps
            eta = self._format_time(eta_seconds)
        else:
            eta = "calculating..."
        
        # Create enhanced progress bar
        progress_bar = self._create_progress_bar(progress_percentage)
        
        # Format message
        action = "📥 Downloading" if user_data.get("phase") == "download" else "📤 Uploading"
        file_info = user_data.get("file_data", {})
        
        if file_info:
            file_name = file_info.get('file_name', 'Unknown')[:25]
            file_size_mb = file_info.get('file_size', total / (1024 * 1024))
            header = f"{action} **{file_name}**"
        else:
            file_size_mb = total / (1024 * 1024)
            header = f"{action} content"
        
        message_text = (
            f"{header}\n\n"
            f"{progress_bar}\n\n"
            f"📊 **Progress**: {progress_percentage}%\n"
            f"🚀 **Speed**: {speed_mbps:.1f} MB/s\n"
            f"⏱️ **ETA**: {eta}\n"
            f"📦 **Size**: {current/(1024*1024):.1f}/{file_size_mb:.1f} MB\n\n"
            f"*High-Performance Telegram Saver*"
        )
        
        try:
            await user_data["client"].edit_message_text(
                user_data["chat_id"],
                user_data["message_id"],
                message_text
            )
        except Exception as e:
            # Ignore rate limit and minor errors
            if "too many requests" not in str(e).lower():
                pass  # Silent fail for progress updates
    
    def _create_progress_bar(self, percentage: int, length: int = 20) -> str:
        """Create a visual progress bar."""
        filled = int(percentage / 100 * length)
        bar = "🟩" * filled + "⬜" * (length - filled)
        return f"{bar} {percentage}%"
    
    def _format_time(self, seconds: float) -> str:
        """Format time duration in human readable format."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds//60)}m {int(seconds%60)}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    async def finish_progress(self, message_id: int) -> None:
        """Clean up progress tracking for completed operation."""
        async with self.update_lock:
            self.progress_states.pop(message_id, None)
    
    def get_progress_info(self, message_id: int) -> Optional[ProgressState]:
        """Get current progress state."""
        return self.progress_states.get(message_id)

# Global instance
progress_tracker = EnhancedProgressTracker()