"""
Application settings and configuration.
"""

import os
from typing import Optional


class Settings:
    """Application settings."""
    
    # Google Cloud Configuration
    GOOGLE_CLOUD_PROJECT: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    DOCUMENT_AI_PROCESSOR_ID: str = os.getenv("DOCUMENT_AI_PROCESSOR_ID", "")
    DOCUMENT_AI_LOCATION: str = os.getenv("DOCUMENT_AI_LOCATION", "us")
    
    # Google Cloud Service Account (optional, for local development)
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Output Configuration
    DEFAULT_OUTPUT_DIR: str = os.getenv("DEFAULT_OUTPUT_DIR", "data/output")
    
    # File Processing
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "50"))  # MB
    SUPPORTED_MIME_TYPES: list = ["application/pdf"]
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required settings."""
        required_settings = [
            cls.GOOGLE_CLOUD_PROJECT,
            cls.DOCUMENT_AI_PROCESSOR_ID
        ]
        
        missing = [setting for setting in required_settings if not setting]
        
        if missing:
            print("Missing required environment variables:")
            for setting in missing:
                if setting == cls.GOOGLE_CLOUD_PROJECT:
                    print("  - GOOGLE_CLOUD_PROJECT")
                elif setting == cls.DOCUMENT_AI_PROCESSOR_ID:
                    print("  - DOCUMENT_AI_PROCESSOR_ID")
            return False
        
        return True


# Global settings instance
settings = Settings() 