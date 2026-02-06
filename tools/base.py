"""
Base Tool Interface - Abstract interface for API integration tools
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel
from enum import Enum


class ToolStatus(str, Enum):
    """Tool execution status."""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"
    RETRY = "retry"


class ToolResult(BaseModel):
    """Result from tool execution."""
    status: ToolStatus
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    
    def is_success(self) -> bool:
        """Check if tool execution was successful."""
        return self.status == ToolStatus.SUCCESS
    
    def is_error(self) -> bool:
        """Check if tool execution failed."""
        return self.status == ToolStatus.ERROR
    
    def is_partial(self) -> bool:
        """Check if tool execution returned partial results."""
        return self.status == ToolStatus.PARTIAL


class ToolParameter(BaseModel):
    """Tool parameter definition."""
    name: str
    type: str  # "string", "number", "boolean", "array", "object"
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None


class ToolCapability(BaseModel):
    """Tool capability definition."""
    name: str
    description: str
    parameters: List[ToolParameter]
    examples: List[str] = []


class BaseTool(ABC):
    """Abstract base class for API integration tools."""
    
    def __init__(self, name: str, description: str):
        """Initialize tool with name and description."""
        self.name = name
        self.description = description
        self.capabilities: List[ToolCapability] = []
    
    @abstractmethod
    async def execute(
        self,
        capability: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """Execute a tool capability with given parameters."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[ToolCapability]:
        """Get list of available capabilities for this tool."""
        pass
    
    @abstractmethod
    def validate_parameters(
        self,
        capability: str,
        parameters: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """Validate parameters for a specific capability."""
        pass
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Get information about this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": [
                {
                    "name": cap.name,
                    "description": cap.description,
                    "parameters": [
                        {
                            "name": p.name,
                            "type": p.type,
                            "description": p.description,
                            "required": p.required,
                            "default": p.default,
                            "enum": p.enum
                        }
                        for p in cap.parameters
                    ],
                    "examples": cap.examples
                }
                for cap in self.capabilities
            ]
        }
    
    def validate_api_key(self) -> bool:
        """Validate that required API keys are configured."""
        return True  # Override in subclasses that need API keys
