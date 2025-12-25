# syntax=docker/dockerfile:1.7-labs

FROM python:3.11.9-slim AS build
WORKDIR /app
COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache \
    pip install --no-cache-dir --upgrade pip==24.2 && \
    pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements.txt

FROM python:3.11.9-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
RUN groupadd -r app && useradd -r -g app -u 10001 app
COPY --from=build /wheels /wheels
RUN --mount=type=cache,target=/root/.cache \
    pip install --no-cache-dir /wheels/*
COPY --chown=app:app app /app/app
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health').read()"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
