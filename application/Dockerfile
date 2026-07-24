FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

RUN groupadd --gid 10001 appgroup \
    && useradd \
    --uid 10001 \
    --gid appgroup \
    --no-create-home \
    appuser

COPY requirements.txt .

RUN pip install \
    --no-cache-dir \
    --requirement requirements.txt

COPY app ./app

USER 10001:10001

EXPOSE 8080

CMD ["uvicorn", \
    "app.main:app", \
    "--host", "0.0.0.0", \
    "--port", "8080", \
    "--proxy-headers"]