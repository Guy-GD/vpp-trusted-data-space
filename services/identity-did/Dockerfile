FROM python:3.11-slim

WORKDIR /app

COPY packages/common/pyproject.toml /app/packages/common/pyproject.toml
COPY packages/common/README.md /app/packages/common/README.md
COPY packages/common/src /app/packages/common/src
COPY services/identity-did/pyproject.toml /app/services/identity-did/pyproject.toml
COPY services/identity-did/src /app/services/identity-did/src

RUN python -m pip install --no-cache-dir \
    -e /app/packages/common \
    -e /app/services/identity-did

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "identity_did.main:app", "--host", "0.0.0.0", "--port", "8000"]
