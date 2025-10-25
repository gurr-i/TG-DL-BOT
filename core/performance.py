"""
Performance optimization module for Telegram Message Saver Bot.
Provides intelligent chunk sizing, connection management, and metrics tracking.
"""

import time
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Track performance metrics for monitoring and optimization."""
    total_downloads: int = 0
    total_uploads: int = 0
    total_bytes_downloaded: int = 0
    total_bytes_uploaded: int = 0
    average_download_speed: float = 0.0
    average_upload_speed: float = 0.0
    failed_operations: int = 0
    retry_count: int = 0
    start_time: float = field(default_factory=time.time)
    speed_samples: list = field(default_factory=list)
    
    def add_download(self, bytes_transferred: int, duration: float) -> None:
        """Record a completed download."""
        self.total_downloads += 1
        self.total_bytes_downloaded += bytes_transferred
        if duration > 0:
            speed = bytes_transferred / duration / (1024 * 1024)  # MB/s
            self.speed_samples.append(speed)
            if len(self.speed_samples) > 100:
                self.speed_samples = self.speed_samples[-100:]
            self.average_download_speed = sum(self.speed_samples) / len(self.speed_samples)
    
    def add_upload(self, bytes_transferred: int, duration: float) -> None:
        """Record a completed upload."""
        self.total_uploads += 1
        self.total_bytes_uploaded += bytes_transferred
        if duration > 0:
            speed = bytes_transferred / duration / (1024 * 1024)  # MB/s
            self.speed_samples.append(speed)
            if len(self.speed_samples) > 100:
                self.speed_samples = self.speed_samples[-100:]
            self.average_upload_speed = sum(self.speed_samples) / len(self.speed_samples)
    
    def add_failure(self) -> None:
        """Record a failed operation."""
        self.failed_operations += 1
    
    def add_retry(self) -> None:
        """Record a retry attempt."""
        self.retry_count += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        uptime = time.time() - self.start_time
        return {
            "uptime_seconds": round(uptime, 2),
            "total_downloads": self.total_downloads,
            "total_uploads": self.total_uploads,
            "total_data_downloaded_mb": round(self.total_bytes_downloaded / (1024 * 1024), 2),
            "total_data_uploaded_mb": round(self.total_bytes_uploaded / (1024 * 1024), 2),
            "average_download_speed_mbps": round(self.average_download_speed, 2),
            "average_upload_speed_mbps": round(self.average_upload_speed, 2),
            "failed_operations": self.failed_operations,
            "retry_count": self.retry_count,
            "success_rate": round(
                (self.total_downloads + self.total_uploads) / 
                max(1, self.total_downloads + self.total_uploads + self.failed_operations) * 100, 
                2
            )
        }


class PerformanceOptimizer:
    """Optimize performance for downloads and uploads."""
    
    def __init__(self):
        self.metrics = PerformanceMetrics()
        self._chunk_size_cache: Dict[int, int] = {}
    
    def get_optimal_chunk_size(self, file_size: int) -> int:
        """
        Calculate optimal chunk size based on file size.
        
        Small files (<10MB): 256KB chunks
        Medium files (10-100MB): 1MB chunks
        Large files (100MB-500MB): 2MB chunks
        Very large files (>500MB): 4MB chunks
        """
        if file_size in self._chunk_size_cache:
            return self._chunk_size_cache[file_size]
        
        MB = 1024 * 1024
        
        if file_size < 10 * MB:
            chunk_size = 256 * 1024  # 256KB
        elif file_size < 100 * MB:
            chunk_size = 1 * MB  # 1MB
        elif file_size < 500 * MB:
            chunk_size = 2 * MB  # 2MB
        else:
            chunk_size = 4 * MB  # 4MB
        
        self._chunk_size_cache[file_size] = chunk_size
        logger.debug(f"Optimal chunk size for {file_size/(1024*1024):.1f}MB: {chunk_size/1024}KB")
        return chunk_size
    
    def should_update_progress(self, current: int, total: int, last_update: float, 
                              last_percentage: int) -> bool:
        """
        Determine if progress should be updated.
        More intelligent throttling to reduce API calls.
        """
        if total == 0:
            return False
        
        current_percentage = int((current / total) * 100)
        current_time = time.time()
        
        # Always update at start and end
        if current == 0 or current >= total:
            return True
        
        # Update every 5% for better performance
        if current_percentage != last_percentage and current_percentage % 5 == 0:
            return True
        
        # Update every 3 seconds minimum
        if current_time - last_update >= 3.0:
            return True
        
        return False
    
    def calculate_eta(self, current: int, total: int, elapsed: float) -> str:
        """Calculate ETA with better accuracy."""
        if elapsed <= 0 or current <= 0:
            return "calculating..."
        
        speed = current / elapsed
        if speed <= 0:
            return "calculating..."
        
        remaining = total - current
        eta_seconds = remaining / speed
        
        if eta_seconds < 60:
            return f"{int(eta_seconds)}s"
        elif eta_seconds < 3600:
            minutes = int(eta_seconds / 60)
            seconds = int(eta_seconds % 60)
            return f"{minutes}m {seconds}s"
        else:
            hours = int(eta_seconds / 3600)
            minutes = int((eta_seconds % 3600) / 60)
            return f"{hours}h {minutes}m"
    
    def get_retry_delay(self, attempt: int, base_delay: float = 1.0, 
                       max_delay: float = 60.0, jitter: bool = True) -> float:
        """
        Calculate retry delay with exponential backoff and optional jitter.
        Jitter helps prevent thundering herd problem.
        """
        import random
        
        delay = min(base_delay * (2 ** attempt), max_delay)
        
        if jitter:
            # Add random jitter (±25%)
            jitter_amount = delay * 0.25
            delay = delay + random.uniform(-jitter_amount, jitter_amount)
        
        return max(0.1, delay)  # Minimum 0.1s delay
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return self.metrics.get_summary()
    
    def record_download(self, bytes_transferred: int, duration: float) -> None:
        """Record a download operation."""
        self.metrics.add_download(bytes_transferred, duration)
    
    def record_upload(self, bytes_transferred: int, duration: float) -> None:
        """Record an upload operation."""
        self.metrics.add_upload(bytes_transferred, duration)
    
    def record_failure(self) -> None:
        """Record a failed operation."""
        self.metrics.add_failure()
    
    def record_retry(self) -> None:
        """Record a retry attempt."""
        self.metrics.add_retry()


# Global instance
performance_optimizer = PerformanceOptimizer()
