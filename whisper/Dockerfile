# syntax=docker/dockerfile:1.6
ARG WHISPER_BASE_IMAGE=${WHISPER_BASE_IMAGE:nvcr.io/nvidia/l4t-pytorch}
ARG WHISPER_BASE_TAG=${WHISPER_BASE_TAG:r35.2.1-pth2.0-py3}
ARG PROXY_URL
FROM ${WHISPER_BASE_IMAGE}:${WHISPER_BASE_TAG} AS runtime

ARG PROXY_URL
ENV PYTHONUNBUFFERED=1 \
    MODEL_NAME=small \
    TORCH_HOME=/models/torch

# Install runtime dependencies (ffmpeg and libsndfile for audio I/O)
RUN set -eux; \
    if [ -n "${PROXY_URL}" ]; then \
      export http_proxy="${PROXY_URL}" https_proxy="${PROXY_URL}" HTTP_PROXY="${PROXY_URL}" HTTPS_PROXY="${PROXY_URL}"; \
    fi; \
    apt-get update; \
    apt-get install -y --no-install-recommends ffmpeg libsndfile1; \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
RUN set -eux; \
    if [ -n "${PROXY_URL}" ]; then \
      export http_proxy="${PROXY_URL}" https_proxy="${PROXY_URL}" HTTP_PROXY="${PROXY_URL}" HTTPS_PROXY="${PROXY_URL}"; \
    fi; \
    pip install --extra-index-url https://pypi.org/simple --no-cache-dir -r /tmp/requirements.txt; \
    rm -f /tmp/requirements.txt

COPY serve.py ./serve.py

EXPOSE 8500
CMD ["python3", "serve.py"]
