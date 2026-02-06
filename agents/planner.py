"""
Planner Agent - Converts natural language to structured execution plans
"""

import json
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from llm.base import BaseLLM, LLMMessage
from tools.registry import ToolRegistry


class PlanStep(BaseModel):
    """Single step in an execution plan."""
    step_id: int = Field(description="Unique identifier for this step")
    capability: str = Field(description="Tool capability to execute")
    parameters: Dict[str, Any] = Field(description="Parameters for the capability")
    description: str = Field(description="Human-readable description of this step")
    dependencies: List[int] = Field(default_factory=list, description="List of step IDs this step depends on")
    optional: bool = Field(default=False, description="Whether this step is optional")


class ExecutionPlan(BaseModel):
    """Complete execution plan for a task."""
    task_description: str = Field(description="Original task description")
    steps: List[PlanStep] = Field(description="List of execution steps")
    estimated_complexity: str = Field(description="Estimated complexity: simple, moderate, complex")
    required_tools: List[str] = Field(description="List of tools required for this plan")
    success_criteria: List[str] = Field(description="Criteria for successful completion")


class PlannerAgent:
    """Agent that creates execution plans from natural language tasks."""
    
    def __init__(self, llm_factory, tool_registry: ToolRegistry):
        """Initialize planner agent."""
        self.llm_factory = llm_factory
        self.tool_registry = tool_registry
        self.llm = llm_factory.create_llm()
    
    async def create_plan(self, user_input: str) -> ExecutionPlan:
        """
        Create an execution plan from natural language input.
        
        Args:
            user_input: Natural language task description
            
        Returns:
            Structured execution plan
        """
        # Get available capabilities
        available_capabilities = self._get_available_capabilities()
        
        # Create planning prompt
        messages = [
            LLMMessage(
                role="system",
                content=self._get_planning_system_prompt(available_capabilities)
            ),
            LLMMessage(
                role="user",
                content=f"Create an execution plan for this task: {user_input}"
            )
        ]
        
        # Generate structured plan
        plan_schema = ExecutionPlan.model_json_schema()
        plan_data = await self.llm.generate_structured(
            messages=messages,
            schema=plan_schema,
            temperature=0.1
        )
        
        # Validate and create plan object
        try:
            plan = ExecutionPlan(**plan_data)
            return self._validate_plan(plan)
        except Exception as e:
            raise RuntimeError(f"Failed to create valid plan: {e}")
    
    def _get_available_capabilities(self) -> List[Dict[str, Any]]:
        """Get list of available capabilities from tool registry."""
        capabilities = []
        for tool_name in self.tool_registry.list_tools():
            tool = self.tool_registry.get_tool(tool_name)
            if tool:
                for cap in tool.get_capabilities():
                    capabilities.append({
                        "name": cap.name,
                        "description": cap.description,
                        "tool": tool_name,
                        "parameters": [
                            {
                                "name": p.name,
                                "type": p.type,
                                "description": p.description,
                                "required": p.required,
                                "default": p.default
                            }
                            for p in cap.parameters
                        ],
                        "examples": cap.examples
                    })
        return capabilities
    
    def _get_planning_system_prompt(self, capabilities: List[Dict[str, Any]]) -> str:
        """Generate system prompt for planning."""
        capabilities_text = json.dumps(capabilities, indent=2)
        
        return f"""You are an AI Planning Agent that creates structured execution plans for natural language tasks.

Your job is to:
1. Analyze the user's task
2. Break it down into logical steps
3. Map each step to available tool capabilities
4. Create a complete execution plan

Available capabilities:
{capabilities_text}

Guidelines:
- Each step should use exactly one capability
- Steps should be ordered logically with dependencies
- Include all required parameters for each capability
- Mark optional steps that aren't critical for task completion
- Estimate complexity based on number of steps and API calls
- Define clear success criteria

You must respond with valid JSON following the ExecutionPlan schema.
Do not include any explanations or text outside the JSON response."""
    
    def _validate_plan(self, plan: ExecutionPlan) -> ExecutionPlan:
        """Validate that the plan is executable."""
        if not plan.steps:
            raise ValueError("Plan must have at least one step")
        
        # Check that all capabilities exist
        for step in plan.steps:
            tool = self.tool_registry.get_tool_for_capability(step.capability)
            if not tool:
                raise ValueError(f"Unknown capability: {step.capability}")
            
            # Validate parameters
            is_valid, error_msg = tool.validate_parameters(step.capability, step.parameters)
            if not is_valid:
                raise ValueError(f"Invalid parameters for {step.capability}: {error_msg}")
        
        # Check dependencies
        step_ids = {step.step_id for step in plan.steps}
        for step in plan.steps:
            for dep_id in step.dependencies:
                if dep_id not in step_ids:
                    raise ValueError(f"Step {step.step_id} depends on non-existent step {dep_id}")
        
        return plan
    
    async def refine_plan(self, plan: ExecutionPlan, feedback: str) -> ExecutionPlan:
        """
        Refine an existing plan based on feedback.
        
        Args:
            plan: Existing execution plan
            feedback: Feedback for improvement
            
        Returns:
            Refined execution plan
        """
        messages = [
            LLMMessage(
                role="system",
                content="You are an AI Planning Agent refining an existing execution plan based on feedback."
            ),
            LLMMessage(
                role="user",
                content=f"""
Original plan:
{plan.model_dump_json(indent=2)}

Feedback: {feedback}

Please create a refined plan that addresses the feedback.
"""
            )
        ]
        
        plan_schema = ExecutionPlan.model_json_schema()
        plan_data = await self.llm.generate_structured(
            messages=messages,
            schema=plan_schema,
            temperature=0.1
        )
        
        return ExecutionPlan(**plan_data)
