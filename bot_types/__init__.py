"""Type definitions and interfaces for the Telegram Content Saver Bot."""

from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
from datetime import datetime

@dataclass
class MessageInfo:
    """Information about a message being processed."""
    chat_id: Union[int, str]
    message_id: int
    link_type: str
    timestamp: datetime = datetime.now()

@dataclass
class UserState:
    """User state information."""
    step: str
    chat_id: int
    timestamp: float
    cid: Optional[Union[int, str]] = None
    sid: Optional[int] = None
    lt: Optional[str] = None
    num: Optional[int] = None

@dataclass
class ProgressInfo:
    """Progress information for file transfers."""
    cancel: bool = False
    last_step: int = 0
    user_id: Optional[int] = None
    retry_count: Optional[int] = None
    download_msg_id: Optional[int] = None
    upload_msg_id: Optional[int] = None
    file_name: Optional[str] = None
    file_size: Optional[float] = None