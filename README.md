# AI Operations Assistant

A multi-agent system that takes natural-language tasks, plans execution steps, calls APIs, and returns structured answers.

## Architecture

The system consists of three main agents:

- **Planner Agent**: Converts user input into structured JSON plans and selects appropriate tools
- **Executor Agent**: Executes plan steps, calls APIs, and handles responses
- **Verifier Agent**: Validates results and fixes missing or incorrect output

## Features

- Multi-agent architecture with LLM-powered reasoning
- Integration with real third-party APIs (GitHub, Weather, News)
- Structured JSON outputs and validation
- Local execution via CLI
- Comprehensive error handling and retry logic
- Modular and extensible tool system

## Quick Start

1. **Setup Environment**
   ```bash
   cd ai_ops_assistant
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run the Assistant**
   ```bash
   python main.py "What's the weather in New York and find popular Python repos on GitHub?"
   ```

## Project Structure

```
ai_ops_assistant/
├── agents/          # Agent implementations
├── tools/           # API integration tools
├── llm/             # LLM provider integrations
├── main.py          # Main orchestration logic
├── requirements.txt # Python dependencies
├── .env.example     # Environment variables template
└── README.md        # This file
```

## Usage Examples

### Weather Information
```bash
python main.py "What's the current weather in London?"
```

### GitHub Repository Search
```bash
python main.py "Find popular machine learning repositories on GitHub"
```

### Combined Tasks
```bash
python main.py "Check the weather in San Francisco and find trending React repositories"
```

## Configuration

The system supports multiple LLM providers:

- **OpenAI**: Set `OPENAI_API_KEY` and optionally `OPENAI_MODEL`
- **Anthropic**: Set `ANTHROPIC_API_KEY` and optionally `ANTHROPIC_MODEL`

Third-party APIs:
- **GitHub**: Set `GITHUB_TOKEN` for higher rate limits
- **Weather**: Set `WEATHER_API_KEY` (supports OpenWeatherMap)
- **News**: Set `NEWS_API_KEY` (supports NewsAPI)

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black .
flake8 .
mypy .
```

## API Integration

Currently supported APIs:
- GitHub API (repository search, user info, repository details)
- Weather API (current weather by city)
- News API (top headlines by category/country)

## Architecture Details

### Planner Agent
- Analyzes natural language input
- Generates structured JSON execution plans
- Selects appropriate tools for each step
- Validates plan completeness

### Executor Agent
- Parses and executes JSON plans
- Makes API calls with proper error handling
- Manages execution context and state
- Handles partial results and retries

### Verifier Agent
- Validates execution results
- Checks for missing or incorrect data
- Formats final output
- Implements quality assurance

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
