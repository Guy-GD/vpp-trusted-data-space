# vpp-trusted-data-space OpenAPI 接口契约

> **文档职责**：本文档是系统 HTTP 接口的完整接口目录，覆盖 `docs/design/module-contracts.md` 列出的全部模块接口。它定义方法、路径、请求字段、响应字段、状态和调用示例；不改变模块职责和主流程。统一响应包络、错误码、追踪和幂等规则以 `docs/api/response-and-errors.md` 为单一来源。

> **一致性规则**：新增或修改接口时，必须同时更新本文档和 `docs/design/module-contracts.md`。接口路径、HTTP 方法、字段名或错误码不一致时，以评审通过后的最新版本为准，禁止只修改代码。

## 1. 基本约定

- API 前缀：`/api/v1`。
- 请求格式：`application/json`。
- 成功响应：`code = 0`，业务结果放在 `data`。
- 失败响应：`data = null`，客户端按 `code` 处理。
- 所有服务提供 `GET /health`。
- 时间字段使用 ISO 8601，例如 `2026-07-10T10:00:00+08:00`。
- DID 使用字符串，例如 `did:vpp:load-aggregator:001`。
- 哈希使用 `sha256:<hex>`，签名和密文使用 Base64 字符串。
- `traceId` 由网关生成并通过 `X-Trace-Id` 传递。
- 写操作建议使用 `Idempotency-Key`，具体规则见 [公共响应与错误码](./response-and-errors.md)。

## 2. 公共响应 Schema

成功响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {},
  "traceId": "trace_20260710_000001"
}
```

错误响应：

```json
{
  "code": 40001,
  "message": "invalid request",
  "data": null,
  "traceId": "trace_20260710_000001",
  "details": [{ "field": "participants", "reason": "must not be empty" }]
}
```

错误码完整目录、HTTP 映射、幂等和健康检查规则见 [response-and-errors.md](./response-and-errors.md)。

## 3. 接口覆盖矩阵

下表必须与 `module-contracts.md` 各模块“对外接口”章节一一对应。

| 模块 | 方法 | 路径 |
|---|---|---|
| api-gateway | POST | `/api/v1/demo/run` |
| api-gateway | GET | `/api/v1/demo/status/{businessId}` |
| meter-simulator | POST | `/api/v1/meter/readings/generate` |
| data-ingestion | POST | `/api/v1/data/ingest` |
| data-ingestion | POST | `/api/v1/data/assets` |
| data-ingestion | GET | `/api/v1/data/assets/{assetId}` |
| identity-did | POST | `/api/v1/identity/subjects` |
| identity-did | POST | `/api/v1/identity/devices` |
| identity-did | POST | `/api/v1/identity/verify` |
| identity-did | POST | `/api/v1/auth/requests` |
| identity-did | POST | `/api/v1/auth/requests/{authId}/approve` |
| identity-did | GET | `/api/v1/auth/requests/{authId}` |
| federated-learning | POST | `/api/v1/fl/tasks` |
| federated-learning | POST | `/api/v1/fl/tasks/{taskId}/start` |
| federated-learning | POST | `/api/v1/fl/tasks/{taskId}/rounds/{roundId}/updates` |
| federated-learning | POST | `/api/v1/fl/tasks/{taskId}/rounds/{roundId}/aggregate` |
| federated-learning | GET | `/api/v1/fl/tasks/{taskId}` |
| federated-learning | GET | `/api/v1/fl/tasks/{taskId}/metrics` |
| federated-learning | GET | `/api/v1/fl/models/{modelVersion}` |
| privacy-compute | POST | `/api/v1/privacy/model-updates/encrypt` |
| privacy-compute | POST | `/api/v1/privacy/model-updates/mask` |
| privacy-compute | POST | `/api/v1/privacy/secure-aggregate` |
| privacy-compute | GET | `/api/v1/privacy/aggregates/{aggregateId}` |
| ledger-service | POST | `/api/v1/ledger/events` |
| ledger-service | GET | `/api/v1/ledger/events/{eventId}` |
| ledger-service | GET | `/api/v1/ledger/traces/{businessId}` |
| ai-agent | POST | `/api/v1/agent/predict` |
| ai-agent | POST | `/api/v1/agent/trading-strategy` |
| ai-agent | POST | `/api/v1/agent/audit-question` |
| ai-agent | POST | `/api/v1/agent/audit-report` |
| 所有服务 | GET | `/health` |

## 4. api-gateway

### `POST /api/v1/demo/run`

启动完整演示流程，由网关依次调用采集、接入、身份授权、训练、隐私计算、存证和 Agent 模块。

请求体：

```json
{
  "scenario": "vpp_day_ahead_trading",
  "participants": ["did:vpp:load-aggregator:001", "did:vpp:renewable-plant:001", "did:vpp:storage:001"],
  "meterCount": 3,
  "trainingRounds": 3
}
```

成功 `data`：

```json
{
  "businessId": "demo_001",
  "readingBatchId": "batch_001",
  "assetId": "asset_001",
  "authId": "auth_001",
  "trainingTaskId": "fl_task_001",
  "globalModelVersion": "global_model_v1",
  "metrics": { "mae": 2.31, "rmse": 3.72, "mape": 0.081 },
  "predictionId": "prediction_001",
  "auditReportId": "report_001",
  "ledgerTxIds": ["tx_data_001", "tx_auth_001", "tx_model_001", "tx_agent_001"]
}
```

可能错误：`40001`、`40102`、`40302`、`42201`、`50203`、`50401`。

### `GET /api/v1/demo/status/{businessId}`

查询演示业务状态，不重复执行流程。成功 `data` 返回 `businessId`、`status`、`currentStage`、`lastEventType`、`globalModelVersion`、`retryable` 和 `error`。

可能错误：`40001`、`40402`。

## 5. meter-simulator

### `POST /api/v1/meter/readings/generate`

请求：`meterId`、`ownerDid`、`count`、`intervalSeconds`。

成功 `data`：

```json
{
  "readingBatchId": "batch_001",
  "readings": [{
    "readingId": "reading_001",
    "meterId": "meter_001",
    "ownerDid": "did:vpp:load-aggregator:001",
    "ciphertext": "base64-ciphertext",
    "signature": "base64-signature",
    "hash": "sha256:abc123",
    "timestamp": "2026-07-10T10:00:00+08:00"
  }]
}
```

可能错误：`40001`、`40002`、`40102`、`50001`。

## 6. data-ingestion

### `POST /api/v1/data/ingest`

接收密文批次并完成签名、哈希校验。请求包含 `readingBatchId`、`ownerDid`、`readings[]`；每条 reading 至少包含 `readingId`、`meterId`、`ciphertext`、`signature`、`hash`、`timestamp`。

成功 `data`：`assetId`、`readingBatchId`、`ownerDid`、`assetType`、`sensitivityLevel`、`status`。

可能错误：`40001`、`40103`、`40104`、`40902`。

### `POST /api/v1/data/assets`

登记资产元信息。请求至少包含 `readingBatchId`、`ownerDid`、`assetType`、`sensitivityLevel`、`purpose`；成功返回资产登记结果。

可能错误：`40002`、`40102`、`40301`、`40901`。

### `GET /api/v1/data/assets/{assetId}`

查询资产元信息；响应不得返回原始明文或未保护模型参数。成功返回 `assetId`、`ownerDid`、`assetType`、`sensitivityLevel`、`status`、`createdAt`。

可能错误：`40101`、`40301`、`40401`。

## 7. identity-did

### `POST /api/v1/identity/subjects`

请求：`name`、`type`、`publicKey`。成功返回 `subjectDid`、`name`、`type`、`status`、`createdAt`。

### `POST /api/v1/identity/devices`

请求：`deviceName`、`deviceType`、`ownerDid`、`publicKey`。成功返回 `deviceDid`、`ownerDid`、`status`、`createdAt`。

### `POST /api/v1/identity/verify`

请求：`subjectDid` 或 `deviceDid`，以及验签所需的 `signature`、`payloadHash`。成功返回 `valid`、`did`、`subjectType`。

### `POST /api/v1/auth/requests`

请求：`requesterDid`、`ownerDid`、`assetId`、`purpose`、`expireAt`。成功返回 `authId`、`status`、双方 DID、资产和用途。

### `POST /api/v1/auth/requests/{authId}/approve`

请求：`approverDid`，可选 `decision` 和 `reason`。成功返回授权记录及 `status: approved`。

### `GET /api/v1/auth/requests/{authId}`

查询授权申请完整记录和当前状态。

以上接口可能错误：`40001`、`40002`、`40102`、`40301`、`40303`、`40401`、`40902`。

## 8. federated-learning

### `POST /api/v1/fl/tasks`

请求字段：`taskName`、`modelType`、`algorithm`、`rounds`、`participants[]`、`assetIds[]`、`target`。成功返回 `trainingTaskId`、`status: created`、轮次和参与方。

### `POST /api/v1/fl/tasks/{taskId}/start`

启动任务；请求可选 `startRound`，成功返回 `trainingTaskId`、`status: running`、`currentRound`。

### `POST /api/v1/fl/tasks/{taskId}/rounds/{roundId}/updates`

请求：`participantDid`、`sampleCount`、`modelUpdateUri`、`updateHash`。成功返回提交状态。

### `POST /api/v1/fl/tasks/{taskId}/rounds/{roundId}/aggregate`

触发安全聚合和 FedAvg。成功 `data`：

```json
{
  "trainingTaskId": "fl_task_001",
  "roundId": 3,
  "globalModelVersion": "global_model_v1",
  "modelHash": "sha256:model123",
  "participantCount": 3,
  "metrics": { "mae": 2.31, "rmse": 3.72, "mape": 0.081 }
}
```

### `GET /api/v1/fl/tasks/{taskId}`

返回任务状态、当前轮次、参与方、模型版本和最近错误。

### `GET /api/v1/fl/tasks/{taskId}/metrics`

返回按轮次记录的 `mae`、`rmse`、`mape` 和样本数。

### `GET /api/v1/fl/models/{modelVersion}`

返回模型元信息、模型哈希、训练任务、轮次、指标和模型 URI；不得返回未授权的原始参数。

以上接口可能错误：`40001`、`40102`、`40302`、`40403`、`40404`、`40902`、`42201`、`42202`、`42204`、`42901`。

## 9. privacy-compute

### `POST /api/v1/privacy/model-updates/encrypt`

请求：`trainingTaskId`、`roundId`、`updates[]`、`algorithm`。成功返回加密更新摘要、结果 URI 和 `privacyMode: homomorphic_demo`。

### `POST /api/v1/privacy/model-updates/mask`

请求结构与 encrypt 相同；成功返回安全掩码更新摘要、结果 URI 和 `privacyMode: secure_masking`。

### `POST /api/v1/privacy/secure-aggregate`

请求：`trainingTaskId`、`roundId`、`updates[]`、`privacyMode`。成功 `data`：

```json
{
  "aggregateId": "aggregate_001",
  "trainingTaskId": "fl_task_001",
  "roundId": 1,
  "aggregateResultUri": "storage://aggregates/fl_task_001/round_1/result.json",
  "aggregateHash": "sha256:agg001",
  "participantCount": 3,
  "privacyMode": "secure_masking"
}
```

### `GET /api/v1/privacy/aggregates/{aggregateId}`

返回聚合元信息、参与方数量、隐私模式、结果 URI 和摘要哈希；不返回单个参与方明文更新。

以上接口可能错误：`40001`、`40102`、`40302`、`40401`、`42202`、`42203`、`50001`。

## 10. ledger-service

### `POST /api/v1/ledger/events`

请求字段：`eventType`、`businessId`、`subjectDid`、`payloadHash`、`payloadUri`、`description`、`metadata`。成功 `data` 返回 `ledgerTxId`、`eventId`、`blockHeight`、`currentHash`。

### `GET /api/v1/ledger/events/{eventId}`

返回单个事件、交易 ID、区块高度、当前哈希、前序哈希和元数据。

### `GET /api/v1/ledger/traces/{businessId}`

返回按时间排序的完整证据链：事件 ID、事件类型、时间、摘要哈希、交易 ID、区块高度和链路状态。

以上接口可能错误：`40001`、`40002`、`40401`、`40402`、`40903`、`50002`。

## 11. ai-agent

### `POST /api/v1/agent/predict`

请求：`modelVersion`、`scenario`、`input`。成功返回 `predictionId`、`modelVersion`、`predictedCapacityKw`、`confidence`。

### `POST /api/v1/agent/trading-strategy`

请求：`predictionId`、`scenario`、`marketPrice`、`riskPreference`。成功返回 `strategyId`、申报容量、价格建议、安全裕度和解释。

### `POST /api/v1/agent/audit-question`

请求：`businessId`、`question`。成功返回 `answer`、`evidenceEventIds`、`confidence`。

### `POST /api/v1/agent/audit-report`

请求：`businessId`、`reportType`。成功 `data`：

```json
{
  "auditReportId": "report_001",
  "title": "虚拟电厂日前交易审计报告",
  "summary": "本次交易使用 global_model_v1 完成可调节容量预测，参与主体 3 个，原始数据未出域，关键操作均已存证。",
  "riskLevel": "low",
  "recommendations": ["建议申报可调节容量 120MW", "建议保留 10% 安全裕度"]
}
```

以上接口可能错误：`40001`、`40002`、`40302`、`40401`、`40404`、`40902`、`50201`。

## 12. 所有服务健康检查

每个后端服务均提供 `GET /health`。成功 `data`：`{ "service": "service-name", "status": "healthy" }`；未就绪时返回 HTTP `503` 和业务码 `50301`/`50302`，仍使用统一响应包络。

## 13. 接口变更规则

1. 修改路径、方法、字段、枚举、状态或错误码前，先修改本文档。
2. 同步修改 `docs/design/module-contracts.md` 对应模块章节。
3. 如果修改影响跨模块时序，再修改 `docs/design/main-flow.md`。
4. 通过接口覆盖矩阵检查后，才能进入代码实现。
5. 任何新增接口必须补充成功示例、至少一个失败示例和幂等说明。
