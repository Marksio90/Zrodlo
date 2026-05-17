FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
# Create a minimal stub so hatchling can resolve the editable install
# before the full source is copied (preserves Docker layer cache for deps).
RUN mkdir -p app && touch app/__init__.py
RUN pip install -e .

COPY . .

RUN addgroup --system app && adduser --system --group app
USER app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
