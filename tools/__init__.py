"""
Tools Module - API Integration Tools

This module contains tools for integrating with third-party APIs:
- GitHub API tools
- Weather API tools  
- News API tools
- Base tool interfaces and utilities
"""

from .base import BaseTool, ToolResult
from .registry import ToolRegistry
from .github import GitHubTool
from .weather import WeatherTool
from .news import NewsTool

__all__ = [
    "BaseTool", 
    "ToolResult", 
    "ToolRegistry",
    "GitHubTool", 
    "WeatherTool", 
    "NewsTool"
]
