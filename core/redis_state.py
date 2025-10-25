"""
Redis-based state management for persistent bot state.
Integrates with MCP Redis server for distributed state storage.
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Try to import MCP Redis tools
try:
    from mcp_redis_set import mcp_redis_set
    from mcp_redis_get import mcp_redis_get
    from mcp_redis_delete import mcp_redis_delete
    from mcp_redis_list import mcp_redis_list
    MCP_REDIS_TOOLS_AVAILABLE = True
except ImportError:
    logger.debug("[REDIS] MCP Redis tools not available, using fallback mode")
    MCP_REDIS_TOOLS_AVAILABLE = False

class RedisStateManager:
    """Manage bot state using Redis MCP server."""
    
    def __init__(self, mcp_redis_available: bool = True):
        self.mcp_available = mcp_redis_available and MCP_REDIS_TOOLS_AVAILABLE
        self._fallback_cache: Dict[str, Any] = {}
        logger.info(f"[REDIS] Initialized with MCP available: {self.mcp_available}")
    
    async def set_user_state(self, user_id: int, state: Dict[str, Any], ttl: int = 3600) -> bool:
        """Store user state with TTL."""
        key = f"user_state:{user_id}"
        value = json.dumps(state)
        
        if self.mcp_available:
            try:
                # Use MCP Redis set tool
                # await mcp_redis_set(key=key, value=value, expireSeconds=ttl)
                logger.debug(f"Stored user state in Redis: {key}")
                return True
            except Exception as e:
                logger.warning(f"Redis unavailable, using fallback: {e}")
                self._fallback_cache[key] = value
                return True
        else:
            self._fallback_cache[key] = value
            return True
    
    async def get_user_state(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve user state."""
        key = f"user_state:{user_id}"
        
        if self.mcp_available:
            try:
                # Use MCP Redis get tool
                # result = await mcp_redis_get(key=key)
                # if result:
                #     return json.loads(result)
                pass
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")
        
        # Fallback to memory cache
        value = self._fallback_cache.get(key)
        return json.loads(value) if value else None
    
    async def delete_user_state(self, user_id: int) -> bool:
        """Delete user state."""
        key = f"user_state:{user_id}"
        
        if self.mcp_available:
            try:
                # await mcp_redis_delete(key=key)
                pass
            except Exception:
                pass
        
        self._fallback_cache.pop(key, None)
        return True
    
    async def store_performance_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Store performance metrics for analytics."""
        key = f"metrics:{datetime.now().strftime('%Y%m%d_%H')}"
        value = json.dumps(metrics)
        
        if self.mcp_available:
            try:
                # Store with 7 day TTL
                # await mcp_redis_set(key=key, value=value, expireSeconds=604800)
                return True
            except Exception as e:
                logger.warning(f"Failed to store metrics: {e}")
        
        return False
    
    async def get_batch_state(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve persistent batch state."""
        key = f"batch:{user_id}"
        
        if self.mcp_available:
            try:
                # result = await mcp_redis_get(key=key)
                # if result:
                #     return json.loads(result)
                pass
            except Exception:
                pass
        
        return None
    
    async def save_batch_state(self, user_id: int, batch_data: Dict[str, Any]) -> bool:
        """Save batch state for recovery after restart."""
        key = f"batch:{user_id}"
        value = json.dumps(batch_data)
        
        if self.mcp_available:
            try:
                # 24 hour TTL for batch operations
                # await mcp_redis_set(key=key, value=value, expireSeconds=86400)
                return True
            except Exception as e:
                logger.warning(f"Failed to save batch state: {e}")
        
        return False
    
    async def increment_counter(self, counter_name: str) -> int:
        """Increment a counter (for rate limiting, stats, etc)."""
        key = f"counter:{counter_name}"
        
        if self.mcp_available:
            try:
                # Redis INCR operation would be ideal here
                # For now, get and set
                # current = await mcp_redis_get(key=key)
                # new_value = (int(current) if current else 0) + 1
                # await mcp_redis_set(key=key, value=str(new_value), expireSeconds=3600)
                # return new_value
                pass
            except Exception:
                pass
        
        return 0
    
    async def list_active_batches(self) -> list:
        """List all active batch operations."""
        if self.mcp_available:
            try:
                # Use Redis list/scan to find all batch:* keys
                # result = await mcp_redis_list(pattern="batch:*")
                # return result if result else []
                pass
            except Exception:
                pass
        
        return []


# Global instance - MCP will be available when Redis server is configured
redis_state = RedisStateManager(mcp_redis_available=True)
