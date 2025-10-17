"""Progress tracking utilities for downloads and uploads."""

import time
from typing import Dict, Any
from pyrogram.types import Message

class ProgressTracker:
    def __init__(self):
        self.progress_cache = {}
        self.progress_info = {}

    async def update_progress(self, current: int, total: int, user_data: Dict[str, Any]) -> None:
        """Update progress for download/upload with percentage, speed, and ETA."""
        progress_percentage = (current / total) * 100
        progress_step = int(progress_percentage // 10) * 10
        message_id = user_data["message_id"]

        if (message_id not in self.progress_cache or 
            self.progress_cache[message_id] != progress_step or 
            progress_percentage >= 100):
            
            self.progress_cache[message_id] = progress_step
            completed_blocks = int(progress_percentage / 10)
            progress_bar = "🔥" * completed_blocks + "🪵" * (10 - completed_blocks)

            elapsed_time = time.time() - user_data["start_time"]
            speed = (current / elapsed_time) / (1024 * 1024) if elapsed_time > 0 else 0
            eta = time.strftime("%M:%S", time.gmtime((total - current) / (speed * 1024 * 1024))) if speed > 0 else "00:00"

            action = "Downloading" if user_data["phase"] == "download" else "Uploading"
            file_info = user_data.get("file_data", {})
            action_message = (
                f"**{action} - {file_info.get('file_name', '')} ({file_info.get('file_size', 0):.2f} MB)**"
                if file_info else f"**{action}.. Hang tight**"
            )

            message_text = (
                f"{action_message}\n\n{progress_bar}\n\n"
                f"📊 **Completed**: {progress_percentage:.2f}%\n"
                f"🚀 **Speed**: {speed:.2f} MB/sec\n"
                f"⏳ **ETA**: {eta}\n\n"
                f"**Powered by @unknown_5145**"
            )

            try:
                await user_data["client"].edit_message_text(
                    user_data["chat_id"], 
                    user_data["message_id"], 
                    message_text
                )
            except Exception as e:
                print(f"Failed to update progress: {e}")

            if progress_percentage >= 100:
                self.progress_cache.pop(message_id, None)

    def get_progress_info(self, user_id: int) -> Dict[str, Any]:
        """Get progress information for a specific user."""
        return self.progress_info.get(user_id, {})

    def set_progress_info(self, user_id: int, info: Dict[str, Any]) -> None:
        """Set progress information for a specific user."""
        self.progress_info[user_id] = info

    def clear_progress_info(self, user_id: int) -> None:
        """Clear progress information for a specific user."""
        self.progress_info.pop(user_id, None)

# Create a global instance of the progress tracker
progress_tracker = ProgressTracker()