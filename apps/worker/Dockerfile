FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN mkdir -p worker && touch worker/__init__.py
RUN pip install -e .

COPY . .

RUN addgroup --system app && adduser --system --group app
USER app

CMD ["python", "-m", "worker.main"]
