FROM python:3.13

RUN pip install uv

WORKDIR /app

COPY backend/pyproject.toml backend/uv.lock ./backend/

RUN uv sync --project backend --no-install-project

COPY backend/ ./backend/
COPY data/ ./data/

EXPOSE 5000

CMD ["uv", "run", "--project", "backend", "python", "backend/src/main.py"]