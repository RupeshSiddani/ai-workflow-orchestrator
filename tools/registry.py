"""
Tool Registry - Manages registration and discovery of tools
"""

from typing import Dict, List, Optional, Type, Any
from .base import BaseTool, ToolCapability, ToolResult


class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self):
        """Initialize tool registry."""
        self._tools: Dict[str, BaseTool] = {}
        self._capability_index: Dict[str, str] = {}  # capability_name -> tool_name
    
    def register_tool(self, tool: BaseTool) -> None:
        """
        Register a tool in the registry.
        
        Args:
            tool: Tool instance to register
        """
        self._tools[tool.name] = tool
        
        # Index capabilities for quick lookup
        for capability in tool.get_capabilities():
            self._capability_index[capability.name] = tool.name
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(name)
    
    def get_tool_for_capability(self, capability: str) -> Optional[BaseTool]:
        """
        Get the tool that provides a specific capability.
        
        Args:
            capability: Capability name
            
        Returns:
            Tool instance or None if not found
        """
        tool_name = self._capability_index.get(capability)
        if tool_name:
            return self._tools.get(tool_name)
        return None
    
    def list_tools(self) -> List[str]:
        """Get list of all registered tool names."""
        return list(self._tools.keys())
    
    def list_capabilities(self) -> List[str]:
        """Get list of all available capabilities."""
        return list(self._capability_index.keys())
    
    def get_all_capabilities(self) -> Dict[str, List[ToolCapability]]:
        """Get all capabilities grouped by tool."""
        result = {}
        for tool_name, tool in self._tools.items():
            result[tool_name] = tool.get_capabilities()
        return result
    
    def search_capabilities(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for capabilities matching a query.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching capabilities with tool info
        """
        query = query.lower()
        matches = []
        
        for tool_name, tool in self._tools.items():
            for capability in tool.get_capabilities():
                # Search in capability name, description, and examples
                searchable_text = (
                    capability.name.lower() + " " +
                    capability.description.lower() + " " +
                    " ".join(capability.examples).lower()
                )
                
                if query in searchable_text:
                    matches.append({
                        "tool": tool_name,
                        "capability": capability.name,
                        "description": capability.description,
                        "examples": capability.examples
                    })
        
        return matches
    
    async def execute_capability(
        self,
        capability: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """
        Execute a capability using the appropriate tool.
        
        Args:
            capability: Capability name to execute
            parameters: Parameters for the capability
            context: Optional execution context
            
        Returns:
            Result from tool execution
            
        Raises:
            ValueError: If capability is not found
        """
        tool = self.get_tool_for_capability(capability)
        if not tool:
            raise ValueError(f"No tool found for capability: {capability}")
        
        # Validate parameters
        is_valid, error_msg = tool.validate_parameters(capability, parameters)
        if not is_valid:
            raise ValueError(f"Invalid parameters for {capability}: {error_msg}")
        
        return await tool.execute(capability, parameters, context)
    
    def get_registry_info(self) -> Dict[str, Any]:
        """Get comprehensive information about the registry."""
        return {
            "total_tools": len(self._tools),
            "total_capabilities": len(self._capability_index),
            "tools": {
                name: tool.get_tool_info()
                for name, tool in self._tools.items()
            },
            "capability_mapping": dict(self._capability_index)
        }
