"""
Executor Agent - Executes plans and calls APIs
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from llm.base import BaseLLM, LLMMessage
from tools.registry import ToolRegistry
from tools.base import ToolResult, ToolStatus
from agents.planner import ExecutionPlan, PlanStep


@dataclass
class ExecutionContext:
    """Context for plan execution."""
    plan: ExecutionPlan
    results: Dict[int, ToolResult] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = {}
        if self.metadata is None:
            self.metadata = {}


class ExecutorAgent:
    """Agent that executes plans and manages API calls."""
    
    def __init__(self, llm_factory, tool_registry: ToolRegistry):
        """Initialize executor agent."""
        self.llm_factory = llm_factory
        self.tool_registry = tool_registry
        self.llm = llm_factory.create_llm()
        self.max_retries = 3
        self.retry_delay = 1.0
    
    async def execute_plan(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """
        Execute an execution plan.
        
        Args:
            plan: Execution plan to execute
            
        Returns:
            Execution results with metadata
        """
        context = ExecutionContext(plan=plan)
        
        try:
            # Sort steps by dependencies (topological sort)
            sorted_steps = self._sort_steps_by_dependencies(plan.steps)
            
            # Execute steps in order
            for step in sorted_steps:
                if await self._should_execute_step(step, context):
                    result = await self._execute_step(step, context)
                    context.results[step.step_id] = result
                    
                    # Handle step failure
                    if result.is_error() and not step.optional:
                        return self._create_execution_result(context, failed=True)
            
            return self._create_execution_result(context, failed=False)
            
        except Exception as e:
            context.metadata["execution_error"] = str(e)
            return self._create_execution_result(context, failed=True, error=str(e))
    
    async def _should_execute_step(self, step: PlanStep, context: ExecutionContext) -> bool:
        """Check if a step should be executed based on dependencies."""
        # Check if all dependencies are completed successfully
        for dep_id in step.dependencies:
            if dep_id not in context.results:
                return False  # Dependency not executed yet
            
            dep_result = context.results[dep_id]
            if dep_result.is_error() and not step.optional:
                return False  # Required dependency failed
        
        return True
    
    async def _execute_step(self, step: PlanStep, context: ExecutionContext) -> ToolResult:
        """Execute a single plan step."""
        start_time = time.time()
        
        for attempt in range(self.max_retries):
            try:
                # Prepare execution context
                execution_context = {
                    "step_id": step.step_id,
                    "attempt": attempt + 1,
                    "previous_results": context.results,
                    "plan_metadata": context.metadata
                }
                
                # Execute the capability
                result = await self.tool_registry.execute_capability(
                    capability=step.capability,
                    parameters=step.parameters,
                    context=execution_context
                )
                
                # Add execution time
                execution_time = time.time() - start_time
                result.execution_time = execution_time
                
                if result.is_success() or result.is_partial():
                    return result
                
                # If we got an error and this isn't the last attempt, retry
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                
                return result
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    return ToolResult(
                        status=ToolStatus.ERROR,
                        error=f"Step execution failed after {self.max_retries} attempts: {str(e)}",
                        execution_time=time.time() - start_time
                    )
                
                await asyncio.sleep(self.retry_delay * (attempt + 1))
    
    def _sort_steps_by_dependencies(self, steps: List[PlanStep]) -> List[PlanStep]:
        """Sort steps topologically based on dependencies."""
        # Create step lookup
        step_map = {step.step_id: step for step in steps}
        
        # Topological sort
        visited = set()
        temp_visited = set()
        sorted_steps = []
        
        def visit(step_id: int):
            if step_id in temp_visited:
                raise ValueError(f"Circular dependency detected involving step {step_id}")
            if step_id in visited:
                return
            
            temp_visited.add(step_id)
            step = step_map[step_id]
            
            # Visit dependencies first
            for dep_id in step.dependencies:
                visit(dep_id)
            
            temp_visited.remove(step_id)
            visited.add(step_id)
            sorted_steps.append(step)
        
        for step in steps:
            if step.step_id not in visited:
                visit(step.step_id)
        
        return sorted_steps
    
    def _create_execution_result(
        self, 
        context: ExecutionContext, 
        failed: bool = False,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create execution result summary."""
        successful_steps = []
        failed_steps = []
        partial_steps = []
        
        for step_id, result in context.results.items():
            step = next(s for s in context.plan.steps if s.step_id == step_id)
            
            if result.is_success():
                successful_steps.append({
                    "step_id": step_id,
                    "description": step.description,
                    "capability": step.capability,
                    "execution_time": result.execution_time
                })
            elif result.is_partial():
                partial_steps.append({
                    "step_id": step_id,
                    "description": step.description,
                    "capability": step.capability,
                    "execution_time": result.execution_time,
                    "data": result.data
                })
            else:
                failed_steps.append({
                    "step_id": step_id,
                    "description": step.description,
                    "capability": step.capability,
                    "error": result.error
                })
        
        total_execution_time = sum(
            result.execution_time or 0 for result in context.results.values()
        )
        
        return {
            "status": "failed" if failed else "success",
            "task_description": context.plan.task_description,
            "execution_summary": {
                "total_steps": len(context.plan.steps),
                "successful_steps": len(successful_steps),
                "failed_steps": len(failed_steps),
                "partial_steps": len(partial_steps),
                "total_execution_time": total_execution_time
            },
            "results": {
                "successful": successful_steps,
                "failed": failed_steps,
                "partial": partial_steps
            },
            "data": {
                step_id: result.data 
                for step_id, result in context.results.items() 
                if result.data
            },
            "metadata": context.metadata,
            "error": error
        }
    
    async def handle_step_failure(
        self, 
        step: PlanStep, 
        result: ToolResult, 
        context: ExecutionContext
    ) -> Optional[Dict[str, Any]]:
        """
        Handle step failure and potentially suggest recovery.
        
        Args:
            step: Failed step
            result: Failure result
            context: Execution context
            
        Returns:
            Recovery suggestions or None
        """
        if step.optional:
            return None  # Optional steps don't need recovery
        
        # Use LLM to suggest recovery
        messages = [
            LLMMessage(
                role="system",
                content="You are an AI Execution Agent that suggests recovery strategies for failed steps."
            ),
            LLMMessage(
                role="user",
                content=f"""
Step failed:
- Step ID: {step.step_id}
- Description: {step.description}
- Capability: {step.capability}
- Parameters: {step.parameters}
- Error: {result.error}

Available capabilities: {list(self.tool_registry.list_capabilities())}

Suggest recovery strategies or alternative approaches.
"""
            )
        ]
        
        try:
            response = await self.llm.generate(messages, temperature=0.3)
            return {"recovery_suggestions": response.content}
        except Exception:
            return None
