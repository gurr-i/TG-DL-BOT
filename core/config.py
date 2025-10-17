"""Configuration management for the Telegram Saver Bot."""

import os
from typing import Optional
from dotenv import load_dotenv

class Config:
    """Configuration class to manage bot settings and credentials."""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # API credentials
        self.api_id: Optional[int] = None
        self.api_hash: Optional[str] = None
        self.bot_token: Optional[str] = None
        self.session: Optional[str] = None
        
        # Load and validate configuration
        self._load_config()
    
    def _load_config(self) -> None:
        """Load and validate configuration from environment variables."""
        try:
            api_id = os.getenv("API_ID")
            if api_id:
                self.api_id = int(api_id)
            
            self.api_hash = os.getenv("API_HASH")
            self.bot_token = os.getenv("BOT_TOKEN")
            self.session = os.getenv("SESSION")
            
        except ValueError as e:
            raise ValueError(f"Invalid configuration value: {e}")
    
    def validate(self) -> bool:
        """Validate that all required configuration is present."""
        return all([
            self.api_id is not None,
            self.api_hash,
            self.bot_token
        ])

# Create a global instance
config = Config()