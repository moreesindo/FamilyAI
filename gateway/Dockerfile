# syntax=docker/dockerfile:1.6
ARG BASE_IMAGE=ghcr.io/dusty-nv/jetson-containers:fastapi
FROM ${BASE_IMAGE} AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --extra-index-url https://pypi.org/simple --no-cache-dir -r requirements.txt

COPY app ./app
COPY config ./config

ENV GATEWAY_PORT=8080 \
    ROUTING_CONFIG=/app/config/routing.yaml \
    LOG_LEVEL=info

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
