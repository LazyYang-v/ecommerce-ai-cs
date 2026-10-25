FROM python:3.12-slim

ENV UV_PYTHON_PREFERENCE=only-system

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.12.3 /uv /uvx /bin/

RUN useradd --create-home --uid 1000 appuser && chown appuser:appuser /app
USER appuser

COPY --chown=appuser:appuser pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY --chown=appuser:appuser app ./app

EXPOSE 8000

CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
