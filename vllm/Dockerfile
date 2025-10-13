# syntax=docker/dockerfile:1.6
ARG BASE_IMAGE=ghcr.io/dusty-nv/jetson-containers:vllm
FROM ${BASE_IMAGE} AS runtime

ENV VLLM_WORKER_USE_NCCL=0 \
    VLLM_OPENAI_PORT=8000 \
    CUDA_VISIBLE_DEVICES=0

WORKDIR /app

COPY models.yaml ./models.yaml
COPY entrypoint.sh ./entrypoint.sh
RUN pip install --extra-index-url https://pypi.org/simple pyyaml==6.0.1
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
CMD ["/app/entrypoint.sh"]
