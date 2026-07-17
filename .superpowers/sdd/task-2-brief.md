# Task 2: 清零并锁定跨模块契约歧义

## 目标

复核并完成三份正式契约文档与契约测试，使第一周所有成员按同一 HTTP 字段和编排边界实现 Mock 服务。

## 所有权文件

- `docs/api/openapi.md`
- `docs/design/main-flow.md`
- `docs/design/module-contracts.md`
- `tests/integration/test_contract_docs.py`

不得修改 Task 1 的公共包、版本文件、README、`.gitignore` 或 `docs/api/response-and-errors.md`。

## 文档职责

- `main-flow.md`：跨模块顺序、数据边界、状态、存证节点和失败处理。
- `openapi.md`：全部 HTTP 路径、方法、请求字段、响应字段和示例。
- `module-contracts.md`：模块职责、输入输出、能力边界和接口清单。
- 统一响应、错误码、追踪和幂等只引用 `response-and-errors.md`，不得重复定义冲突规则。

## 必须冻结的决策

1. 第一周只有 `api-gateway` 负责跨模块编排；业务模块不直接写 `ledger-service`。
2. `POST /api/v1/fl/tasks/{taskId}/start` 成功 `data` 必须包含当前轮次 `updates[]`，每项至少有 `participantDid`、`sampleCount`、`modelUpdateUri`、`updateHash`。
3. 网关把 `updates` 交给 `POST /api/v1/privacy/secure-aggregate`；其响应至少含 `aggregateId`、`aggregateResultUri`、`aggregateHash`。
4. `POST /api/v1/fl/tasks/{taskId}/rounds/{roundId}/aggregate` 请求必须接收 `aggregateId`、`aggregateResultUri`、`aggregateHash`，再执行 FedAvg。
5. 主流程使用 `POST /api/v1/data/ingest`，该接口完成校验与资产登记并返回 `assetId`；`POST /api/v1/data/assets` 是独立元信息登记接口，不在一键主流程中，但仍需实现。
6. `POST /api/v1/demo/run` 的业务 `data` 至少包含 `businessId`、`metrics`、`predictionId`、`strategyId`、`auditReportId`、`ledgerTxIds`；完整响应的公共包络含 `traceId`，不得把 `traceId` 重复放入业务 `data`。
7. `POST /api/v1/agent/audit-question` 和 `/audit-report` 请求都包含 `businessId`、`modelVersion`、`evidenceEventIds[]`，并分别包含 `question`/`reportType`。证据 ID 由网关从账本查询后传入，Agent 不直接调用账本。
8. `openapi.md` 的接口覆盖矩阵与 `module-contracts.md` 对外接口必须保持一致。

## 测试与交付

复核 `tests/integration/test_contract_docs.py` 是否对上述冻结项进行有意义的文本契约验证，并运行：

```powershell
$python = 'C:\Users\David\AppData\Local\Temp\vpp-python311\python.exe'
$deps = 'C:\Users\David\AppData\Local\Temp\vpp-test-deps311'
$src = Join-Path (Get-Location) 'packages/common/src'
$env:PYTHONPATH = "$deps;$src"
& $python -m pytest tests/integration/test_contract_docs.py -q -p no:cacheprovider
```

只提交所有权文件，提交信息：`docs: freeze week-one module contracts`。
