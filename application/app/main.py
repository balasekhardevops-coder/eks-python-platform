import os
import socket
import time
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="EKS Python Application",
    description="Production-style FastAPI application running on Amazon EKS",
    version="1.0.0",
)

START_TIME = time.time()


class User(BaseModel):
    name: str
    email: str


@app.get("/")
def root() -> dict:
    return {
        "message": "Python application is running on EKS",
        "version": os.getenv("APP_VERSION", "local"),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "pod_name": socket.gethostname(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health/live")
def liveness() -> dict:
    return {
        "status": "alive",
    }


@app.get("/health/ready")
def readiness() -> dict:
    return {
        "status": "ready",
    }


@app.get("/info")
def application_info() -> dict:
    return {
        "application": "eks-python-app",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "version": os.getenv("APP_VERSION", "local"),
        "pod_name": socket.gethostname(),
        "uptime_seconds": round(time.time() - START_TIME, 2),
    }


@app.get("/cpu")
def cpu_load(iterations: int = 1_000_000) -> dict:
    if iterations > 20_000_000:
        raise HTTPException(
            status_code=400,
            detail="iterations cannot exceed 20000000",
        )

    result = 0

    for number in range(iterations):
        result += number * number

    return {
        "iterations": iterations,
        "result": result,
        "pod_name": socket.gethostname(),
    }


@app.post("/users", status_code=201)
def create_user(user: User) -> dict:
    return {
        "message": "User created",
        "user": user.model_dump(),
        "pod_name": socket.gethostname(),
    }