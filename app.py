#!/usr/bin/env python3
"""
Web Interface for AI Operations Assistant
Provides FastAPI endpoint and Streamlit UI for the multi-agent system
"""

import asyncio
import sys
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from main import AIOpsAssistant


class TaskRequest(BaseModel):
    """Request model for task submission."""
    task: str
    verbose: bool = False


class TaskResponse(BaseModel):
    """Response model for task results."""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None


# Initialize FastAPI app
app = FastAPI(
    title="AI Workflow Orchestrator",
    description="Multi-agent AI system for task execution and API integration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI Assistant
assistant = AIOpsAssistant()


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AI Workflow Orchestrator API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "execute": "/execute",
            "docs": "/docs"
        },
        "usage": {
            "execute": "POST /execute with task parameter"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agents": {
            "planner": "ready",
            "executor": "ready", 
            "verifier": "ready"
        },
        "tools": {
            "github": "ready",
            "weather": "ready",
            "news": "ready"
        }
    }


@app.post("/execute", response_model=TaskResponse)
async def execute_task(request: TaskRequest):
    """Execute a task through the AI agent pipeline."""
    import time
    start_time = time.time()
    
    try:
        # Process the task
        result = await assistant.process_request(request.task)
        
        execution_time = time.time() - start_time
        
        return TaskResponse(
            success=result.get("success", False),
            result=result,
            execution_time=execution_time
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        
        return TaskResponse(
            success=False,
            error=str(e),
            execution_time=execution_time
        )


@app.get("/agents")
async def get_agents_info():
    """Get information about available agents."""
    return {
        "planner": {
            "name": "Planner Agent",
            "description": "Converts natural language to structured execution plans",
            "capabilities": ["plan_creation", "dependency_resolution", "tool_selection"]
        },
        "executor": {
            "name": "Executor Agent", 
            "description": "Executes plans and calls APIs",
            "capabilities": ["api_execution", "retry_logic", "error_handling"]
        },
        "verifier": {
            "name": "Verifier Agent",
            "description": "Validates results and formats output", 
            "capabilities": ["result_validation", "quality_assessment", "output_formatting"]
        }
    }


@app.get("/tools")
async def get_tools_info():
    """Get information about available tools."""
    return {
        "github": {
            "name": "GitHub API",
            "capabilities": [
                "search_repositories",
                "get_repository", 
                "get_user_info",
                "list_repository_commits"
            ],
            "authentication": "GitHub token (optional for public endpoints)"
        },
        "weather": {
            "name": "Weather API",
            "capabilities": [
                "get_current_weather",
                "get_weather_forecast",
                "get_weather_by_coordinates"
            ],
            "provider": "OpenWeatherMap",
            "authentication": "API key required"
        },
        "news": {
            "name": "News API",
            "capabilities": [
                "get_top_headlines",
                "search_news",
                "get_sources"
            ],
            "provider": "NewsAPI",
            "authentication": "API key required"
        }
    }


if __name__ == "__main__":
    # Check if running with uvicorn command
    if len(sys.argv) > 1 and sys.argv[1] == "uvicorn":
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
    else:
        # Default: run with uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
