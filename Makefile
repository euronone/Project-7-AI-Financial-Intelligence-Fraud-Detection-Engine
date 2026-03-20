.PHONY: dev backend frontend infra db-migrate db-seed test test-backend test-frontend lint format build docs

# Start local infrastructure (Postgres, Redis, MailHog)
infra:
	docker compose up -d

# Start backend dev server
backend:
	cd backend && poetry run uvicorn app.main:app --reload --port 8000

# Start frontend dev server
frontend:
	cd frontend && npm run dev

# Start everything
dev: infra
	@echo "Infrastructure started. Run 'make backend' and 'make frontend' in separate terminals."

# Database
db-migrate:
	cd backend && poetry run alembic upgrade head

db-seed:
	cd backend && poetry run python scripts/seed_data.py

db-seed-trends:
	cd backend && poetry run python scripts/seed_trend_scenario.py

# Testing
test: test-backend test-frontend

test-backend:
	cd backend && poetry run pytest --cov=app -v

test-frontend:
	cd frontend && npm run test

# Code quality
lint:
	cd backend && poetry run ruff check .
	cd frontend && npm run lint

format:
	cd backend && poetry run ruff format .

# Build Docker images
build:
	docker build -t finshield-backend:latest ./backend
	docker build -t finshield-frontend:latest ./frontend

# Open API docs
docs:
	@echo "Opening API docs at http://localhost:8000/docs"
	@start http://localhost:8000/docs 2>/dev/null || open http://localhost:8000/docs 2>/dev/null || true

# Train ML models
train-models:
	cd backend && poetry run python scripts/train_models.py
