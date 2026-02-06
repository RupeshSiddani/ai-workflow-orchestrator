"""
Configuration Management - Application settings and environment variables
"""

import os
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings."""
    
    # LLM Configuration
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4", env="OPENAI_MODEL")
    openai_base_url: str = Field("https://api.openai.com/v1", env="OPENAI_BASE_URL")
    
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    anthropic_model: str = Field("claude-3-sonnet-20240229", env="ANTHROPIC_MODEL")
    
    # Third-party API Keys
    github_token: Optional[str] = Field(None, env="GITHUB_TOKEN")
    weather_api_key: Optional[str] = Field(None, env="WEATHER_API_KEY")
    news_api_key: Optional[str] = Field(None, env="NEWS_API_KEY")
    
    # Application Settings
    log_level: str = Field("INFO", env="LOG_LEVEL")
    max_retries: int = Field(3, env="MAX_RETRIES")
    request_timeout: int = Field(30, env="REQUEST_TIMEOUT")
    cache_enabled: bool = Field(True, env="CACHE_ENABLED")
    cache_ttl: int = Field(3600, env="CACHE_TTL")
    
    # Agent Settings
    planner_temperature: float = Field(0.1, env="PLANNER_TEMPERATURE")
    executor_max_retries: int = Field(3, env="EXECUTOR_MAX_RETRIES")
    verifier_temperature: float = Field(0.1, env="VERIFIER_TEMPERATURE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def get_llm_provider(self) -> str:
        """Get the configured LLM provider."""
        if self.openai_api_key:
            return "openai"
        elif self.anthropic_api_key:
            return "anthropic"
        else:
            raise ValueError("No LLM provider configured")
    
    def validate_required_keys(self) -> dict[str, bool]:
        """Validate that required API keys are configured."""
        return {
            "openai": bool(self.openai_api_key),
            "anthropic": bool(self.anthropic_api_key),
            "github": bool(self.github_token),
            "weather": bool(self.weather_api_key),
            "news": bool(self.news_api_key)
        }


# Global settings instance
settings = Settings()
