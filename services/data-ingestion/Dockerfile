FROM python:3.11-slim

WORKDIR /app

COPY packages/common /app/packages/common
COPY services/data-ingestion /app/services/data-ingestion

RUN pip install --no-cache-dir \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com \
    -e packages/common \
    -e "services/data-ingestion"

EXPOSE 8000

CMD ["uvicorn", "data_ingestion.main:app", "--host", "0.0.0.0", "--port", "8000"]
