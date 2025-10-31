"""
Enhanced file management using MCP Filesystem server.
Provides better file operations, monitoring, and cleanup.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class EnhancedFileManager:
    """Enhanced file operations using MCP Filesystem."""
    
    def __init__(self, mcp_filesystem_available: bool = False):
        self.mcp_available = mcp_filesystem_available
        self.downloads_dir = "./downloads"
    
    async def get_directory_stats(self) -> Dict[str, Any]:
        """Get comprehensive directory statistics."""
        if self.mcp_available:
            try:
                # Use MCP filesystem to get detailed stats
                # files = await mcp_filesystem_list_directory_with_sizes(
                #     path=self.downloads_dir,
                #     sortBy="size"
                # )
                
                # Calculate stats
                # total_size = sum(f['size'] for f in files if f['type'] == 'file')
                # file_count = len([f for f in files if f['type'] == 'file'])
                
                # return {
                #     "total_files": file_count,
                #     "total_size_mb": total_size / (1024 * 1024),
                #     "largest_file": max(files, key=lambda x: x.get('size', 0)),
                #     "timestamp": datetime.now().isoformat()
                # }
                pass
            except Exception as e:
                logger.warning(f"MCP filesystem unavailable: {e}")
        
        # Fallback to standard os operations
        try:
            files = os.listdir(self.downloads_dir)
            total_size = sum(
                os.path.getsize(os.path.join(self.downloads_dir, f))
                for f in files if os.path.isfile(os.path.join(self.downloads_dir, f))
            )
            return {
                "total_files": len(files),
                "total_size_mb": total_size / (1024 * 1024),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get directory stats: {e}")
            return {"total_files": 0, "total_size_mb": 0}
    
    async def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """Clean up files older than specified hours."""
        cleaned = 0
        
        if self.mcp_available:
            try:
                # Use MCP to search and get file info
                # files = await mcp_filesystem_list_directory(path=self.downloads_dir)
                
                # for file in files:
                #     file_info = await mcp_filesystem_get_file_info(
                #         path=os.path.join(self.downloads_dir, file['name'])
                #     )
                #     
                #     # Check age and delete if old
                #     if file_info['age_hours'] > max_age_hours:
                #         os.remove(file_info['path'])
                #         cleaned += 1
                
                pass
            except Exception as e:
                logger.warning(f"MCP cleanup failed: {e}")
        
        # Fallback cleanup
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            for filename in os.listdir(self.downloads_dir):
                filepath = os.path.join(self.downloads_dir, filename)
                if os.path.isfile(filepath):
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if file_time < cutoff_time:
                        os.remove(filepath)
                        cleaned += 1
                        logger.debug(f"Cleaned up old file: {filename}")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
        
        return cleaned
    
    async def find_temp_files(self) -> List[str]:
        """Find temporary files that may need cleanup."""
        temp_files = []
        
        if self.mcp_available:
            try:
                # Use MCP search to find .temp files
                # results = await mcp_filesystem_search_files(
                #     path=self.downloads_dir,
                #     pattern="*.temp"
                # )
                # temp_files = results
                pass
            except Exception as e:
                logger.warning(f"MCP search failed: {e}")
        
        # Fallback search
        try:
            for filename in os.listdir(self.downloads_dir):
                if filename.endswith('.temp'):
                    temp_files.append(os.path.join(self.downloads_dir, filename))
        except Exception as e:
            logger.error(f"Temp file search failed: {e}")
        
        return temp_files
    
    async def get_file_tree(self) -> Optional[Dict[str, Any]]:
        """Get directory tree structure."""
        if self.mcp_available:
            try:
                # Use MCP to get tree structure
                # tree = await mcp_filesystem_directory_tree(path=self.downloads_dir)
                # return tree
                pass
            except Exception as e:
                logger.warning(f"MCP tree failed: {e}")
        
        return None
    
    async def monitor_disk_space(self) -> Dict[str, Any]:
        """Monitor disk space usage."""
        try:
            import shutil
            total, used, free = shutil.disk_usage(self.downloads_dir)
            
            return {
                "total_gb": total / (1024**3),
                "used_gb": used / (1024**3),
                "free_gb": free / (1024**3),
                "usage_percent": (used / total) * 100,
                "warning": (free / total) < 0.1  # Warn if <10% free
            }
        except Exception as e:
            logger.error(f"Disk space check failed: {e}")
            return {"warning": False}


# Global instance
file_manager = EnhancedFileManager(mcp_available=False)
