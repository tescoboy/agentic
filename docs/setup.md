# Setup Guide

This guide will help you set up and run the AdCP Demo Orchestrator from scratch.

## Prerequisites

### Python Version
- **Python 3.11+** (tested with Python 3.13.1)
- We recommend using a virtual environment

### System Requirements
- macOS, Linux, or Windows
- Git
- At least 100MB free disk space

## Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd orcs3
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the project root:

```bash
# Required: AI Provider Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Override defaults
DEBUG=0
ADCP_VERSION=adcp-demo-0.1
SERVICE_BASE_URL=http://localhost:8000

# Database (auto-created)
DATABASE_URL=sqlite:///./data/adcp_demo.sqlite3

# Orchestrator Configuration
ORCH_TIMEOUT_MS_DEFAULT=8000
ORCH_CONCURRENCY=8
CB_FAILURE_THRESHOLD=3
CB_TTL_SECONDS=60
```

### 5. Initialize Database
```bash
python -c "from app.db import init_db; init_db()"
```

### 6. Run the Application
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at: http://localhost:8000

## Development Setup

### Code Quality Tools
Install development dependencies:
```bash
pip install ruff black mypy pytest pytest-asyncio
```

### Linting
```bash
# Format code
black app/ tests/

# Lint code
ruff check app/ tests/

# Type checking
mypy app/
```

### Testing
```bash
# Run all tests
pytest

# Run specific test files
pytest tests/test_prompt_precedence.py

# Run with coverage (optional)
pip install pytest-cov
pytest --cov=app --cov-report=html
```

### Database Management
```bash
# Database file location
./data/adcp_demo.sqlite3

# Reset database (WARNING: deletes all data)
rm ./data/adcp_demo.sqlite3
python -c "from app.db import init_db; init_db()"
```

## Project Structure

```
orcs3/
├── app/
│   ├── ai/                 # AI provider abstraction
│   ├── models/             # SQLModel data models
│   ├── repositories/       # Data access layer
│   ├── routes/             # FastAPI route handlers
│   ├── services/           # Business logic
│   ├── templates/          # Jinja2 HTML templates
│   └── main.py            # FastAPI application
├── data/                   # SQLite database (auto-created)
├── docs/                   # Documentation
├── tests/                  # Test suite
├── requirements.txt        # Python dependencies
└── .env                    # Environment variables
```

## Key Features

### Multi-Tenant Architecture
- Each tenant has their own products and agent settings
- Tenant isolation via cookie-based context
- Publisher-specific AI prompts and configurations

### AI Integration
- Gemini AI provider (default)
- Swappable AI provider architecture
- Configurable timeouts and model selection

### AdCP Protocol
- Advertising Context Protocol compliance
- Standardized request/response formats
- Error handling with structured responses

### Orchestrator Service
- Concurrent agent fan-out
- Circuit breaker pattern for fault tolerance
- Timeout handling and retry logic

## Troubleshooting

### Common Issues

#### Missing API Key
```
Error: Missing API key for Gemini AI provider
```
**Solution**: Set `GEMINI_API_KEY` in your `.env` file

#### Database Errors
```
Error: No such table 'tenants'
```
**Solution**: Run database initialization:
```bash
python -c "from app.db import init_db; init_db()"
```

#### Import Errors
```
ModuleNotFoundError: No module named 'app'
```
**Solution**: Ensure you're in the project root and using the virtual environment:
```bash
source .venv/bin/activate
export PYTHONPATH=.
```

#### Port Already in Use
```
Error: [Errno 48] Address already in use
```
**Solution**: Use a different port:
```bash
uvicorn app.main:app --reload --port 8001
```

### Getting Help

1. Check the logs for detailed error messages
2. Verify all environment variables are set correctly
3. Ensure the database file exists and is writable
4. Check that all dependencies are installed

## Next Steps

After setup, you can:

1. **Create Tenants**: Visit http://localhost:8000/tenants
2. **Add Products**: Use CSV import or manual entry
3. **Configure AI Settings**: Set custom prompts per tenant
4. **Test Buyer Flow**: Use the buyer interface at http://localhost:8000/buyer
5. **Explore API**: Check http://localhost:8000/docs for API documentation

## Production Deployment

For production deployment:

1. Use a production WSGI server (Gunicorn, uWSGI)
2. Set up a proper database (PostgreSQL, MySQL)
3. Configure reverse proxy (Nginx, Apache)
4. Set up monitoring and logging
5. Use environment-specific configuration files
6. Implement proper security measures

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

[Add your license information here]
