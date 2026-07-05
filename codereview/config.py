import os
from typing import Any, Dict, Optional
from dotenv import load_dotenv

class Config:
    def __init__(self, overrides: Optional[Dict[str, Any]] = None):
        # Load .env file if present
        load_dotenv()
        
        overrides = overrides or {}
        
        # API Keys - try overrides, then standard ENV, then typo ENV
        if "openai_api_key" in overrides:
            self.openai_api_key = overrides["openai_api_key"]
        else:
            self.openai_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAPI_KEY")
            
        # Provider settings
        if "default_provider" in overrides:
            self.default_provider = overrides["default_provider"]
        else:
            self.default_provider = os.getenv("CODIVUS_PROVIDER", "openai")
            
        # Model settings
        if "default_model" in overrides:
            self.default_model = overrides["default_model"]
        else:
            self.default_model = os.getenv("CODIVUS_MODEL", "gpt-4o-mini")
            
        # Temperature settings
        if "temperature" in overrides:
            raw_temp = overrides["temperature"]
        else:
            raw_temp = os.getenv("CODIVUS_TEMPERATURE", "0.2")
            
        try:
            self.temperature = float(raw_temp) if raw_temp is not None else 0.2
        except ValueError:
            self.temperature = 0.2

    def validate(self) -> None:
        """Validate critical configuration settings."""
        if self.default_provider == "openai" and not self.openai_api_key:
            raise ValueError(
                "OpenAI API Key is missing. Please set OPENAI_API_KEY (or OPENAPI_KEY) in your environment or .env file."
            )
