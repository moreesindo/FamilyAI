# syntax=docker/dockerfile:1.6
ARG BASE_IMAGE=ghcr.io/dusty-nv/jetson-containers:whisper
FROM ${BASE_IMAGE} AS runtime

ENV PYTHONUNBUFFERED=1 \
    MODEL_NAME=small \
    TORCH_HOME=/models/torch

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --extra-index-url https://pypi.org/simple --no-cache-dir -r requirements.txt

COPY serve.py ./serve.py

EXPOSE 8500
CMD ["python3", "serve.py"]
