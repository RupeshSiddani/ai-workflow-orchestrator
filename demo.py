#!/usr/bin/env python3
"""
Demo Script - AI Operations Assistant Demonstration

This script demonstrates the AI Operations Assistant with various example tasks.
"""

import asyncio
import os
from main import AIOpsAssistant
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


async def run_demo():
    """Run demonstration of AI Operations Assistant."""
    
    console.print(Panel(
        Text("AI Operations Assistant - Demo Mode", style="bold blue"),
        title="🤖 Demo",
        border_style="blue"
    ))
    
    # Check environment setup
    console.print("\n[yellow]🔍 Checking environment setup...[/yellow]")
    
    # Check API keys
    api_keys = {
        "OpenAI": bool(os.getenv("OPENAI_API_KEY")),
        "Anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
        "GitHub": bool(os.getenv("GITHUB_TOKEN")),
        "Weather": bool(os.getenv("WEATHER_API_KEY")),
        "News": bool(os.getenv("NEWS_API_KEY"))
    }
    
    console.print("API Key Status:")
    for provider, configured in api_keys.items():
        status = "✅" if configured else "❌"
        console.print(f"  {status} {provider}")
    
    if not any(api_keys.values()):
        console.print("\n[red]❌ No API keys configured. Please set up your .env file.[/red]")
        console.print("Copy .env.example to .env and add your API keys.")
        return
    
    # Initialize assistant
    try:
        assistant = AIOpsAssistant()
        console.print("\n[green]✅ AI Operations Assistant initialized successfully![/green]")
    except Exception as e:
        console.print(f"\n[red]❌ Failed to initialize assistant: {e}[/red]")
        return
    
    # Demo tasks
    demo_tasks = [
        {
            "name": "Simple Weather Query",
            "task": "What's the current weather in London?",
            "requires": ["weather"]
        },
        {
            "name": "GitHub Repository Search",
            "task": "Find popular Python machine learning repositories on GitHub",
            "requires": ["github"]
        },
        {
            "name": "Technology News",
            "task": "Get top technology headlines from the US",
            "requires": ["news"]
        },
        {
            "name": "Combined Task",
            "task": "Check the weather in San Francisco and find trending React repositories",
            "requires": ["weather", "github"]
        }
    ]
    
    console.print("\n[bold]📋 Available Demo Tasks:[/bold]")
    for i, demo in enumerate(demo_tasks, 1):
        missing_apis = [api for api in demo["requires"] if not api_keys.get(api.capitalize())]
        status = "✅" if not missing_apis else f"❌ (needs: {', '.join(missing_apis)})"
        console.print(f"  {i}. {demo['name']} {status}")
        console.print(f"     Task: {demo['task']}")
    
    # Run available demos
    console.print("\n[bold]🚀 Running available demos...[/bold]")
    
    for demo in demo_tasks:
        missing_apis = [api for api in demo["requires"] if not api_keys.get(api.capitalize())]
        if missing_apis:
            console.print(f"\n[red]⏭️  Skipping {demo['name']} - missing: {', '.join(missing_apis)}[/red]")
            continue
        
        console.print(f"\n[bold blue]📝 Demo: {demo['name']}[/bold blue]")
        console.print(f"Task: {demo['task']}")
        
        try:
            result = await assistant.process_request(demo["task"])
            
            if result.get("success"):
                console.print("[green]✅ Success![/green]")
                if "final_output" in result and result["final_output"]:
                    console.print("Result Summary:")
                    if "summary" in result["final_output"]:
                        console.print(f"  {result['final_output']['summary']}")
                else:
                    console.print("Task completed successfully!")
            else:
                console.print("[yellow]⚠️  Partial success or issues detected[/yellow]")
                
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")
        
        console.print("-" * 50)
    
    console.print("\n[bold green]🎉 Demo completed![/bold green]")
    console.print("\nTo run with your own tasks:")
    console.print("  python main.py \"Your task here\"")
    console.print("  python main.py --interactive")


if __name__ == "__main__":
    asyncio.run(run_demo())
