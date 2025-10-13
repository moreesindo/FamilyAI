# syntax=docker/dockerfile:1.6
ARG BASE_IMAGE=nvcr.io/nvidia/tritonserver:25.08-vllm-python-py3
FROM ${BASE_IMAGE} AS runtime

ENV VLLM_WORKER_USE_NCCL=0 \
    VLLM_OPENAI_PORT=8000 \
    CUDA_VISIBLE_DEVICES=0 \
    HTTP_PROXY=http://127.0.0.1:2526 \
    http_proxy=http://127.0.0.1:2526 \
    HTTPS_PROXY=http://127.0.0.1:2526 \
    https_proxy=http://127.0.0.1:2526 \
    NO_PROXY=localhost,127.0.0.1 \
    no_proxy=localhost,127.0.0.1

WORKDIR /app

COPY models.yaml ./models.yaml
COPY entrypoint.sh ./entrypoint.sh
RUN pip install --extra-index-url https://pypi.org/simple pyyaml==6.0.1 huggingface-hub==0.23.3
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
CMD ["/app/entrypoint.sh"]
