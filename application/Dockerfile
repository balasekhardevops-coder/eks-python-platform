FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=9010

WORKDIR /app

RUN groupadd --gid 10001 appgroup \
    && useradd \
        --uid 10001 \
        --gid appgroup \
        --no-create-home \
        --shell /usr/sbin/nologin \
        appuser

COPY requirements.txt ./requirements.txt

RUN python -m pip install \
    --requirement requirements.txt

COPY --chown=10001:10001 app ./app

USER 10001:10001

EXPOSE 9010

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.getenv('PORT', '9010') + '/health/live', timeout=3)" || exit 1

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-9010} --proxy-headers --forwarded-allow-ips='*' --timeout-keep-alive 65"]
