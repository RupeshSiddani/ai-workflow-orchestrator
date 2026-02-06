"""
Base LLM Interface - Abstract interface for LLM providers
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class LLMMessage(BaseModel):
    """Message model for LLM conversations."""
    role: str  # "system", "user", "assistant"
    content: str
    name: Optional[str] = None


class LLMResponse(BaseModel):
    """Response model from LLM providers."""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, model: str, **kwargs):
        """Initialize LLM provider with model and configuration."""
        self.model = model
        self.config = kwargs
    
    @abstractmethod
    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response from LLM."""
        pass
    
    @abstractmethod
    async def generate_structured(
        self,
        messages: List[LLMMessage],
        schema: Dict[str, Any],
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate structured response following JSON schema."""
        pass
    
    @abstractmethod
    def validate_api_key(self) -> bool:
        """Validate that API key is properly configured."""
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "provider": self.__class__.__name__,
            "model": self.model,
            "config": self.config
        }
