# AdCP Demo Orchestrator

Demo-ready AdCP orchestration that lets a buyer brief fan out to publisher sales agents and return relevant products with reasons.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -e .
   pip install -e ".[dev]"
   ```

2. **Configure environment:**
   ```bash
   cp env.example .env
   # Edit .env and set your GEMINI_API_KEY
   ```

3. **Run the application:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

4. **Test the health endpoint:**
   ```bash
   curl http://localhost:8000/health
   ```

## Development

- **Run tests:** `pytest -q`
- **Lint code:** `ruff check .`
- **Format code:** `black .`
- **Type check:** `mypy app`
- **All checks:** `make all`

## Documentation

- [Setup Guide](docs/setup.md) - Installation and running instructions
- [Architecture](docs/architecture.md) - Project structure and design decisions

## Project Status

**Phase 1 Complete** ✅
- FastAPI skeleton with health endpoint
- Environment configuration
- Bootstrap 5 + Font Awesome UI
- Unit tests and documentation
- Reference repositories cloned

**Next:** Phase 2 - Data models and database layer

## Golden Rules

- Max 150 lines per file (HTML and tests may exceed)
- No dummy data - always actionable errors
- Modular, simple, small functions
- Always unit tests and short docs
- Bootstrap 5 and Font Awesome, no inline CSS
- Reference repos are read-only
