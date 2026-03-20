FROM python:3.11-slim AS base

RUN groupadd -r finshield && useradd -r -g finshield finshield

WORKDIR /app

RUN pip install --no-cache-dir poetry==2.3.2 && \
    poetry config virtualenvs.create false

# --- Dependencies stage ---
FROM base AS deps

COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root --only main --no-interaction

# --- Production stage ---
FROM base AS production

COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

COPY app/ ./app/

USER finshield

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
