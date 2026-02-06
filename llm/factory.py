"""
LLM Factory - Creates and manages LLM provider instances
"""

import os
from typing import Optional
from dotenv import load_dotenv

from .base import BaseLLM
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider


class LLMFactory:
    """Factory for creating LLM provider instances."""
    
    def __init__(self):
        """Initialize LLM factory and load environment variables."""
        load_dotenv()
    
    def create_llm(
        self, 
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> BaseLLM:
        """
        Create an LLM provider instance.
        
        Args:
            provider: LLM provider name ("openai", "anthropic", or auto-detect)
            model: Specific model to use (provider default if None)
            
        Returns:
            Configured LLM provider instance
            
        Raises:
            ValueError: If no suitable provider is configured
        """
        if provider is None:
            provider = self._detect_provider()
        
        provider = provider.lower()
        
        if provider == "openai":
            return self._create_openai(model)
        elif provider == "anthropic":
            return self._create_anthropic(model)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def _detect_provider(self) -> str:
        """Auto-detect available LLM provider based on API keys."""
        if os.getenv("OPENAI_API_KEY"):
            return "openai"
        elif os.getenv("ANTHROPIC_API_KEY"):
            return "anthropic"
        else:
            raise ValueError(
                "No LLM provider configured. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY"
            )
    
    def _create_openai(self, model: Optional[str]) -> OpenAIProvider:
        """Create OpenAI provider instance."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
        default_model = os.getenv("OPENAI_MODEL", "gpt-4")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        
        return OpenAIProvider(
            api_key=api_key,
            model=model or default_model,
            base_url=base_url
        )
    
    def _create_anthropic(self, model: Optional[str]) -> AnthropicProvider:
        """Create Anthropic provider instance."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        
        default_model = os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
        
        return AnthropicProvider(
            api_key=api_key,
            model=model or default_model
        )
    
    def list_available_providers(self) -> list[str]:
        """List all configured LLM providers."""
        providers = []
        if os.getenv("OPENAI_API_KEY"):
            providers.append("openai")
        if os.getenv("ANTHROPIC_API_KEY"):
            providers.append("anthropic")
        return providers
    
    def get_provider_info(self) -> dict:
        """Get information about configured providers."""
        return {
            "available_providers": self.list_available_providers(),
            "default_provider": self._detect_provider() if self.list_available_providers() else None,
            "openai_model": os.getenv("OPENAI_MODEL"),
            "anthropic_model": os.getenv("ANTHROPIC_MODEL")
        }
