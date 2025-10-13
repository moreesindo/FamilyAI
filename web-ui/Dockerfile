# syntax=docker/dockerfile:1.6
ARG BASE_IMAGE=ghcr.io/dusty-nv/jetson-containers:open-webui
FROM ${BASE_IMAGE} AS runtime

ENV GATEWAY_URL=http://gateway:8080

WORKDIR /app

COPY config/settings.json /app/config/settings.json

EXPOSE 3000
CMD ["npm", "run", "start"]
