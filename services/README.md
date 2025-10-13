# Services Directory

Place new microservices under this directory using the structure:

```
services/<name>/
├── Dockerfile
├── README.md
├── src/
└── k3s/
```

Ensure Dockerfiles inherit from `jetson-containers` base images and include health endpoints for the gateway to probe.
