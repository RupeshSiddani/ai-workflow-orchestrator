# Contributing to AI Operations Assistant

## Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai_ops_assistant
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys (NEVER commit this file)
   ```

4. **Run tests**
   ```bash
   pytest tests/ -v
   ```

5. **Run demo**
   ```bash
   python demo.py
   ```

## API Keys Setup

The system requires API keys for full functionality:

### Required for LLM Operations (choose one):
- **OpenAI**: Get key from https://platform.openai.com/account/api-keys
- **Anthropic**: Get key from https://console.anthropic.com/

### Optional for API Integrations:
- **GitHub**: Create personal access token at https://github.com/settings/tokens
- **Weather**: Get key from https://openweathermap.org/api
- **News**: Get key from https://newsapi.org/

**IMPORTANT**: Never commit API keys to the repository. The `.env` file is included in `.gitignore`.

## Code Style

This project uses:
- **Black** for code formatting
- **Flake8** for linting
- **MyPy** for type checking

Run all checks:
```bash
black .
flake8 .
mypy .
```

## Testing

Run all tests:
```bash
pytest tests/ -v
```

Run specific test file:
```bash
pytest tests/test_agents.py -v
```

## Architecture

```
ai_ops_assistant/
├── agents/          # Core AI agents (Planner, Executor, Verifier)
├── tools/           # API integration tools (GitHub, Weather, News)
├── llm/             # LLM provider integrations (OpenAI, Anthropic)
├── tests/           # Unit and integration tests
├── main.py          # Main CLI application
├── demo.py          # Demonstration script
├── config.py        # Configuration management
└── requirements.txt # Python dependencies
```

## Submitting Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass: `pytest tests/ -v`
6. Format code: `black .`
7. Commit changes: `git commit -m "Add feature description"`
8. Push to fork: `git push origin feature-name`
9. Create pull request

## Project Structure Guidelines

- **Agents**: Keep agent logic focused and single-purpose
- **Tools**: Each tool should handle one external API
- **Tests**: Mock external dependencies in tests
- **Documentation**: Update README.md for user-facing changes

## Debugging

Enable verbose logging:
```bash
python main.py "task" --verbose
```

Run in interactive mode for testing:
```bash
python main.py --interactive
```
