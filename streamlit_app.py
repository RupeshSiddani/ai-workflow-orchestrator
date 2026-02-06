#!/usr/bin/env python3
"""
Streamlit Web Interface for AI Operations Assistant
Interactive web UI for the multi-agent AI system
"""

import asyncio
import time
import streamlit as st
import sys
from main import AIOpsAssistant


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'assistant' not in st.session_state:
        st.session_state.assistant = AIOpsAssistant()
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'current_task' not in st.session_state:
        st.session_state.current_task = ""


def display_message(role: str, content: str, metadata: dict = None):
    """Display a message in the chat interface."""
    st.session_state.messages.append({"role": role, "content": content, "metadata": metadata})
    
    with st.chat_message(role):
        if role == "user":
            st.write(content)
        elif role == "assistant":
            if metadata and metadata.get("execution_time"):
                st.caption(f"⚡ Executed in {metadata['execution_time']:.2f}s")
            
            if isinstance(content, dict):
                # Display structured result
                if content.get("success"):
                    st.success("✅ Task completed successfully!")
                    
                    if "final_output" in content:
                        final_output = content["final_output"]
                        
                        # Display summary
                        if final_output.get("summary"):
                            st.info(f"📋 **Summary:** {final_output['summary']}")
                        
                        # Display details
                        if final_output.get("details"):
                            with st.expander("📊 Detailed Results"):
                                st.json(final_output["details"])
                        
                        # Display sources
                        if final_output.get("sources"):
                            st.write("**📚 Sources:**")
                            for source in final_output["sources"]:
                                st.write(f"- {source}")
                        
                        # Display limitations
                        if final_output.get("limitations"):
                            st.warning("**⚠️ Limitations:**")
                            for limitation in final_output["limitations"]:
                                st.write(f"- {limitation}")
                    else:
                        with st.expander("🔍 Raw Results"):
                            st.json(content)
                else:
                    st.error(content.get("error", "Unknown error occurred"))
            else:
                st.write(content)


def display_example_prompts():
    """Display example prompts for testing."""
    st.sidebar.markdown("### 🧪 Example Prompts")
    
    examples = [
        "What's the current weather in London, UK?",
        "Find popular Python machine learning repositories on GitHub",
        "Get top technology headlines from United States", 
        "Check weather in San Francisco and find trending React repositories",
        "Find recent news about artificial intelligence and get weather in major tech hubs"
    ]
    
    for i, example in enumerate(examples, 1):
        if st.sidebar.button(f"{i}. {example[:50]}..."):
            st.session_state.current_task = example


def display_system_info():
    """Display system information in sidebar."""
    st.sidebar.markdown("### 🏗️ System Information")
    
    # Agent status
    st.sidebar.write("**🤖 Agents:**")
    agents = ["Planner", "Executor", "Verifier"]
    for agent in agents:
        st.sidebar.write(f"✅ {agent} Agent")
    
    # Tool status
    st.sidebar.write("**🔧 Tools:**")
    tools = ["GitHub API", "Weather API", "News API"]
    for tool in tools:
        st.sidebar.write(f"✅ {tool}")
    
    # API key status
    st.sidebar.markdown("### 🔑 API Configuration")
    
    import os
    api_status = {
        "OpenAI": bool(os.getenv("OPENAI_API_KEY")),
        "Anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
        "GitHub": bool(os.getenv("GITHUB_TOKEN")),
        "Weather": bool(os.getenv("WEATHER_API_KEY")),
        "News": bool(os.getenv("NEWS_API_KEY"))
    }
    
    for provider, configured in api_status.items():
        status = "✅" if configured else "❌"
        st.sidebar.write(f"{status} {provider}")


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="AI Workflow Orchestrator",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.title("🤖 AI Workflow Orchestrator")
    st.markdown("*Multi-agent system for task execution and API integration*")
    
    # Display system info
    display_system_info()
    
    # Display example prompts
    display_example_prompts()
    
    # Main chat interface
    st.markdown("---")
    st.subheader("💬 Task Input")
    
    # Task input
    col1, col2 = st.columns([4, 1])
    
    with col1:
        task = st.text_input(
            "Enter your task:",
            value=st.session_state.current_task,
            placeholder="e.g., What's the weather in New York?",
            key="task_input"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Align button
        if st.button("🚀 Execute", type="primary"):
            if task.strip():
                st.session_state.current_task = task.strip()
    
    # Execute task if entered
    if st.session_state.current_task and st.session_state.current_task != st.session_state.get("last_task", ""):
        st.session_state.last_task = st.session_state.current_task
        
        # Display user message
        display_message("user", st.session_state.current_task)
        
        # Process task
        with st.spinner("🤔 Planning... ⚡ Executing... 🔍 Verifying..."):
            start_time = time.time()
            try:
                result = await st.session_state.assistant.process_request(st.session_state.current_task)
                execution_time = time.time() - start_time
                
                display_message(
                    "assistant", 
                    result, 
                    metadata={"execution_time": execution_time}
                )
                
            except Exception as e:
                execution_time = time.time() - start_time
                display_message(
                    "assistant",
                    {"success": False, "error": str(e)},
                    metadata={"execution_time": execution_time}
                )
        
        # Clear current task
        st.session_state.current_task = ""
    
    # Display conversation history
    if st.session_state.messages:
        st.markdown("---")
        st.subheader("📜 Conversation History")
        
        for message in st.session_state.messages:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message["content"])
            elif message["role"] == "assistant":
                with st.chat_message("assistant"):
                    if message.get("metadata", {}).get("execution_time"):
                        st.caption(f"⚡ Executed in {message['metadata']['execution_time']:.2f}s")
                    
                    content = message["content"]
                    if isinstance(content, dict):
                        if content.get("success"):
                            if "final_output" in content:
                                final_output = content["final_output"]
                                
                                if final_output.get("summary"):
                                    st.info(f"📋 **Summary:** {final_output['summary']}")
                                
                                if final_output.get("details"):
                                    with st.expander("📊 Detailed Results"):
                                        st.json(final_output["details"])
                                
                                if final_output.get("sources"):
                                    st.write("**📚 Sources:**")
                                    for source in final_output["sources"]:
                                        st.write(f"- {source}")
                            else:
                                with st.expander("🔍 Raw Results"):
                                    st.json(content)
                        else:
                            st.error(content.get("error", "Unknown error"))
                    else:
                        st.write(content)
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <p>🤖 AI Workflow Orchestrator | Multi-Agent Task Execution System</p>
            <p><small>Built with Streamlit, FastAPI, and modern AI agents</small></p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    # Check if running with streamlit command
    if len(sys.argv) > 1 and sys.argv[1] == "streamlit":
        main()
    else:
        # Default: run streamlit
        main()
