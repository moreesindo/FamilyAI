# syntax=docker/dockerfile:1.6
ARG BASE_IMAGE=ghcr.io/dusty-nv/jetson-containers:fastapi
FROM ${BASE_IMAGE} AS runtime

WORKDIR /app

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt ./requirements.txt
RUN pip install --extra-index-url https://pypi.org/simple --no-cache-dir -r requirements.txt

COPY app ./app
COPY config ./config

EXPOSE 9000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000"]
