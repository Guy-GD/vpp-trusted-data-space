# api-gateway

虚拟电厂可信数据空间协同计算与审计平台 —— 统一编排网关（模块 0）。

## 职责

- 统一演示入口：POST /api/v1/demo/run
- 工作流状态查询：GET /api/v1/demo/status/{businessId}
- 健康检查：GET /api/v1/health
- 编排 7 个下游服务：meter-simulator / data-ingestion / identity-did / federated-learning / privacy-compute / ledger-service / ai-agent

## 技术基线

Python 3.11 + FastAPI + Pydantic v2 + httpx + pytest，依赖仓库内 vpp-common==0.1.0。

## 本地启动

在仓库根目录（已激活 .venv）：

python -m pip install -e "packages/common[test]"
python -m pip install -e "services/api-gateway[test]"
uvicorn api_gateway.main:app --host 0.0.0.0 --port 8000 --reload

启动后访问 http://127.0.0.1:8000/docs 查看 Swagger。

## 测试

python -m pytest services/api-gateway/tests -v

预期：8 passed。

## 接口示例（curl）

健康检查：
curl http://127.0.0.1:8000/api/v1/health

触发演示工作流：
curl -X POST http://127.0.0.1:8000/api/v1/demo/run -H "Content-Type: application/json" -d '{"scenario":"vpp_day_ahead_trading","participants":["aggregator-A","energy-user-B"],"meterCount":3,"trainingRounds":2}'

查询状态（用返回的 businessId）：
curl http://127.0.0.1:8000/api/v1/demo/status/<businessId>

> 提示：PowerShell 里 curl 是 Invoke-WebRequest 的别名，如需原生 curl 请用 curl.exe。

## 边界与说明

- 审计存证是 ledger-service 的职责，网关不实现本地审计。
- 下游服务未启动时，POST /api/v1/demo/run 返回 50203（符合契约，非 bug）。
- 幂等记录与工作流状态均为内存存储，服务重启后丢失（Week 1 范围）。
- 编排为 7 阶段骨架；15 步细分为后续任务。