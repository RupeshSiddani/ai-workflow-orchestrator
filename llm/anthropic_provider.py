"""
Anthropic LLM Provider - Integration with Anthropic Claude models
"""

import json
import asyncio
from typing import Dict, List, Optional, Any
import anthropic
from pydantic import ValidationError

from .base import BaseLLM, LLMMessage, LLMResponse


class AnthropicProvider(BaseLLM):
    """Anthropic Claude model provider."""
    
    def __init__(self, api_key: str, model: str):
        """Initialize Anthropic provider."""
        super().__init__(model)
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.api_key = api_key
    
    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response from Anthropic."""
        try:
            # Convert messages to Anthropic format
            anthropic_messages = []
            system_message = None
            
            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                elif msg.role == "user":
                    anthropic_messages.append({"role": "user", "content": msg.content})
                elif msg.role == "assistant":
                    anthropic_messages.append({"role": "assistant", "content": msg.content})
            
            response = await self.client.messages.create(
                model=self.model,
                messages=anthropic_messages,
                system=system_message,
                temperature=temperature,
                max_tokens=max_tokens or 4096,
                **kwargs
            )
            
            return LLMResponse(
                content=response.content[0].text if response.content else "",
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.input_tokens if response.usage else 0,
                    "completion_tokens": response.usage.output_tokens if response.usage else 0,
                    "total_tokens": (response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0
                } if response.usage else None,
                finish_reason=response.stop_reason,
                metadata={"id": response.id}
            )
            
        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {str(e)}")
    
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
Your entire response should be a single JSON object.
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
                enhanced_messages.insert(0, LLMMessage(
                    role="system",
                    content=schema_instruction
                ))
            
            response = await self.generate(
                messages=enhanced_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # Parse and validate JSON response
            try:
                # Extract JSON from response (in case there's extra text)
                content = response.content.strip()
                if content.startswith("```json"):
                    content = content[7:-3].strip()
                elif content.startswith("```"):
                    content = content[3:-3].strip()
                
                return json.loads(content)
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Invalid JSON response from Anthropic: {e}")
                
        except Exception as e:
            raise RuntimeError(f"Anthropic structured generation error: {str(e)}")
    
    def validate_api_key(self) -> bool:
        """Validate Anthropic API key."""
        try:
            # Simple validation - check if key looks like a valid Anthropic key
            return (
                self.api_key.startswith("sk-ant-") and 
                len(self.api_key) > 40
            )
        except Exception:
            return False
