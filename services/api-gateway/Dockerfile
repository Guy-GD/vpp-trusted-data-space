FROM python:3.11-slim
WORKDIR /app
COPY packages/common /app/packages/common
RUN python -m pip install --no-cache-dir -e "/app/packages/common[test]"
COPY services/api-gateway /app/services/api-gateway
RUN python -m pip install --no-cache-dir -e "/app/services/api-gateway[test]"
WORKDIR /app/services/api-gateway
EXPOSE 8000
CMD ["uvicorn", "api_gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]