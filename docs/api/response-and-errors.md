# 公共响应格式与错误码

> **文档职责**：本文档是 vpp-trusted-data-space 全部 HTTP 服务的公共协议单一来源，定义统一响应包络、错误码、HTTP 状态码、追踪字段和幂等约定。`docs/api/openapi.md` 负责引用这些规则并描述具体接口；`docs/design/module-contracts.md` 负责描述模块职责和接口边界，不能另行定义冲突的响应格式或错误码。

## 1. 适用范围

适用于 `api-gateway`、`meter-simulator`、`data-ingestion`、`identity-did`、`federated-learning`、`privacy-compute`、`ledger-service`、`ai-agent` 的所有业务接口和 `GET /health`。

接口路径、请求字段和模块边界以 `docs/api/openapi.md` 与 `docs/design/module-contracts.md` 为准；本文件只定义跨模块通用规则。

## 2. 统一成功响应

所有 HTTP 响应均使用以下包络：

```json
{
  "code": 0,
  "message": "ok",
  "data": {},
  "traceId": "trace_20260710_000001"
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `code` | integer | 是 | 业务码；`0` 表示成功，非 `0` 表示失败。 |
| `message` | string | 是 | 面向调用方的简短稳定说明。 |
| `data` | object/array/null | 是 | 业务结果；无内容时固定为 `null`。 |
| `traceId` | string | 是 | 请求链路追踪 ID；网关生成并向下游传递。 |
| `requestId` | string | 否 | 服务内部请求 ID。 |
| `timestamp` | string | 否 | ISO 8601 响应时间。 |

约定：

1. 业务成功只返回 `code: 0`，不得用 HTTP 200 搭配非零 `code` 表示失败。
2. `data` 结构由具体接口定义，不得把业务字段平铺到响应根部。
3. `message` 不得包含密钥、明文电表数据、模型参数或内部堆栈。

## 3. 统一错误响应

```json
{
  "code": 40001,
  "message": "invalid request",
  "data": null,
  "traceId": "trace_20260710_000001",
  "details": [
    { "field": "participants", "reason": "must not be empty" }
  ]
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `code` | integer | 是 | 稳定业务错误码；客户端按错误码处理。 |
| `message` | string | 是 | 稳定英文短语。 |
| `data` | null | 是 | 错误时固定为 `null`。 |
| `traceId` | string | 是 | 跨服务排查标识。 |
| `details` | array | 否 | 字段级校验或下游错误详情，不得泄露敏感数据。 |

## 4. HTTP 状态码映射

| HTTP | 使用场景 | 典型业务码 |
|---:|---|---|
| `200` | 查询、生成、审批、聚合成功 | `0` |
| `201` | 创建资源成功；MVP 可统一使用 `200` | `0` |
| `400` | 请求体、参数或字段格式错误 | `40001`-`40005` |
| `401` | 身份、签名或 DID 校验失败 | `40101`-`40104` |
| `403` | 无资源权限或授权不可用 | `40301`-`40303` |
| `404` | 资源不存在 | `40401`-`40404` |
| `409` | 幂等冲突或状态冲突 | `40901`-`40903` |
| `422` | 业务前置条件不满足 | `42201`-`42204` |
| `429` | 限流或并发超限 | `42901` |
| `500` | 当前服务内部错误 | `50001`-`50003` |
| `502` | 网关收到下游失败 | `50201`-`50203` |
| `503` | 服务或依赖未就绪 | `50301`-`50303` |
| `504` | 下游调用超时 | `50401` |

## 5. 错误码目录

### 5.1 通用请求错误 `400xx`

| 错误码 | message | 说明 |
|---:|---|---|
| `40001` | `invalid request` | 请求参数不符合 Schema。 |
| `40002` | `missing required field` | 缺少必填字段。 |
| `40003` | `invalid timestamp` | 时间不是 ISO 8601 或超出业务范围。 |
| `40004` | `invalid enum value` | 枚举值非法。 |
| `40005` | `payload too large` | 请求内容超过限制。 |

### 5.2 身份与签名错误 `401xx`

| 错误码 | message | 说明 |
|---:|---|---|
| `40101` | `missing identity` | 未提供调用方身份。 |
| `40102` | `invalid did` | DID 不存在、格式非法或状态不可用。 |
| `40103` | `invalid signature` | 签名校验失败。 |
| `40104` | `invalid hash` | 摘要与重新计算结果不一致。 |

### 5.3 授权错误 `403xx`

| 错误码 | message | 说明 |
|---:|---|---|
| `40301` | `access denied` | 调用方无权访问资源。 |
| `40302` | `authorization required` | 数据资产或模型尚未授权。 |
| `40303` | `authorization expired` | 授权已过期或撤销。 |

### 5.4 资源与状态错误 `404xx`/`409xx`

| 错误码 | message | 说明 |
|---:|---|---|
| `40401` | `resource not found` | 通用资源不存在。 |
| `40402` | `business not found` | `businessId` 不存在。 |
| `40403` | `training task not found` | 训练任务不存在。 |
| `40404` | `model version not found` | 模型版本不存在。 |
| `40901` | `idempotency conflict` | 同一幂等键对应不同请求体。 |
| `40902` | `invalid resource state` | 当前资源状态不允许该操作。 |
| `40903` | `duplicate event` | 相同事件已成功存证。 |

### 5.5 业务前置条件 `422xx`

| 错误码 | message | 说明 |
|---:|---|---|
| `42201` | `participants not ready` | 参与方、资产或授权未准备完成。 |
| `42202` | `insufficient updates` | 当前轮次模型更新不足。 |
| `42203` | `unsupported privacy mode` | 隐私计算模式不支持。 |
| `42204` | `invalid training configuration` | 训练配置不合法。 |

### 5.6 限流、服务与依赖错误

| 错误码 | message | 说明 |
|---:|---|---|
| `42901` | `rate limit exceeded` | 请求频率或并发超限。 |
| `50001` | `internal error` | 未分类内部错误。 |
| `50002` | `storage error` | 存储读写失败。 |
| `50003` | `serialization error` | 序列化失败。 |
| `50201` | `downstream rejected` | 下游返回可识别失败。 |
| `50202` | `downstream invalid response` | 下游响应不符合公共协议。 |
| `50203` | `downstream unavailable` | 网关无法连接下游。 |
| `50301` | `service unavailable` | 当前服务未就绪。 |
| `50302` | `dependency unavailable` | 依赖未就绪。 |
| `50303` | `maintenance mode` | 服务维护中。 |
| `50401` | `downstream timeout` | 下游响应超时。 |

## 6. 请求头、幂等和追踪

| Header | 约定 |
|---|---|
| `Content-Type` | JSON 请求固定为 `application/json`。 |
| `X-Trace-Id` | 网关接收或生成追踪 ID；下游沿用。 |
| `Idempotency-Key` | 创建批次、资产、授权、训练任务、聚合和存证等写操作建议传入。 |
| `X-Caller-Did` | 服务间调用时传入调用方 DID；与请求体 DID 不一致时返回 `40102`。 |

幂等规则：相同 Key 重试返回首次结果；相同 Key 但请求体不同返回 HTTP `409`、业务码 `40901`；超时后不得生成新 Key 造成重复业务。

## 7. 健康检查

```http
GET /health
```

健康时返回 HTTP `200`：

```json
{
  "code": 0,
  "message": "ok",
  "data": { "service": "service-name", "status": "healthy" },
  "traceId": "trace_20260710_000001"
}
```

服务未就绪时返回 HTTP `503`、业务码 `50301` 或 `50302`，仍必须使用统一错误包络。
