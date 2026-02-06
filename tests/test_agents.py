"""
Tests for AI Agents - Unit tests for Planner, Executor, and Verifier agents
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from agents.planner import PlannerAgent, ExecutionPlan, PlanStep
from agents.executor import ExecutorAgent
from agents.verifier import VerifierAgent
from tools.base import ToolResult, ToolStatus
from tools.registry import ToolRegistry


class TestPlannerAgent:
    """Test cases for Planner Agent."""
    
    @pytest.fixture
    def mock_llm_factory(self):
        """Mock LLM factory."""
        factory = MagicMock()
        llm = AsyncMock()
        factory.create_llm.return_value = llm
        return factory
    
    @pytest.fixture
    def mock_tool_registry(self):
        """Mock tool registry."""
        registry = MagicMock()
        registry.list_tools.return_value = ["github", "weather", "news"]
        registry.get_tool_for_capability.return_value = MagicMock()
        return registry
    
    @pytest.fixture
    def planner(self, mock_llm_factory, mock_tool_registry):
        """Create planner agent for testing."""
        return PlannerAgent(mock_llm_factory, mock_tool_registry)
    
    @pytest.mark.asyncio
    async def test_create_plan_success(self, planner, mock_llm_factory):
        """Test successful plan creation."""
        # Mock LLM response
        mock_plan_data = {
            "task_description": "Get weather in New York",
            "steps": [
                {
                    "step_id": 1,
                    "capability": "get_current_weather",
                    "parameters": {"city": "New York"},
                    "description": "Get current weather for New York",
                    "dependencies": [],
                    "optional": False
                }
            ],
            "estimated_complexity": "simple",
            "required_tools": ["weather"],
            "success_criteria": ["Weather data retrieved successfully"]
        }
        
        mock_llm_factory.create_llm.return_value.generate_structured.return_value = mock_plan_data
        
        # Mock tool validation
        mock_tool = MagicMock()
        mock_tool.validate_parameters.return_value = (True, None)
        planner.tool_registry.get_tool_for_capability.return_value = mock_tool
        
        plan = await planner.create_plan("Get weather in New York")
        
        assert isinstance(plan, ExecutionPlan)
        assert plan.task_description == "Get weather in New York"
        assert len(plan.steps) == 1
        assert plan.steps[0].capability == "get_current_weather"
        assert plan.estimated_complexity == "simple"
    
    @pytest.mark.asyncio
    async def test_create_plan_invalid_capability(self, planner, mock_llm_factory):
        """Test plan creation with invalid capability."""
        mock_plan_data = {
            "task_description": "Invalid task",
            "steps": [
                {
                    "step_id": 1,
                    "capability": "invalid_capability",
                    "parameters": {},
                    "description": "Invalid step",
                    "dependencies": [],
                    "optional": False
                }
            ],
            "estimated_complexity": "simple",
            "required_tools": [],
            "success_criteria": []
        }
        
        mock_llm_factory.create_llm.return_value.generate_structured.return_value = mock_plan_data
        
        # Mock tool registry to return None for invalid capability
        planner.tool_registry.get_tool_for_capability.return_value = None
        
        with pytest.raises(RuntimeError, match="Failed to create valid plan"):
            await planner.create_plan("Invalid task")


class TestExecutorAgent:
    """Test cases for Executor Agent."""
    
    @pytest.fixture
    def mock_llm_factory(self):
        """Mock LLM factory."""
        factory = MagicMock()
        llm = AsyncMock()
        factory.create_llm.return_value = llm
        return factory
    
    @pytest.fixture
    def mock_tool_registry(self):
        """Mock tool registry."""
        registry = MagicMock()
        return registry
    
    @pytest.fixture
    def executor(self, mock_llm_factory, mock_tool_registry):
        """Create executor agent for testing."""
        return ExecutorAgent(mock_llm_factory, mock_tool_registry)
    
    @pytest.fixture
    def sample_plan(self):
        """Create a sample execution plan."""
        step = PlanStep(
            step_id=1,
            capability="get_current_weather",
            parameters={"city": "New York"},
            description="Get weather for New York",
            dependencies=[],
            optional=False
        )
        
        return ExecutionPlan(
            task_description="Get weather in New York",
            steps=[step],
            estimated_complexity="simple",
            required_tools=["weather"],
            success_criteria=["Weather retrieved"]
        )
    
    @pytest.mark.asyncio
    async def test_execute_plan_success(self, executor, sample_plan):
        """Test successful plan execution."""
        # Mock tool execution
        mock_result = ToolResult(
            status=ToolStatus.SUCCESS,
            data={"temperature": 72, "condition": "sunny"}
        )
        
        executor.tool_registry.execute_capability = AsyncMock(return_value=mock_result)
        
        result = await executor.execute_plan(sample_plan)
        
        assert result["status"] == "success"
        assert result["execution_summary"]["successful_steps"] == 1
        assert result["execution_summary"]["failed_steps"] == 0
    
    @pytest.mark.asyncio
    async def test_execute_plan_with_failure(self, executor, sample_plan):
        """Test plan execution with step failure."""
        # Mock tool execution failure
        mock_result = ToolResult(
            status=ToolStatus.ERROR,
            error="API call failed"
        )
        
        executor.tool_registry.execute_capability = AsyncMock(return_value=mock_result)
        
        result = await executor.execute_plan(sample_plan)
        
        assert result["status"] == "failed"
        assert result["execution_summary"]["failed_steps"] == 1
    
    @pytest.mark.asyncio
    async def test_execute_plan_with_dependencies(self, executor):
        """Test plan execution with step dependencies."""
        # Create plan with dependencies
        step1 = PlanStep(
            step_id=1,
            capability="get_current_weather",
            parameters={"city": "New York"},
            description="Get weather for New York",
            dependencies=[],
            optional=False
        )
        
        step2 = PlanStep(
            step_id=2,
            capability="search_news",
            parameters={"query": "weather New York"},
            description="Search news about New York weather",
            dependencies=[1],
            optional=False
        )
        
        plan = ExecutionPlan(
            task_description="Get weather and news",
            steps=[step1, step2],
            estimated_complexity="moderate",
            required_tools=["weather", "news"],
            success_criteria=["Weather and news retrieved"]
        )
        
        # Mock tool executions
        mock_result1 = ToolResult(
            status=ToolStatus.SUCCESS,
            data={"temperature": 72}
        )
        
        mock_result2 = ToolResult(
            status=ToolStatus.SUCCESS,
            data={"articles": []}
        )
        
        executor.tool_registry.execute_capability = AsyncMock(side_effect=[mock_result1, mock_result2])
        
        result = await executor.execute_plan(plan)
        
        assert result["status"] == "success"
        assert result["execution_summary"]["successful_steps"] == 2


class TestVerifierAgent:
    """Test cases for Verifier Agent."""
    
    @pytest.fixture
    def mock_llm_factory(self):
        """Mock LLM factory."""
        factory = MagicMock()
        llm = AsyncMock()
        factory.create_llm.return_value = llm
        return factory
    
    @pytest.fixture
    def verifier(self, mock_llm_factory):
        """Create verifier agent for testing."""
        return VerifierAgent(mock_llm_factory)
    
    @pytest.fixture
    def sample_plan(self):
        """Create a sample execution plan."""
        step = PlanStep(
            step_id=1,
            capability="get_current_weather",
            parameters={"city": "New York"},
            description="Get weather for New York",
            dependencies=[],
            optional=False
        )
        
        return ExecutionPlan(
            task_description="Get weather in New York",
            steps=[step],
            estimated_complexity="simple",
            required_tools=["weather"],
            success_criteria=["Weather data retrieved successfully"]
        )
    
    @pytest.fixture
    def sample_execution_result(self):
        """Create a sample execution result."""
        return {
            "status": "success",
            "task_description": "Get weather in New York",
            "execution_summary": {
                "total_steps": 1,
                "successful_steps": 1,
                "failed_steps": 0,
                "partial_steps": 0,
                "total_execution_time": 1.5
            },
            "results": {
                "successful": [
                    {
                        "step_id": 1,
                        "description": "Get weather for New York",
                        "capability": "get_current_weather",
                        "execution_time": 1.5
                    }
                ],
                "failed": [],
                "partial": []
            },
            "data": {
                1: {"temperature": 72, "condition": "sunny"}
            }
        }
    
    @pytest.mark.asyncio
    async def test_verify_result_success(self, verifier, sample_plan, sample_execution_result, mock_llm_factory):
        """Test successful result verification."""
        # Mock verification response
        mock_verification = {
            "is_complete": True,
            "is_accurate": True,
            "missing_information": [],
            "quality_score": 0.9,
            "issues": [],
            "recommendations": [],
            "formatted_output": {
                "summary": "Weather in New York is sunny and 72°F",
                "details": {"temperature": 72, "condition": "sunny"},
                "sources": ["OpenWeatherMap"],
                "limitations": [],
                "confidence": "high"
            }
        }
        
        mock_llm_factory.create_llm.return_value.generate_structured.return_value = mock_verification
        
        result = await verifier.verify_result("Get weather in New York", sample_plan, sample_execution_result)
        
        assert result["success"] is True
        assert result["verification"]["is_complete"] is True
        assert result["verification"]["quality_score"] == 0.9
        assert "final_output" in result
    
    @pytest.mark.asyncio
    async def test_verify_result_with_issues(self, verifier, sample_plan, sample_execution_result, mock_llm_factory):
        """Test verification with identified issues."""
        # Mock verification response with issues
        mock_verification = {
            "is_complete": False,
            "is_accurate": True,
            "missing_information": ["humidity data"],
            "quality_score": 0.6,
            "issues": ["Missing humidity information"],
            "recommendations": ["Add humidity data to weather query"],
            "formatted_output": {
                "summary": "Partial weather data retrieved",
                "details": {"temperature": 72},
                "sources": ["OpenWeatherMap"],
                "limitations": ["Missing humidity"],
                "confidence": "medium"
            }
        }
        
        mock_llm_factory.create_llm.return_value.generate_structured.return_value = mock_verification
        
        result = await verifier.verify_result("Get weather in New York", sample_plan, sample_execution_result)
        
        assert result["success"] is False  # Due to incomplete data
        assert result["verification"]["is_complete"] is False
        assert "humidity" in result["verification"]["missing_information"][0]


if __name__ == "__main__":
    pytest.main([__file__])
