#!/usr/bin/env python3
"""
AI Operations Assistant - Main Entry Point

A multi-agent system that processes natural language tasks,
plans execution steps, calls APIs, and returns structured answers.
"""

import asyncio
import sys
from typing import Optional
import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent  
from agents.verifier import VerifierAgent
from llm.factory import LLMFactory
from tools.registry import ToolRegistry
from tools.github import GitHubTool
from tools.weather import WeatherTool
from tools.news import NewsTool

console = Console()


class AIOpsAssistant:
    """Main AI Operations Assistant orchestrator."""
    
    def __init__(self):
        """Initialize the AI Operations Assistant."""
        self.llm_factory = LLMFactory()
        self.tool_registry = ToolRegistry()
        
        # Register tools
        self.tool_registry.register_tool(GitHubTool())
        self.tool_registry.register_tool(WeatherTool())
        self.tool_registry.register_tool(NewsTool())
        
        # Initialize agents
        self.planner = PlannerAgent(self.llm_factory, self.tool_registry)
        self.executor = ExecutorAgent(self.llm_factory, self.tool_registry)
        self.verifier = VerifierAgent(self.llm_factory)
    
    async def process_request(self, user_input: str) -> dict:
        """
        Process a natural language request through the agent pipeline.
        
        Args:
            user_input: Natural language task description
            
        Returns:
            Structured result from the verifier agent
        """
        try:
            console.print(f"[bold blue]Processing request:[/bold blue] {user_input}")
            
            # Step 1: Planning
            console.print("[yellow]🤔 Planning execution steps...[/yellow]")
            plan = await self.planner.create_plan(user_input)
            console.print(Panel(
                Text(str(plan), style="green"),
                title="✅ Execution Plan Created",
                border_style="green"
            ))
            
            # Step 2: Execution
            console.print("[yellow]⚡ Executing plan...[/yellow]")
            execution_result = await self.executor.execute_plan(plan)
            console.print(Panel(
                Text(str(execution_result), style="blue"),
                title="⚡ Plan Execution Complete",
                border_style="blue"
            ))
            
            # Step 3: Verification
            console.print("[yellow]🔍 Verifying results...[/yellow]")
            verified_result = await self.verifier.verify_result(
                user_input, plan, execution_result
            )
            console.print(Panel(
                Text(str(verified_result), style="cyan"),
                title="✅ Results Verified",
                border_style="cyan"
            ))
            
            return verified_result
            
        except Exception as e:
            console.print(Panel(
                Text(f"Error: {str(e)}", style="red"),
                title="❌ Processing Failed",
                border_style="red"
            ))
            return {"error": str(e), "status": "failed"}


@click.command()
@click.argument("task", required=False)
@click.option("--interactive", "-i", is_flag=True, help="Run in interactive mode")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def main(task: Optional[str], interactive: bool, verbose: bool):
    """
    AI Operations Assistant - Process natural language tasks.
    
    Examples:
        python main.py "What's the weather in New York?"
        python main.py "Find popular Python repos on GitHub"
        python main.py --interactive
    """
    if verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    assistant = AIOpsAssistant()
    
    if interactive:
        console.print(Panel(
            Text("AI Operations Assistant - Interactive Mode", style="bold blue"),
            title="🤖 Welcome",
            border_style="blue"
        ))
        
        while True:
            try:
                user_input = console.input("\n[bold green]Enter your task (or 'quit' to exit):[/bold green] ")
                if user_input.lower() in ['quit', 'exit', 'q']:
                    console.print("[yellow]Goodbye! 👋[/yellow]")
                    break
                
                result = asyncio.run(assistant.process_request(user_input))
                console.print("\n[bold]Final Result:[/bold]")
                console.print(result)
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Goodbye! 👋[/yellow]")
                break
    else:
        if not task:
            console.print("[red]Error: Please provide a task or use --interactive mode[/red]")
            console.print("Example: python main.py \"What's the weather in London?\"")
            sys.exit(1)
        
        result = asyncio.run(assistant.process_request(task))
        console.print("\n[bold]Final Result:[/bold]")
        console.print(result)


if __name__ == "__main__":
    main()
