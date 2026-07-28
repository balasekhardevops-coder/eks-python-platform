import base64
import json
import os
import socket
import time
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI(
    title="EKS Python Application",
    description=(
        "Production-style FastAPI application running on Amazon EKS "
        "with S3 and AWS Secrets Manager integration"
    ),
    version="1.1.0",
)

START_TIME = time.time()

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_OBJECT_KEY = os.getenv("S3_OBJECT_KEY")
SECRET_NAME = os.getenv("SECRET_NAME")
APP_PORT = int(os.getenv("PORT", "9010"))

# Do not pass aws_access_key_id or aws_secret_access_key.
# Boto3 obtains temporary credentials from IRSA automatically.
AWS_SESSION = boto3.session.Session(region_name=AWS_REGION)

s3_client = AWS_SESSION.client("s3")
secrets_client = AWS_SESSION.client("secretsmanager")


class User(BaseModel):
    name: str
    email: str


def require_environment_variable(name: str, value: str | None) -> str:
    if not value:
        raise HTTPException(
            status_code=500,
            detail=f"Required environment variable {name} is not configured",
        )

    return value


def aws_error_detail(error: ClientError) -> str:
    response = error.response.get("Error", {})

    error_code = response.get("Code", "Unknown")
    error_message = response.get("Message", "AWS request failed")

    return f"{error_code}: {error_message}"


def parse_secret_response(response: dict[str, Any]) -> Any:
    if "SecretString" in response:
        secret_value = response["SecretString"]

        try:
            return json.loads(secret_value)
        except json.JSONDecodeError:
            return secret_value

    if "SecretBinary" in response:
        binary_secret = response["SecretBinary"]

        if isinstance(binary_secret, str):
            binary_secret = base64.b64decode(binary_secret)

        return binary_secret.decode("utf-8")

    raise HTTPException(
        status_code=500,
        detail="Secret response did not contain SecretString or SecretBinary",
    )


@app.get("/")
def root() -> dict:
    return {
        "message": "Python application is running on EKS",
        "version": os.getenv("APP_VERSION", "local"),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "pod_name": socket.gethostname(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "port": APP_PORT,
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
        "aws_region": AWS_REGION,
        "s3_bucket_configured": bool(S3_BUCKET_NAME),
        "secret_configured": bool(SECRET_NAME),
        "port": APP_PORT,
    }


@app.get("/aws/s3")
def read_s3_object(
    object_key: str | None = Query(
        default=None,
        description="S3 object key. Uses S3_OBJECT_KEY when omitted.",
    ),
) -> dict:
    bucket_name = require_environment_variable(
        "S3_BUCKET_NAME",
        S3_BUCKET_NAME,
    )

    selected_object_key = object_key or S3_OBJECT_KEY

    selected_object_key = require_environment_variable(
        "S3_OBJECT_KEY",
        selected_object_key,
    )

    try:
        response = s3_client.get_object(
            Bucket=bucket_name,
            Key=selected_object_key,
        )

        raw_content = response["Body"].read()

        try:
            content = raw_content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=415,
                detail="S3 object is not a UTF-8 text file",
            )

        content_type = response.get(
            "ContentType",
            "application/octet-stream",
        )

        if content_type == "application/json":
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                pass

        return {
            "bucket": bucket_name,
            "object_key": selected_object_key,
            "content_type": content_type,
            "content_length": response.get("ContentLength"),
            "last_modified": (
                response["LastModified"].isoformat()
                if response.get("LastModified")
                else None
            ),
            "etag": response.get("ETag"),
            "content": content,
            "pod_name": socket.gethostname(),
        }

    except s3_client.exceptions.NoSuchKey:
        raise HTTPException(
            status_code=404,
            detail=f"S3 object '{selected_object_key}' was not found",
        )

    except s3_client.exceptions.NoSuchBucket:
        raise HTTPException(
            status_code=404,
            detail=f"S3 bucket '{bucket_name}' was not found",
        )

    except ClientError as error:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to read S3 object: {aws_error_detail(error)}",
        )

    except BotoCoreError as error:
        raise HTTPException(
            status_code=502,
            detail=f"AWS SDK error while reading S3: {str(error)}",
        )


@app.get("/aws/secret")
def read_secret(
    secret_name: str | None = Query(
        default=None,
        description="Secret name or ARN. Uses SECRET_NAME when omitted.",
    ),
    reveal: bool = Query(
        default=False,
        description="Return the secret value. Keep disabled in production.",
    ),
) -> dict:
    selected_secret_name = secret_name or SECRET_NAME

    selected_secret_name = require_environment_variable(
        "SECRET_NAME",
        selected_secret_name,
    )

    try:
        response = secrets_client.get_secret_value(
            SecretId=selected_secret_name,
        )

        secret_value = parse_secret_response(response)

        result: dict[str, Any] = {
            "secret_name": response.get("Name", selected_secret_name),
            "version_id": response.get("VersionId"),
            "version_stages": response.get("VersionStages", []),
            "created_date": (
                response["CreatedDate"].isoformat()
                if response.get("CreatedDate")
                else None
            ),
            "pod_name": socket.gethostname(),
        }

        if isinstance(secret_value, dict):
            result["secret_keys"] = list(secret_value.keys())
        else:
            result["secret_type"] = "string"

        # Avoid exposing secret values accidentally.
        if reveal:
            result["secret_value"] = secret_value
        else:
            result["secret_value"] = "REDACTED"

        return result

    except secrets_client.exceptions.ResourceNotFoundException:
        raise HTTPException(
            status_code=404,
            detail=f"Secret '{selected_secret_name}' was not found",
        )

    except secrets_client.exceptions.DecryptionFailure:
        raise HTTPException(
            status_code=502,
            detail="Secrets Manager could not decrypt the secret",
        )

    except ClientError as error:
        raise HTTPException(
            status_code=502,
            detail=(
                "Unable to retrieve Secrets Manager secret: "
                f"{aws_error_detail(error)}"
            ),
        )

    except BotoCoreError as error:
        raise HTTPException(
            status_code=502,
            detail=(
                "AWS SDK error while retrieving secret: "
                f"{str(error)}"
            ),
        )


@app.get("/cpu")
def cpu_load(iterations: int = 1_000_000) -> dict:
    if iterations < 1:
        raise HTTPException(
            status_code=400,
            detail="iterations must be greater than zero",
        )

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