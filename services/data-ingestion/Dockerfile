FROM python:3.11-slim

WORKDIR /app

COPY packages/common /app/packages/common
COPY services/data-ingestion /app/services/data-ingestion

ARG PIP_INDEX_URL=https://pypi.org/simple/
ARG PIP_TRUSTED_HOST=

RUN pip install --no-cache-dir \
    -i ${PIP_INDEX_URL} \
    ${PIP_TRUSTED_HOST:+--trusted-host ${PIP_TRUSTED_HOST}} \
    -e packages/common \
    -e "services/data-ingestion"

EXPOSE 8000

CMD ["uvicorn", "data_ingestion.main:app", "--host", "0.0.0.0", "--port", "8000"]
