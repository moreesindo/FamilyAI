# syntax=docker/dockerfile:1.6
ARG BASE_IMAGE=node:20-alpine
FROM ${BASE_IMAGE} AS builder

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS runtime
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
