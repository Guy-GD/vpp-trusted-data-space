FROM python:3.11-slim

WORKDIR /app

COPY packages/common /app/packages/common
COPY services/identity-did /app/services/identity-did

RUN python -m pip install --no-cache-dir \
    -e /app/packages/common \
    -e /app/services/identity-did

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "identity_did.main:app", "--host", "0.0.0.0", "--port", "8000"]
