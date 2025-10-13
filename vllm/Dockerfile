# syntax=docker/dockerfile:1.6
ARG BASE_IMAGE=nvcr.io/nvidia/tritonserver:25.08-vllm-python-py3
FROM ${BASE_IMAGE} AS runtime

ARG PROXY_URL=http://127.0.0.1:2526

ENV VLLM_WORKER_USE_NCCL=0 \
    VLLM_OPENAI_PORT=8000 \
    CUDA_VISIBLE_DEVICES=0

WORKDIR /app

COPY models.yaml ./models.yaml
COPY entrypoint.sh ./entrypoint.sh
RUN pip install --no-cache-dir pyyaml==6.0.1 huggingface-hub==0.23.3
RUN chmod +x /app/entrypoint.sh

ENV HTTP_PROXY=${PROXY_URL} \
    http_proxy=${PROXY_URL} \
    HTTPS_PROXY=${PROXY_URL} \
    https_proxy=${PROXY_URL} \
    NO_PROXY=localhost,127.0.0.1 \
    no_proxy=localhost,127.0.0.1

EXPOSE 8000
CMD ["/app/entrypoint.sh"]
