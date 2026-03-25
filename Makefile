.PHONY: dev backend frontend db-migrate db-seed train-models test lint format build

# ── Development ──────────────────────────────────────────────────────────────
dev:
	docker compose up --build

backend:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

# ── Database ─────────────────────────────────────────────────────────────────
db-migrate:
	cd backend && alembic upgrade head

db-migrate-create:
	cd backend && alembic revision --autogenerate -m "$(MSG)"

db-seed:
	cd backend && python scripts/seed_data.py

# ── ML ───────────────────────────────────────────────────────────────────────
train-models:
	cd backend && python scripts/train_models.py

# ── Testing ──────────────────────────────────────────────────────────────────
test:
	cd backend && pytest tests/ -v
	cd frontend && npm test

test-backend:
	cd backend && pytest tests/ -v --tb=short

test-frontend:
	cd frontend && npm test

# ── Quality ──────────────────────────────────────────────────────────────────
lint:
	cd backend && ruff check .
	cd frontend && npm run lint

format:
	cd backend && ruff format .

# ── Build ────────────────────────────────────────────────────────────────────
build:
	docker compose build

# ── Docs ─────────────────────────────────────────────────────────────────────
docs:
	@echo "API Docs: http://localhost:8000/docs"
	@echo "MailHog:  http://localhost:8025"
	@start http://localhost:8000/docs 2>/dev/null || open http://localhost:8000/docs 2>/dev/null || true
