FROM python:3.11-slim

WORKDIR /app

# 将仓库内的公共包一并复制并安装（构建上下文需包含仓库根）
COPY ../../packages/common /app/packages/common
RUN pip install --no-cache-dir /app/packages/common

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY src/ ./src/

EXPOSE 8000

CMD ["uvicorn", "privacy_compute.main:app", "--host", "0.0.0.0", "--port", "8000"]