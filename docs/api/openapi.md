# vpp-trusted-data-space OpenAPI 接口契约

> **文档职责**：本文档是系统 HTTP 接口的完整接口目录，覆盖 `docs/design/module-contracts.md` 列出的全部模块接口。它定义方法、路径、请求字段、响应字段、状态和调用示例；不改变模块职责和主流程。统一响应包络、错误码、追踪和幂等规则以 `docs/api/response-and-errors.md` 为单一来源。

> **一致性规则**：新增或修改接口时，必须同时更新本文档和 `docs/design/module-contracts.md`。接口路径、HTTP 方法、字段名或错误码不一致时，以评审通过后的最新版本为准，禁止只修改代码。

## 1. 基本约定

- API 前缀：`/api/v1`。
- 请求格式：`application/json`。
- 所有服务提供 `GET /health`。
- 时间字段使用 ISO 8601，例如 `2026-07-10T10:00:00+08:00`。
- DID 使用字符串，例如 `did:vpp:load-aggregator:001`。
- 哈希使用 `sha256:<hex>`，签名和密文使用 Base64 字符串。
- 统一响应、错误码、追踪和幂等规则只引用 [公共响应与错误码](./response-and-errors.md)；本文档只定义端点的业务字段和示例。

## 2. 公共契约引用

统一响应包络、错误码、`traceId`、`Idempotency-Key` 和健康检查规则均以 [公共响应与错误码](./response-and-errors.md) 为准。端点的成功 `data` 示例只展示业务字段；例如一键演示的完整响应按第 4 节说明在公共包络中携带 `traceId`。

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

**请求说明**：JSON 请求体使用 `DemoRunRequest`，字段均来自请求体。

**字段类型与必填性**：`scenario: string`、`participants: array<string>`、`meterCount: integer`、`trainingRounds: integer` 均必填。

请求：

```json
{
  "scenario": "vpp_day_ahead_trading",
  "participants": ["did:vpp:load-aggregator:001", "did:vpp:renewable-plant:001", "did:vpp:storage:001"],
  "meterCount": 3,
  "trainingRounds": 3
}
```

**成功说明**：`data` 为下列可解析 JSON，包含完整演示链路标识、指标与存证交易 ID。

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
  "strategyId": "strategy_001",
  "auditReportId": "report_001",
  "ledgerTxIds": ["tx_data_001", "tx_auth_001", "tx_model_001", "tx_agent_001"]
}
```

完整成功响应还必须在公共包络中包含与响应头 `X-Trace-Id` 相同的 `traceId`。`businessId`、模型指标、三个 Agent 结果标识和存证交易 ID 均为冻结字段。

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的请求校验、身份授权、状态冲突及下游错误。

**幂等规则**：适用；调用方必须传 `Idempotency-Key`，相同 Key 与相同请求体复用首次结果，冲突按[公共响应与错误码](./response-and-errors.md)处理。

### `GET /api/v1/demo/status/{businessId}`

查询演示业务状态，不重复执行流程。成功 `data` 返回 `businessId`、`status`、`currentStage`、`lastEventType`、`globalModelVersion`、`retryable` 和 `error`。

**请求说明**：`businessId` 来自路径；无请求体。

**字段类型与必填性**：路径参数 `businessId: string` 必填。

**成功说明**：`data` 为 object，包含 `businessId: string`、`status: string`、`currentStage: string`、`lastEventType: string|null`、`globalModelVersion: string|null`、`retryable: boolean`、`error: object|null`。

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的业务不存在和通用服务错误。

**幂等规则**：不适用；该接口为只读查询。

## 5. meter-simulator

### `POST /api/v1/meter/readings/generate`

请求：`meterId`、`ownerDid`、`count`、`intervalSeconds`。

**请求说明**：JSON 请求体使用 `GenerateReadingsRequest`，字段均来自请求体。

**字段类型与必填性**：`meterId: string`、`ownerDid: string`、`count: integer`、`intervalSeconds: integer` 均必填。

**成功说明**：`data` 为下列 JSON；`readings` 是读数对象数组。

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

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的请求校验、DID 和服务错误。

**幂等规则**：适用；相同 `Idempotency-Key` 与相同请求体返回同一 `readingBatchId`，冲突按[公共响应与错误码](./response-and-errors.md)处理。

## 6. data-ingestion

### `POST /api/v1/data/ingest`

主流程使用本接口接收密文批次、完成签名与哈希校验，并同时登记数据资产。请求包含 `readingBatchId`、`ownerDid`、`readings[]`；每条 reading 至少包含 `readingId`、`meterId`、`ciphertext`、`signature`、`hash`、`timestamp`。

**请求说明**：JSON 请求体使用 `DataIngestRequest`；所有字段来自请求体。

**字段类型与必填性**：`readingBatchId: string`、`ownerDid: string`、`readings: array<object>` 必填；每项的 `readingId: string`、`meterId: string`、`ciphertext: string`、`signature: string`、`hash: string`、`timestamp: string(date-time)` 均必填。

成功 `data`：`assetId`、`readingBatchId`、`ownerDid`、`assetType`、`sensitivityLevel`、`status`。

**成功说明**：`data` 为 object，字段为 `assetId: string`、`readingBatchId: string`、`ownerDid: string`、`assetType: string`、`sensitivityLevel: string`、`status: string`。

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的请求校验、无效签名、无效哈希和状态冲突。

**幂等规则**：适用；相同 `Idempotency-Key` 与相同批次返回同一 `assetId`，冲突按[公共响应与错误码](./response-and-errors.md)处理。

### `POST /api/v1/data/assets`

独立登记资产元信息，不属于第一周一键演示主流程，也不要求再次提交读数。请求至少包含 `readingBatchId`、`ownerDid`、`assetType`、`sensitivityLevel`、`purpose`；成功返回资产登记结果。

**请求说明**：JSON 请求体使用 `CreateAssetRequest`；所有字段来自请求体。

**字段类型与必填性**：`readingBatchId: string`、`ownerDid: string`、`assetType: string`、`sensitivityLevel: string`、`purpose: string` 均必填。

**成功说明**：`data` 为 object，包含 `assetId: string`、上述资产元信息、`status: string` 与 `createdAt: string(date-time)`。

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的请求校验、DID、重复资源和服务错误。

**幂等规则**：适用；相同 `Idempotency-Key` 与相同请求体复用首次资产登记结果，冲突按[公共响应与错误码](./response-and-errors.md)处理。

### `GET /api/v1/data/assets/{assetId}`

查询资产元信息；响应不得返回原始明文或未保护模型参数。成功返回 `assetId`、`ownerDid`、`assetType`、`sensitivityLevel`、`status`、`createdAt`。

**请求说明**：`assetId` 来自路径；无请求体。

**字段类型与必填性**：路径参数 `assetId: string` 必填。

**成功说明**：`data` 为 object，包含 `assetId: string`、`ownerDid: string`、`assetType: string`、`sensitivityLevel: string`、`status: string`、`createdAt: string(date-time)`。

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的资源不存在、访问拒绝和服务错误。

**幂等规则**：不适用；该接口为只读查询。

## 7. identity-did

### `POST /api/v1/identity/subjects`

请求：`name`、`type`、`publicKey`。成功返回 `subjectDid`、`name`、`type`、`status`、`createdAt`。

**请求说明**：JSON 请求体使用 `CreateSubjectRequest`；所有字段来自请求体。

**字段类型与必填性**：`name: string`、`type: string`、`publicKey: string` 均必填。

**成功说明**：`data` 为 object，包含 `subjectDid: string`、`name: string`、`type: string`、`status: string`、`createdAt: string(date-time)`。

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的请求校验、DID 和状态冲突错误。

**幂等规则**：适用；相同 `Idempotency-Key` 与相同请求体返回同一 `subjectDid`，冲突按[公共响应与错误码](./response-and-errors.md)处理。

### `POST /api/v1/identity/devices`

请求：`deviceName`、`deviceType`、`ownerDid`、`publicKey`。成功返回 `deviceDid`、`ownerDid`、`status`、`createdAt`。

**请求说明**：JSON 请求体使用 `CreateDeviceRequest`；所有字段来自请求体。

**字段类型与必填性**：`deviceName: string`、`deviceType: string`、`ownerDid: string`、`publicKey: string` 均必填。

**成功说明**：`data` 为 object，包含 `deviceDid: string`、`ownerDid: string`、`status: string`、`createdAt: string(date-time)`。

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的请求校验、DID 和状态冲突错误。

**幂等规则**：适用；相同 `Idempotency-Key` 与相同请求体返回同一 `deviceDid`，冲突按[公共响应与错误码](./response-and-errors.md)处理。

### `POST /api/v1/identity/verify`

请求：`subjectDid` 或 `deviceDid`，以及验签所需的 `signature`、`payloadHash`。成功返回 `valid`、`did`、`subjectType`。

**请求说明**：JSON 请求体使用 `VerifyIdentityRequest`；身份字段与验签字段均来自请求体。

**字段类型与必填性**：`subjectDid: string` 与 `deviceDid: string` 二选一且必须提供一个；`signature: string`、`payloadHash: string` 必填。

**成功说明**：`data` 为 object，包含 `valid: boolean`、`did: string`、`subjectType: string`。

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的 DID、签名、哈希和请求校验错误。

**幂等规则**：适用；相同 `Idempotency-Key` 与相同请求体返回同一验证结果，冲突按[公共响应与错误码](./response-and-errors.md)处理。

### `POST /api/v1/auth/requests`

请求：`requesterDid`、`ownerDid`、`assetId`、`purpose`、`expireAt`。成功返回 `authId`、`status`、双方 DID、资产和用途。

**请求说明**：JSON 请求体使用 `CreateAuthRequest`；所有字段来自请求体。

**字段类型与必填性**：`requesterDid: string`、`ownerDid: string`、`assetId: string`、`purpose: string`、`expireAt: string(date-time)` 均必填。

**成功说明**：`data` 为 object，包含 `authId: string`、`status: string`、请求双方 DID、`assetId: string`、`purpose: string`、`expireAt: string(date-time)`。

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的 DID、资源、时间和状态冲突错误。

**幂等规则**：适用；相同 `Idempotency-Key` 与相同请求体返回同一 `authId`，冲突按[公共响应与错误码](./response-and-errors.md)处理。

### `POST /api/v1/auth/requests/{authId}/approve`

请求：`approverDid`，可选 `decision` 和 `reason`。成功返回授权记录及 `status: approved`。

**请求说明**：`authId` 来自路径；JSON 请求体使用 `ApproveAuthRequest`，不得在请求体重复 `authId`。

**字段类型与必填性**：路径参数 `authId: string` 必填；请求体 `approverDid: string` 必填，`decision: string`、`reason: string` 可选。

**成功说明**：`data` 为 object，包含 `authId: string`、`status: string`、`approverDid: string`、`decision: string`、`reason: string|null`、`approvedAt: string(date-time)`。

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的授权不存在、DID、访问拒绝和状态冲突错误。

**幂等规则**：适用；相同 `Idempotency-Key` 与相同审批请求复用首次结果，冲突按[公共响应与错误码](./response-and-errors.md)处理。

### `GET /api/v1/auth/requests/{authId}`

查询授权申请完整记录和当前状态。

**请求说明**：`authId` 来自路径；无请求体。

**字段类型与必填性**：路径参数 `authId: string` 必填。

**成功说明**：`data` 为 object，包含授权申请字段、`status: string`、`decision: string|null`、`reason: string|null` 和创建/审批时间。

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的资源不存在、访问拒绝和服务错误。

**幂等规则**：不适用；该接口为只读查询。

## 8. federated-learning

### `POST /api/v1/fl/tasks`

请求字段：`taskName`、`modelType`、`algorithm`、`rounds`、`participants[]`、`assetIds[]`、`target`。成功返回 `trainingTaskId`、`status: created`、轮次和参与方。

**请求说明**：JSON 请求体使用 `CreateTrainingTaskRequest`；所有字段来自请求体。

**字段类型与必填性**：`taskName: string`、`modelType: string`、`algorithm: string`、`rounds: integer`、`participants: array<string>`、`assetIds: array<string>`、`target: string` 均必填。

**成功说明**：`data` 为 object，包含 `trainingTaskId: string`、`status: string`、`rounds: integer`、`participants: array<string>`、`assetIds: array<string>`。

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的请求校验、训练配置、参与方和状态错误。

**幂等规则**：适用；相同 `Idempotency-Key` 与相同请求体返回同一 `trainingTaskId`，冲突按[公共响应与错误码](./response-and-errors.md)处理。

### `POST /api/v1/fl/tasks/{taskId}/start`

启动任务并固定生成第 1 轮可交给隐私计算的更新摘要。

**请求说明**：`taskId` 仅来自路径；无请求体。

**字段类型与必填性**：路径参数 `taskId: string` 必填；无请求体字段。

**成功说明**：`data` 为下列 JSON，返回第 1 轮 `currentRound` 和完整 `updates`。

成功 `data`：

```json
{
  "trainingTaskId": "fl_task_001",
  "status": "running",
  "currentRound": 1,
  "updates": [
    {
      "participantDid": "did:vpp:load-aggregator:001",
      "sampleCount": 500,
      "modelUpdateUri": "storage://updates/fl_task_001/round_1/load_client.json",
      "updateHash": "sha256:update001"
    }
  ]
}
```

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的训练任务不存在、参与方未就绪、训练配置和状态冲突错误。

**幂等规则**：适用；相同 `Idempotency-Key` 与相同任务复用首次启动结果，冲突按[公共响应与错误码](./response-and-errors.md)处理。

### `POST /api/v1/fl/tasks/{taskId}/rounds/{roundId}/updates`

**请求说明**：`taskId`、`roundId` 仅来自路径；JSON 请求体使用 `SubmitModelUpdateRequest`，禁止重复这两个路径 ID。

**字段类型与必填性**：路径参数 `taskId: string`、`roundId: integer` 必填；请求体 `participantDid: string`、`sampleCount: integer`、`modelUpdateUri: string(uri)`、`updateHash: string` 均必填。

请求：

```json
{
  "participantDid": "did:vpp:load-aggregator:001",
  "sampleCount": 500,
  "modelUpdateUri": "storage://updates/fl_task_001/round_1/load_client.json",
  "updateHash": "sha256:update001"
}
```

**成功说明**：`data` 为 object，包含 `participantDid: string`、`sampleCount: integer`、`status: string`、`acceptedAt: string(date-time)`；任务与轮次由路径确定。

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的任务不存在、无效哈希、更新不足和状态冲突错误。

**幂等规则**：适用；相同 `Idempotency-Key` 与相同路径/请求体复用首次提交结果，冲突按[公共响应与错误码](./response-and-errors.md)处理。

### `POST /api/v1/fl/tasks/{taskId}/rounds/{roundId}/aggregate`

接收网关从 `privacy-compute` 取得的安全聚合结果并执行 FedAvg。

**请求说明**：`taskId`、`roundId` 仅来自路径；JSON 请求体使用 `AggregateRoundRequest`，禁止重复这两个路径 ID。

**字段类型与必填性**：路径参数 `taskId: string`、`roundId: integer` 必填；请求体 `aggregateId: string`、`aggregateResultUri: string(uri)`、`aggregateHash: string` 均必填。

请求：

```json
{
  "aggregateId": "aggregate_001",
  "aggregateResultUri": "storage://aggregates/fl_task_001/round_3/result.json",
  "aggregateHash": "sha256:agg001"
}
```

**成功说明**：成功 `data` 在非最终轮返回 `status: running`、整数 `nextRound` 和下一轮完整 `updates`；最终轮返回 `status: completed`、`nextRound: null`、空 `updates` 及最终模型信息。

非最终轮成功 `data`：

```json
{
  "trainingTaskId": "fl_task_001",
  "roundId": 1,
  "status": "running",
  "nextRound": 2,
  "updates": [
    {
      "participantDid": "did:vpp:load-aggregator:001",
      "sampleCount": 500,
      "modelUpdateUri": "storage://updates/fl_task_001/round_2/load_client.json",
      "updateHash": "sha256:update002"
    }
  ]
}
```

最终轮成功 `data`：

```json
{
  "trainingTaskId": "fl_task_001",
  "roundId": 3,
  "status": "completed",
  "nextRound": null,
  "updates": [],
  "globalModelVersion": "global_model_v1",
  "modelHash": "sha256:model123",
  "participantCount": 3,
  "metrics": { "mae": 2.31, "rmse": 3.72, "mape": 0.081 }
}
```

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的任务不存在、无效哈希、更新不足和状态冲突错误。

**幂等规则**：适用；相同 `Idempotency-Key` 与相同路径/聚合结果复用该轮首次结果，冲突按[公共响应与错误码](./response-and-errors.md)处理。

### `GET /api/v1/fl/tasks/{taskId}`

返回任务状态、当前轮次、参与方、模型版本和最近错误。

**请求说明**：`taskId` 来自路径；无请求体。

**字段类型与必填性**：路径参数 `taskId: string` 必填。

**成功说明**：`data` 为 object，包含 `trainingTaskId: string`、`status: string`、`currentRound: integer|null`、`participants: array<string>`、`globalModelVersion: string|null`、`lastError: object|null`。

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的训练任务不存在和服务错误。

**幂等规则**：不适用；该接口为只读查询。

### `GET /api/v1/fl/tasks/{taskId}/metrics`

返回按轮次记录的 `mae`、`rmse`、`mape` 和样本数。

**请求说明**：`taskId` 来自路径；无请求体。

**字段类型与必填性**：路径参数 `taskId: string` 必填。

**成功说明**：`data` 为 object，包含 `trainingTaskId: string` 与 `rounds: array<object>`；每项含 `roundId: integer`、`mae: number`、`rmse: number`、`mape: number`、`sampleCount: integer`。

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的训练任务不存在和服务错误。

**幂等规则**：不适用；该接口为只读查询。

### `GET /api/v1/fl/models/{modelVersion}`

返回模型元信息、模型哈希、训练任务、轮次、指标和模型 URI；不得返回未授权的原始参数。

**请求说明**：`modelVersion` 来自路径；无请求体。

**字段类型与必填性**：路径参数 `modelVersion: string` 必填。

**成功说明**：`data` 为 object，包含 `modelVersion: string`、`modelHash: string`、`trainingTaskId: string`、`roundId: integer`、`metrics: object`、`modelUri: string(uri)`。

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的模型版本不存在、访问拒绝和服务错误。

**幂等规则**：不适用；该接口为只读查询。

## 9. privacy-compute

### `POST /api/v1/privacy/model-updates/encrypt`

请求：`trainingTaskId`、`roundId`、`updates[]`、`algorithm`。成功返回加密更新摘要、结果 URI 和 `privacyMode: homomorphic_demo`。

**请求说明**：JSON 请求体使用 `ProtectModelUpdatesRequest`；所有字段来自请求体。

**字段类型与必填性**：`trainingTaskId: string`、`roundId: integer`、`updates: array<object>`、`algorithm: string` 均必填；每项更新包含必填的 `participantDid: string`、`sampleCount: integer`、`modelUpdateUri: string(uri)`、`updateHash: string`。

**成功说明**：`data` 为 object，包含 `trainingTaskId: string`、`roundId: integer`、`protectedUpdates: array<object>`、`resultUri: string(uri)`、`privacyMode: string`（固定 `homomorphic_demo`）。

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的请求校验、无效哈希、更新不足和隐私模式错误。

**幂等规则**：适用；相同 `Idempotency-Key` 与相同请求体复用首次保护结果，冲突按[公共响应与错误码](./response-and-errors.md)处理。

### `POST /api/v1/privacy/model-updates/mask`

请求结构与 encrypt 相同；成功返回安全掩码更新摘要、结果 URI 和 `privacyMode: secure_masking`。

**请求说明**：JSON 请求体使用 `ProtectModelUpdatesRequest`；所有字段来自请求体。

**字段类型与必填性**：`trainingTaskId: string`、`roundId: integer`、`updates: array<object>`、`algorithm: string` 均必填；每项更新包含必填的 `participantDid: string`、`sampleCount: integer`、`modelUpdateUri: string(uri)`、`updateHash: string`。

**成功说明**：`data` 为 object，包含 `trainingTaskId: string`、`roundId: integer`、`protectedUpdates: array<object>`、`resultUri: string(uri)`、`privacyMode: string`（固定 `secure_masking`）。

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的请求校验、无效哈希、更新不足和隐私模式错误。

**幂等规则**：适用；相同 `Idempotency-Key` 与相同请求体复用首次掩码结果，冲突按[公共响应与错误码](./response-and-errors.md)处理。

### `POST /api/v1/privacy/secure-aggregate`

请求字段：`trainingTaskId`、`roundId`、`updates[]`、`privacyMode`。

**请求说明**：JSON 请求体使用 `SecureAggregateRequest`；所有字段来自请求体。

**字段类型与必填性**：`trainingTaskId: string`、`roundId: integer`、`updates: array<object>`、`privacyMode: string` 均必填；每项更新包含必填的 `participantDid: string`、`sampleCount: integer`、`modelUpdateUri: string(uri)`、`updateHash: string`。

请求：

```json
{
  "trainingTaskId": "fl_task_001",
  "roundId": 1,
  "updates": [
    {
      "participantDid": "did:vpp:load-aggregator:001",
      "sampleCount": 500,
      "modelUpdateUri": "storage://updates/fl_task_001/round_1/load_client.json",
      "updateHash": "sha256:update001"
    }
  ],
  "privacyMode": "secure_masking"
}
```

**成功说明**：`data` 为下列 JSON，包含聚合标识、结果 URI、摘要、参与方数量和隐私模式。

成功 `data`：

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

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的请求校验、无效哈希、更新不足和不支持的隐私模式错误。

**幂等规则**：适用；相同 `Idempotency-Key` 与相同请求体返回同一 `aggregateId`，冲突按[公共响应与错误码](./response-and-errors.md)处理。

### `GET /api/v1/privacy/aggregates/{aggregateId}`

返回聚合元信息、参与方数量、隐私模式、结果 URI 和摘要哈希；不返回单个参与方明文更新。

**请求说明**：`aggregateId` 来自路径；无请求体。

**字段类型与必填性**：路径参数 `aggregateId: string` 必填。

**成功说明**：`data` 为 object，包含 `aggregateId: string`、`trainingTaskId: string`、`roundId: integer`、`aggregateResultUri: string(uri)`、`aggregateHash: string`、`participantCount: integer`、`privacyMode: string`。

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的资源不存在、访问拒绝和服务错误。

**幂等规则**：不适用；该接口为只读查询。

## 10. ledger-service

### `POST /api/v1/ledger/events`

请求字段：`eventType`、`businessId`、`subjectDid`、`payloadHash`、`payloadUri`、`description`、`metadata`。成功 `data` 返回 `ledgerTxId`、`eventId`、`blockHeight`、`currentHash`。

**请求说明**：JSON 请求体使用 `CreateLedgerEventRequest`；所有字段来自请求体。

**字段类型与必填性**：`eventType: string`、`businessId: string`、`subjectDid: string`、`payloadHash: string` 必填；`payloadUri: string(uri)`、`description: string`、`metadata: object` 可选。

**成功说明**：`data` 为 object，包含 `ledgerTxId: string`、`eventId: string`、`blockHeight: integer`、`currentHash: string`、`previousHash: string|null`、`createdAt: string(date-time)`。

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的请求校验、无效 DID/哈希、重复事件和存储错误。

**幂等规则**：适用；相同 `Idempotency-Key` 与相同事件复用首次存证结果，冲突按[公共响应与错误码](./response-and-errors.md)处理。

### `GET /api/v1/ledger/events/{eventId}`

返回单个事件、交易 ID、区块高度、当前哈希、前序哈希和元数据。

**请求说明**：`eventId` 来自路径；无请求体。

**字段类型与必填性**：路径参数 `eventId: string` 必填。

**成功说明**：`data` 为 object，包含事件请求字段及 `eventId: string`、`ledgerTxId: string`、`blockHeight: integer`、`currentHash: string`、`previousHash: string|null`、`createdAt: string(date-time)`。

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的资源不存在、访问拒绝和服务错误。

**幂等规则**：不适用；该接口为只读查询。

### `GET /api/v1/ledger/traces/{businessId}`

返回按时间排序的完整证据链：事件 ID、事件类型、时间、摘要哈希、交易 ID、区块高度和链路状态。

**请求说明**：`businessId` 来自路径；无请求体。

**字段类型与必填性**：路径参数 `businessId: string` 必填。

**成功说明**：`data` 为 object，包含 `businessId: string`、`chainValid: boolean`、`events: array<object>`；事件按时间排序并含 ID、类型、时间、摘要、交易 ID、区块高度与前序/当前哈希。

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的业务不存在、访问拒绝和服务错误。

**幂等规则**：不适用；该接口为只读查询。

## 11. ai-agent

### `POST /api/v1/agent/predict`

请求：`modelVersion`、`scenario`、`input`。成功返回 `predictionId`、`modelVersion`、`predictedCapacityKw`、`confidence`。

**请求说明**：JSON 请求体使用 `PredictRequest`；所有字段来自请求体。

**字段类型与必填性**：`modelVersion: string`、`scenario: string`、`input: object` 均必填；`input` 中的场景特征值为 string、number 或 boolean。

请求：

```json
{
  "modelVersion": "global_model_v1",
  "scenario": "day_ahead_trading",
  "input": { "date": "2026-07-11", "temperature": 34, "marketPrice": 0.68 }
}
```

**成功说明**：`data` 为下列可解析 JSON。

成功 `data`：

```json
{
  "predictionId": "prediction_001",
  "modelVersion": "global_model_v1",
  "predictedCapacityKw": 120000,
  "confidence": 0.91
}
```

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的模型版本不存在、请求校验、访问拒绝和服务错误。

**幂等规则**：适用；相同 `Idempotency-Key` 与相同请求体复用首次预测结果，冲突按[公共响应与错误码](./response-and-errors.md)处理。

### `POST /api/v1/agent/trading-strategy`

请求：`predictionId`、`scenario`、`marketPrice`、`riskPreference`。成功返回 `strategyId`、申报容量、价格建议、安全裕度和解释。

**请求说明**：JSON 请求体使用 `TradingStrategyRequest`；所有字段来自请求体。

**字段类型与必填性**：`predictionId: string`、`scenario: string`、`marketPrice: number`、`riskPreference: string` 均必填。

请求：

```json
{
  "predictionId": "prediction_001",
  "scenario": "day_ahead_trading",
  "marketPrice": 0.68,
  "riskPreference": "balanced"
}
```

**成功说明**：`data` 为下列可解析 JSON。

成功 `data`：

```json
{
  "strategyId": "strategy_001",
  "bidCapacityKw": 108000,
  "suggestedPrice": 0.7,
  "safetyMargin": 0.1,
  "explanation": "按预测容量保留 10% 安全裕度"
}
```

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的资源不存在、请求校验、状态冲突和服务错误。

**幂等规则**：适用；相同 `Idempotency-Key` 与相同请求体复用首次策略结果，冲突按[公共响应与错误码](./response-and-errors.md)处理。

### `POST /api/v1/agent/audit-question`

请求字段：`businessId`、`modelVersion`、`evidenceEventIds[]`、`question`。

**请求说明**：JSON 请求体使用 `AuditQuestionRequest`；账本证据 ID 由网关查询后放入请求体。

**字段类型与必填性**：`businessId: string`、`modelVersion: string`、`evidenceEventIds: array<string>`、`question: string` 均必填。

请求：

```json
{
  "businessId": "demo_001",
  "modelVersion": "global_model_v1",
  "evidenceEventIds": ["evt_data_001", "evt_model_001"],
  "question": "本次预测使用了哪个模型版本？"
}
```

证据 ID 由网关查询账本后提供。

**成功说明**：`data` 为下列可解析 JSON，实际引用的证据必须来自请求。

成功 `data`：

```json
{
  "answer": "本次预测使用 global_model_v1。",
  "evidenceEventIds": ["evt_model_001"],
  "modelVersion": "global_model_v1",
  "confidence": 0.95
}
```

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的业务/模型不存在、访问拒绝、请求校验和服务错误。

**幂等规则**：适用；相同 `Idempotency-Key` 与相同请求体复用首次回答，冲突按[公共响应与错误码](./response-and-errors.md)处理。

### `POST /api/v1/agent/audit-report`

请求字段：`businessId`、`modelVersion`、`evidenceEventIds[]`、`reportType`。

**请求说明**：JSON 请求体使用 `AuditReportRequest`；账本证据 ID 由网关查询后放入请求体。

**字段类型与必填性**：`businessId: string`、`modelVersion: string`、`evidenceEventIds: array<string>`、`reportType: string` 均必填。

请求：

```json
{
  "businessId": "demo_001",
  "modelVersion": "global_model_v1",
  "evidenceEventIds": ["evt_data_001", "evt_auth_001", "evt_model_001"],
  "reportType": "transaction_audit"
}
```

证据 ID 由网关查询账本后提供。

**成功说明**：`data` 为下列可解析 JSON。

成功 `data`：

```json
{
  "auditReportId": "report_001",
  "title": "虚拟电厂日前交易审计报告",
  "summary": "本次交易使用 global_model_v1 完成可调节容量预测，参与主体 3 个，原始数据未出域，关键操作均已存证。",
  "riskLevel": "low",
  "recommendations": ["建议申报可调节容量 120MW", "建议保留 10% 安全裕度"]
}
```

**可能错误**：仅引用[公共响应与错误码](./response-and-errors.md)中的业务/模型不存在、访问拒绝、请求校验和服务错误。

**幂等规则**：适用；相同 `Idempotency-Key` 与相同请求体复用首次报告，冲突按[公共响应与错误码](./response-and-errors.md)处理。

## 12. 所有服务健康检查

### `GET /health`

每个后端服务均提供该公共健康接口。

**请求说明**：无路径参数或查询参数；无请求体。

**字段类型与必填性**：无请求字段。

**成功说明**：`data` 为 object，包含必填的 `service: string` 与 `status: string`；完整公共包络见[公共响应与错误码](./response-and-errors.md)。

**可能错误**：未就绪时仅引用[公共响应与错误码](./response-and-errors.md)中的服务或依赖不可用错误。

**幂等规则**：不适用；该接口为只读查询。

## 13. 接口变更规则

1. 修改路径、方法、字段、枚举、状态或错误码前，先修改本文档。
2. 同步修改 `docs/design/module-contracts.md` 对应模块章节。
3. 如果修改影响跨模块时序，再修改 `docs/design/main-flow.md`。
4. 通过接口覆盖矩阵检查后，才能进入代码实现。
5. 任何新增接口必须补充成功示例、至少一个失败示例和幂等说明。
