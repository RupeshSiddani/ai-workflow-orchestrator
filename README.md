# AI Operations Assistant

A multi-agent system that takes natural-language tasks, plans execution steps, calls APIs, and returns structured answers.

## 🏗️ Architecture

The system consists of three main agents:

### 🧠 **Planner Agent** (`agents/planner.py`)
- Converts natural language input into structured JSON plans
- Maps tasks to available tool capabilities
- Resolves dependencies between execution steps
- Uses LLM with structured outputs (no monolithic prompts)

### ⚡ **Executor Agent** (`agents/executor.py`)
- Executes JSON plans with topological sorting
- Makes API calls with retry logic (3 attempts)
- Manages execution context and state
- Handles partial results and optional steps

### 🔍 **Verifier Agent** (`agents/verifier.py`)
- Validates execution results against success criteria
- Assesses quality and completeness (0.0-1.0 score)
- Identifies missing information and issues
- Formats user-friendly final output

## 🔧 Tool System

### 📚 **Tool Registry** (`tools/registry.py`)
- Discovers and registers available tools
- Maps capabilities to tool implementations
- Provides parameter validation
- Supports capability search

### 🛠️ **Base Tool Interface** (`tools/base.py`)
- Abstract interface for all API integrations
- Standardized result format and error handling
- Capability definition system
- Parameter validation framework

## 🌐 Integrated APIs

### 1. **GitHub API** (`tools/github.py`)
- **Capabilities**: search_repositories, get_repository, get_user_info, list_repository_commits
- **Authentication**: GitHub personal access token (optional for public endpoints)
- **Features**: Rate limiting awareness, comprehensive data extraction, error handling

### 2. **Weather API** (`tools/weather.py`)
- **Capabilities**: get_current_weather, get_weather_forecast, get_weather_by_coordinates
- **Provider**: OpenWeatherMap API
- **Features**: Multiple unit systems, location support, 5-day forecasts

### 3. **News API** (`tools/news.py`)
- **Capabilities**: get_top_headlines, search_news, get_sources
- **Provider**: NewsAPI
- **Features**: Content summarization, multi-language support, source discovery

## 🚀 Setup Instructions

### Prerequisites
- Python 3.8+
- Git

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd ai_ops_assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# Required for LLM (choose one):
OPENAI_API_KEY=your_openai_api_key_here
# OR
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional for API integrations:
GITHUB_TOKEN=your_github_token_here
WEATHER_API_KEY=your_weather_api_key_here
NEWS_API_KEY=your_news_api_key_here
```

## 🏃‍♂️ Running the Project

### Option 1: FastAPI Web Server
```bash
# Start FastAPI server
uvicorn app:app

# Or with custom host/port
uvicorn app:app --host 0.0.0.0 --port 8000

# Access the API
# Web Interface: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Health Check: http://localhost:8000/health
```

### Option 2: Streamlit Web Interface  
```bash
# Start Streamlit app
streamlit run streamlit_app.py

# Access the web interface
# Web UI: http://localhost:8501
```

### Option 3: Command Line Interface
```bash
# Run with a specific task
python main.py "What's the weather in New York?"

# Run in interactive mode
python main.py --interactive

# Run with verbose logging
python main.py "Find Python repos on GitHub" --verbose
```

### Demo Mode
```bash
# Run demonstration script
python demo.py
```

### Test Suite
```bash
# Run all tests
pytest tests/ -v

# Run specific tests
pytest tests/test_agents.py -v
```

## 🧪 Example Prompts

### 1. **Simple Weather Query**
```bash
python main.py "What's the current weather in London, UK?"
```

### 2. **GitHub Repository Search**
```bash
python main.py "Find popular machine learning repositories on GitHub with more than 1000 stars"
```

### 3. **Technology News**
```bash
python main.py "Get top technology headlines from the United States"
```

### 4. **Combined Multi-Step Task**
```bash
python main.py "Check the weather in San Francisco and find trending React repositories on GitHub"
```

### 5. **Complex Research Task**
```bash
python main.py "Find recent news about artificial intelligence and get weather in major tech hubs (San Francisco, New York, London)"
```

## ⚠️ Known Limitations & Tradeoffs

### Current Limitations
1. **API Rate Limits**: Free API tiers have usage limits
2. **Sequential Execution**: Steps run sequentially (not parallel)
3. **No Caching**: API responses aren't cached between runs
4. **LLM Dependency**: Requires API keys for planning/verification
5. **Error Recovery**: Limited automatic recovery from API failures

### Design Tradeoffs
1. **Simplicity vs Features**: Focused on core functionality over extensive features
2. **Mock Testing**: Tests use mocks for reliability (requires real keys for live testing)
3. **Structured Outputs**: Enforced JSON schemas limit flexibility but ensure reliability
4. **Single LLM Provider**: Uses one LLM at a time (not hybrid approaches)

### Future Improvements
1. **Parallel Step Execution**: Run independent steps concurrently
2. **Response Caching**: Cache API responses to reduce calls
3. **Cost Tracking**: Monitor API usage and costs
4. **Enhanced Error Recovery**: More sophisticated retry and fallback strategies
5. **Web Interface**: Add Streamlit or FastAPI frontend

## 🧪 Verification

### Mandatory Requirements Check

- ✅ **Multi-agent design**: Planner, Executor, Verifier agents implemented
- ✅ **LLM with structured outputs**: Uses JSON schemas, no monolithic prompts
- ✅ **2+ real APIs**: GitHub, Weather, News APIs integrated
- ✅ **End-to-end results**: Complete pipeline from natural language to formatted output
- ✅ **No hard-coded responses**: All responses generated dynamically

### Test Results
```bash
pytest tests/ -v
# 23 tests passed, 1 warning
```

## 📁 Project Structure

```
ai_ops_assistant/
├── agents/              # Core AI agents
│   ├── planner.py       # Planner agent implementation
│   ├── executor.py      # Executor agent implementation
│   └── verifier.py     # Verifier agent implementation
├── tools/               # API integration tools
│   ├── github.py        # GitHub API integration
│   ├── weather.py       # Weather API integration
│   ├── news.py         # News API integration
│   ├── base.py         # Base tool interface
│   └── registry.py     # Tool registry system
├── llm/                # LLM provider integrations
│   ├── base.py         # Base LLM interface
│   ├── factory.py      # LLM factory pattern
│   ├── openai_provider.py    # OpenAI integration
│   └── anthropic_provider.py # Anthropic integration
├── tests/               # Test suite
│   ├── test_agents.py  # Agent tests
│   └── test_tools.py  # Tool tests
├── main.py             # Main CLI application
├── app.py              # FastAPI web server
├── streamlit_app.py    # Streamlit web interface
├── demo.py             # Demonstration script
├── config.py           # Configuration management
├── requirements.txt    # Python dependencies
├── .env.example       # Environment variables template
└── README.md          # This file
```

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

See CONTRIBUTING.md for development guidelines and setup instructions.
