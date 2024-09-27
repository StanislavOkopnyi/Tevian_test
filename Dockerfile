FROM python:3.11

WORKDIR /usr/src/app

RUN pip install uv

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

COPY app/ ./
COPY pyproject.toml ./
COPY uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

ENV PATH="/usr/src/app/.venv/bin:$PATH"

ENTRYPOINT []

CMD ["python", "-m", "fastapi", "dev", "--host", "0.0.0.0", "main.py"]
