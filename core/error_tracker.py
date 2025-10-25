"""
Error tracking and pattern analysis using MCP Memory server.
Helps identify recurring issues and suggest preventive measures.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

class ErrorTracker:
    """Track and analyze error patterns for better reliability."""
    
    def __init__(self):
        self._local_errors: Dict[str, int] = defaultdict(int)
        self._error_contexts: list = []
        
    async def record_error(self, error_type: str, context: Dict[str, Any]) -> None:
        """
        Record an error occurrence with context.
        
        Args:
            error_type: Type of error (e.g., 'flood_wait', 'timeout', 'not_found')
            context: Additional context (user_id, channel_id, operation, etc.)
        """
        self._local_errors[error_type] += 1
        self._error_contexts.append({
            "type": error_type,
            "context": context,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 100 errors in memory
        if len(self._error_contexts) > 100:
            self._error_contexts = self._error_contexts[-100:]
        
        logger.info(f"[ERROR_TRACKER] Recorded {error_type}: {context}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of error patterns."""
        return {
            "total_errors": sum(self._local_errors.values()),
            "error_types": dict(self._local_errors),
            "recent_errors": self._error_contexts[-10:] if self._error_contexts else []
        }
    
    def get_most_common_errors(self, limit: int = 5) -> list:
        """Get most common error types."""
        sorted_errors = sorted(
            self._local_errors.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_errors[:limit]
    
    async def suggest_fixes(self, error_type: str) -> Optional[str]:
        """Suggest fixes based on error patterns."""
        suggestions = {
            "flood_wait": (
                "🔧 **Flood Wait Detected**\n\n"
                "**Suggestions:**\n"
                "• Reduce concurrent downloads (currently 3)\n"
                "• Increase delay between operations\n"
                "• Use sequential mode for sensitive channels\n"
                "• Bot will automatically retry with backoff"
            ),
            "timeout": (
                "🔧 **Timeout Issues**\n\n"
                "**Suggestions:**\n"
                "• Check network connectivity with /speed\n"
                "• Try smaller batch sizes\n"
                "• Verify channel is accessible\n"
                "• Consider using userbot for private channels"
            ),
            "not_found": (
                "🔧 **Message Not Found**\n\n"
                "**Possible Causes:**\n"
                "• Message was deleted\n"
                "• Channel is private (need userbot)\n"
                "• Invalid message ID\n"
                "• Bot not member of channel"
            ),
            "session_crash": (
                "🔧 **Session Crash**\n\n"
                "**Recovery Steps:**\n"
                "• Bot will automatically retry\n"
                "• If persists, regenerate session: /session\n"
                "• Check .env file for valid SESSION string\n"
                "• Restart bot if needed"
            )
        }
        
        return suggestions.get(error_type)


# Global instance
error_tracker = ErrorTracker()
