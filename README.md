# EKS Python Platform

The FastAPI container listens on port **9010** by default.

## Run locally with Docker Compose

```bash
docker compose up --build
```

Open:

- `http://localhost:9010/`
- `http://localhost:9010/health/live`
- `http://localhost:9010/health/ready`
- `http://localhost:9010/docs`

## Run with Docker

```bash
docker build -t eks-python-app:local application
docker run --rm -p 9010:9010 -e PORT=9010 eks-python-app:local
```

## Kubernetes/Helm alignment

The workload must use port 9010 at every layer:

- container `PORT=9010`
- Deployment `containerPort: 9010`
- Service `port: 9010` and `targetPort: 9010`
- readiness probe `/health/ready` on port 9010
- liveness probe `/health/live` on port 9010

See `kubernetes/port-9010-values.yaml` for a values example.
