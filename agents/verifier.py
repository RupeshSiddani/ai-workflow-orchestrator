"""
Verifier Agent - Validates results and fixes missing/incorrect output
"""

import json
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from llm.base import BaseLLM, LLMMessage
from agents.planner import ExecutionPlan


class VerificationResult(BaseModel):
    """Result of verification process."""
    is_complete: bool = Field(description="Whether the task was completed successfully")
    is_accurate: bool = Field(description="Whether the results are accurate")
    missing_information: List[str] = Field(default_factory=list, description="Missing critical information")
    quality_score: float = Field(description="Quality score from 0.0 to 1.0")
    issues: List[str] = Field(default_factory=list, description="Identified issues")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for improvement")
    formatted_output: Optional[Dict[str, Any]] = Field(description="Formatted final output")


class VerifierAgent:
    """Agent that validates execution results and ensures quality."""
    
    def __init__(self, llm_factory):
        """Initialize verifier agent."""
        self.llm_factory = llm_factory
        self.llm = llm_factory.create_llm()
    
    async def verify_result(
        self,
        user_input: str,
        plan: ExecutionPlan,
        execution_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Verify and validate execution results.
        
        Args:
            user_input: Original user task
            plan: Execution plan that was used
            execution_result: Results from executor agent
            
        Returns:
            Verified and formatted results
        """
        # Initial verification
        verification = await self._perform_initial_verification(
            user_input, plan, execution_result
        )
        
        # If verification fails, attempt to fix issues
        if not verification.is_complete or verification.quality_score < 0.7:
            verification = await self._attempt_fixes(
                user_input, plan, execution_result, verification
            )
        
        # Format final output
        final_output = await self._format_final_output(
            user_input, plan, execution_result, verification
        )
        
        return {
            "verification": verification.model_dump(),
            "final_output": final_output,
            "original_task": user_input,
            "execution_summary": execution_result.get("execution_summary", {}),
            "success": verification.is_complete and verification.is_accurate
        }
    
    async def _perform_initial_verification(
        self,
        user_input: str,
        plan: ExecutionPlan,
        execution_result: Dict[str, Any]
    ) -> VerificationResult:
        """Perform initial verification of execution results."""
        
        messages = [
            LLMMessage(
                role="system",
                content=self._get_verification_system_prompt()
            ),
            LLMMessage(
                role="user",
                content=f"""
Verify the execution results for this task:

Original Task: {user_input}

Execution Plan:
{plan.model_dump_json(indent=2)}

Execution Results:
{json.dumps(execution_result, indent=2)}

Success Criteria from Plan:
{json.dumps(plan.success_criteria, indent=2)}

Please analyze:
1. Was the task completed successfully?
2. Are the results accurate and reliable?
3. Is any critical information missing?
4. What is the overall quality of the results?
5. Are there any issues or problems?
6. What improvements would you recommend?

Respond with a JSON object following the VerificationResult schema.
"""
            )
        ]
        
        verification_schema = VerificationResult.model_json_schema()
        verification_data = await self.llm.generate_structured(
            messages=messages,
            schema=verification_schema,
            temperature=0.1
        )
        
        return VerificationResult(**verification_data)
    
    async def _attempt_fixes(
        self,
        user_input: str,
        plan: ExecutionPlan,
        execution_result: Dict[str, Any],
        verification: VerificationResult
    ) -> VerificationResult:
        """Attempt to fix identified issues."""
        
        if not verification.missing_information and not verification.issues:
            return verification
        
        messages = [
            LLMMessage(
                role="system",
                content="You are an AI Verification Agent attempting to fix issues with execution results."
            ),
            LLMMessage(
                role="user",
                content=f"""
The execution has issues that need to be addressed:

Original Task: {user_input}

Issues Found:
{json.dumps(verification.issues, indent=2)}

Missing Information:
{json.dumps(verification.missing_information, indent=2)}

Current Results:
{json.dumps(execution_result, indent=2)}

Please suggest specific fixes or workarounds for these issues.
If data is missing, suggest how to obtain it or reasonable defaults.
If there are accuracy issues, suggest corrections.
"""
            )
        ]
        
        try:
            response = await self.llm.generate(messages, temperature=0.3)
            
            # Update verification with fix suggestions
            verification.recommendations.extend([
                line.strip() for line in response.content.split('\n') if line.strip()
            ])
            
            return verification
            
        except Exception:
            return verification
    
    async def _format_final_output(
        self,
        user_input: str,
        plan: ExecutionPlan,
        execution_result: Dict[str, Any],
        verification: VerificationResult
    ) -> Dict[str, Any]:
        """Format the final output for the user."""
        
        messages = [
            LLMMessage(
                role="system",
                content=self._get_formatting_system_prompt()
            ),
            LLMMessage(
                role="user",
                content=f"""
Format the final output for this task:

Original Task: {user_input}

Execution Results:
{json.dumps(execution_result, indent=2)}

Verification Results:
{verification.model_dump_json(indent=2)}

Create a clean, user-friendly response that:
1. Directly answers the user's question
2. Presents the key information clearly
3. Includes relevant details from the execution
4. Acknowledges any limitations or issues
5. Is well-structured and easy to read

Respond with a JSON object containing the formatted output.
"""
            )
        ]
        
        formatting_schema = {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Brief summary of results"},
                "details": {"type": "object", "description": "Detailed results"},
                "sources": {"type": "array", "items": {"type": "string"}, "description": "Data sources"},
                "limitations": {"type": "array", "items": {"type": "string"}, "description": "Any limitations"},
                "confidence": {"type": "string", "description": "Confidence level in results"}
            },
            "required": ["summary", "details"]
        }
        
        try:
            formatted_data = await self.llm.generate_structured(
                messages=messages,
                schema=formatting_schema,
                temperature=0.1
            )
            
            verification.formatted_output = formatted_data
            return formatted_data
            
        except Exception as e:
            # Fallback formatting
            return {
                "summary": f"Results for: {user_input}",
                "details": execution_result.get("data", {}),
                "sources": [],
                "limitations": verification.issues,
                "confidence": "medium" if verification.quality_score > 0.5 else "low"
            }
    
    def _get_verification_system_prompt(self) -> str:
        """Get system prompt for verification."""
        return """You are an AI Verification Agent responsible for ensuring the quality and completeness of execution results.

Your responsibilities:
1. Verify that the original task was completed successfully
2. Check accuracy and reliability of the results
3. Identify missing critical information
4. Assess overall quality of the execution
5. Detect any issues or problems
6. Provide recommendations for improvement

Be thorough but fair in your assessment. Consider:
- Whether all success criteria were met
- Accuracy of the data provided
- Completeness of the information
- Any obvious errors or inconsistencies
- User experience and clarity

You must respond with valid JSON following the VerificationResult schema."""
    
    def _get_formatting_system_prompt(self) -> str:
        """Get system prompt for output formatting."""
        return """You are an AI Output Formatter responsible for creating user-friendly responses.

Your responsibilities:
1. Create clear, readable summaries
2. Organize information logically
3. Present key findings prominently
4. Include relevant details without overwhelming the user
5. Acknowledge any limitations or issues
6. Ensure the response directly addresses the user's original question

Focus on:
- Clarity and readability
- Logical organization
- User-friendly language
- Appropriate level of detail
- Honest assessment of limitations

You must respond with valid JSON following the provided schema."""
