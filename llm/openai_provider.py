"""
OpenAI LLM Provider - Integration with OpenAI GPT models
"""

import json
import asyncio
from typing import Dict, List, Optional, Any
import openai
from pydantic import ValidationError

from .base import BaseLLM, LLMMessage, LLMResponse


class OpenAIProvider(BaseLLM):
    """OpenAI GPT model provider."""
    
    def __init__(self, api_key: str, model: str, base_url: str = "https://api.openai.com/v1"):
        """Initialize OpenAI provider."""
        super().__init__(model)
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.api_key = api_key
    
    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response from OpenAI."""
        try:
            openai_messages = [
                {"role": msg.role, "content": msg.content, "name": msg.name}
                for msg in messages if msg.name
            ]
            openai_messages.extend([
                {"role": msg.role, "content": msg.content}
                for msg in messages if not msg.name
            ])
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                } if response.usage else None,
                finish_reason=response.choices[0].finish_reason,
                metadata={"id": response.id}
            )
            
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")
    
    async def generate_structured(
        self,
        messages: List[LLMMessage],
        schema: Dict[str, Any],
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate structured response following JSON schema."""
        try:
            # Add schema instruction to system message
            schema_instruction = f"""
You must respond with valid JSON that follows this schema:
{json.dumps(schema, indent=2)}

Do not include any other text, explanations, or formatting - only the JSON response.
"""
            
            enhanced_messages = []
            system_found = False
            
            for msg in messages:
                if msg.role == "system":
                    enhanced_messages.append(LLMMessage(
                        role="system",
                        content=msg.content + "\n\n" + schema_instruction
                    ))
                    system_found = True
                else:
                    enhanced_messages.append(msg)
            
            if not system_found:
                enhanced_messages.insert(0, LMMessage(
                    role="system",
                    content=schema_instruction
                ))
            
            response = await self.generate(
                messages=enhanced_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
                **kwargs
            )
            
            # Parse and validate JSON response
            try:
                return json.loads(response.content)
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Invalid JSON response from OpenAI: {e}")
                
        except Exception as e:
            raise RuntimeError(f"OpenAI structured generation error: {str(e)}")
    
    def validate_api_key(self) -> bool:
        """Validate OpenAI API key."""
        try:
            # Simple validation - check if key looks like a valid OpenAI key
            return (
                self.api_key.startswith("sk-") and 
                len(self.api_key) > 40
            )
        except Exception:
            return False
