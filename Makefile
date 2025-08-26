# AdCP Demo Orchestrator Makefile
# POSIX sh compatible commands only

.PHONY: help venv install run freeport health preflight test lint type fmt check psport env

# Variables
PORT ?= 8000
PY ?= python

help: ## Print targets with one line descriptions
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

venv: ## Create .venv then install project in editable mode
	@if [ ! -f app/main.py ]; then echo "Run make from repo root"; exit 2; fi
	@echo "Creating virtual environment..."
	$(PY) -m venv .venv
	@echo "Installing dependencies..."
	.venv/bin/pip install -e .
	@echo "Virtual environment ready. Activate with: source .venv/bin/activate"

install: ## Install deps without recreating venv
	@if [ ! -f app/main.py ]; then echo "Run make from repo root"; exit 2; fi
	@if [ ! -d .venv ]; then echo "Run 'make venv' first"; exit 1; fi
	.venv/bin/pip install -e .

run: ## Start uvicorn app.main:app with reload on PORT env
	@if [ ! -f app/main.py ]; then echo "Run make from repo root"; exit 2; fi
	@if [ ! -d .venv ]; then echo "Run 'make venv' first"; exit 1; fi
	@if lsof -i :$(PORT) >/dev/null 2>&1; then \
		echo "Port $(PORT) is busy. Run: PORT=\$$(make -s freeport) make run"; \
		echo "Or use: make psport to see what's using the port"; \
		exit 1; \
	fi
	.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port $(PORT)

freeport: ## Echo first free port in 8000..8010 to stdout
	@for port in 8000 8001 8002 8003 8004 8005 8006 8007 8008 8009 8010; do \
		if ! lsof -i :$$port >/dev/null 2>&1; then \
			echo $$port; \
			exit 0; \
		fi; \
	done; \
	echo "No free ports found in 8000-8010"; \
	exit 1

health: ## Curl GET http://localhost:$(PORT)/health with non zero exit on failure
	@if ! curl -s -f http://localhost:$(PORT)/health >/dev/null; then \
		echo "Health check failed. Is the server running on port $(PORT)?"; \
		exit 1; \
	fi
	@echo "Health check passed"

preflight: ## Curl GET /preflight and pretty print if jq exists, else raw
	@if ! curl -s -f http://localhost:$(PORT)/preflight >/dev/null; then \
		echo "Preflight check failed. Is the server running on port $(PORT)?"; \
		exit 1; \
	fi
	@if command -v jq >/dev/null 2>&1; then \
		curl -s http://localhost:$(PORT)/preflight | jq .; \
	else \
		curl -s http://localhost:$(PORT)/preflight; \
	fi

test: ## Run pytest -q. Do not run live AI tests
	@if [ ! -f app/main.py ]; then echo "Run make from repo root"; exit 2; fi
	@if [ ! -d .venv ]; then echo "Run 'make venv' first"; exit 1; fi
	PYTHONPATH=. .venv/bin/pytest -q

lint: ## Run ruff check . (if ruff in deps)
	@if [ ! -f app/main.py ]; then echo "Run make from repo root"; exit 2; fi
	@if [ ! -d .venv ]; then echo "Run 'make venv' first"; exit 1; fi
	@if ! .venv/bin/pip show ruff >/dev/null 2>&1; then \
		echo "ruff not installed. Install with: .venv/bin/pip install ruff"; \
		exit 1; \
	fi
	.venv/bin/ruff check .

type: ## Run mypy app (if mypy in deps)
	@if [ ! -f app/main.py ]; then echo "Run make from repo root"; exit 2; fi
	@if [ ! -d .venv ]; then echo "Run 'make venv' first"; exit 1; fi
	@if ! .venv/bin/pip show mypy >/dev/null 2>&1; then \
		echo "mypy not installed. Install with: .venv/bin/pip install mypy"; \
		exit 1; \
	fi
	.venv/bin/mypy app

fmt: ## Run black . (if black in deps) then ruff format . if present
	@if [ ! -f app/main.py ]; then echo "Run make from repo root"; exit 2; fi
	@if [ ! -d .venv ]; then echo "Run 'make venv' first"; exit 1; fi
	@if .venv/bin/pip show black >/dev/null 2>&1; then \
		.venv/bin/black .; \
	fi
	@if .venv/bin/pip show ruff >/dev/null 2>&1; then \
		.venv/bin/ruff format .; \
	fi

check: ## Run lint, type, and test in that order. Fail fast
	@$(MAKE) lint
	@$(MAKE) type
	@$(MAKE) test

psport: ## List processes listening on PORT
	@if command -v lsof >/dev/null 2>&1; then \
		if lsof -i :$(PORT) >/dev/null 2>&1; then \
			echo "Processes using port $(PORT):"; \
			lsof -i :$(PORT); \
		else \
			echo "No processes using port $(PORT)"; \
		fi; \
	else \
		echo "lsof not available. On Windows, use: netstat -ano | findstr :$(PORT)"; \
	fi

env: ## Print key envs: DB_URL, SERVICE_BASE_URL, GEMINI_API_KEY set or not, DEBUG, PORT
	@echo "Environment variables:"
	@echo "  PORT: $(PORT)"
	@echo "  DEBUG: $(if $(DEBUG),$(DEBUG),not set)"
	@echo "  DATABASE_URL: $(if $(DATABASE_URL),$(DATABASE_URL),not set)"
	@echo "  SERVICE_BASE_URL: $(if $(SERVICE_BASE_URL),$(SERVICE_BASE_URL),not set)"
	@echo "  GEMINI_API_KEY: $(if $(GEMINI_API_KEY),set,not set)"
