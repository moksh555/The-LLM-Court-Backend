# A small Python base
FROM python:3.12-slim

# Install uv by copying the binary from Astral's image (fast + clean)
COPY --from=ghcr.io/astral-sh/uv:0.9.18 /uv /uvx /bin/

WORKDIR /app

# Copy the project (must include pyproject.toml + uv.lock + your src/)
COPY . /app

# Don't install dev dependencies in production images
ENV UV_NO_DEV=1

# Install deps exactly as locked
RUN uv sync --locked

# Make sure your "src/" is importable (since your app is in Backend/src/app/...)
ENV PYTHONPATH=/app/src

EXPOSE 8000

# Run using uv's environment
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
