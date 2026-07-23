# data-ingestion

数据接入模块，负责接收源端密文电表数据，完成签名校验、哈希校验和数据资产登记。第一周先以 Mock 实现跑通链路，后续替换为真实验签验哈希。

## 职责边界

> **你只负责本模块（`services/data-ingestion`）下的代码。** 你可以通过 HTTP 调用其他模块的接口来完成联调和验证，但**不得修改其他模块的源码、配置、文档或测试**。

本 README 明确划分你的工作范围：以下所有"负责"、"接口"、"实现"均指 `data-ingestion` 内部；引用其他模块时仅描述调用关系，不侵入其代码。

## 模块职责

### 负责

1. 接收密文电表数据（`POST /api/v1/data/ingest`）
2. 校验数据签名和哈希
3. 保存数据元信息并登记数据资产（`POST /api/v1/data/assets`）
4. 查询资产元信息（`GET /api/v1/data/assets/{assetId}`）
5. 标记数据敏感级别和用途

### 不负责

- 不负责生成电表数据（属于 `meter-simulator`）
- 不负责授权审批（属于 `identity-did`）
- 不负责模型训练（属于 `federated-learning`）
- 不负责链上存证（由 `api-gateway` 统一调用 `ledger-service`）
- 不负责解密原始电表数据

## 架构位置

### 被谁调用

| 调用方 | 调用方式 | 说明 |
|---|---|---|
| `api-gateway` | HTTP POST / GET | 网关在源端采集后将密文批次发来验签验哈希，登记资产后返回 `assetId` |
| 其他服务 | 无 | 本模块不对外开放其他调用入口 |

### 是否调用他人

**不调用任何外部服务。** 本模块是纯处理节点，接收输入后直接返回结果。

### 在主流程中的位置

```
meter-simulator 生成密文批次
  → api-gateway 将密文批次发给 data-ingestion
  → data-ingestion 验签、验哈希、登记数据资产 → 返回 assetId
  → api-gateway 将 assetId 传给 identity-did 发起授权
```

详细时序见 `docs/design/main-flow.md` 第 4.1 节。

## 技术栈

| 项目 | 版本 / 选型 |
|---|---|
| Python | `>=3.11,<3.12` |
| Web 框架 | FastAPI `>=0.115,<1` |
| 数据校验 | Pydantic v2 `>=2,<3` |
| 服务器 | Uvicorn `>=0.34,<1` |
| 测试 | pytest `>=8,<9` / httpx `>=0.28,<1` |
| 公共包 | `vpp-common==0.1.0` |

## 安装

```bash
# 仓库根目录执行
python -m pip install -e packages/common -e "services/data-ingestion[test]"
```

## 启动

```bash
# 开发模式（热重载）
uvicorn data_ingestion.main:app --host 0.0.0.0 --port 8002 --reload

# 生产模式
uvicorn data_ingestion.main:app --host 0.0.0.0 --port 8002
```

## 测试

```bash
python -m pytest services/data-ingestion/tests -v
```

## Docker

```bash
# 以仓库根目录为 context 构建
docker build -f services/data-ingestion/Dockerfile -t vpp/data-ingestion:week1 .

# 运行
docker run --rm -p 8002:8000 vpp/data-ingestion:week1
```

## 接口列表（共 4 个）

| 方法 | 路径 | 用途 | 幂等 |
|---|---|---|---|
| GET | `/health` | 健康检查 | 不适用 |
| POST | `/api/v1/data/ingest` | **主流程数据接入**：接收密文批次，验签验哈希，登记资产 | 适用 |
| POST | `/api/v1/data/assets` | 独立登记资产元信息 | 适用 |
| GET | `/api/v1/data/assets/{assetId}` | 查询资产元信息 | 不适用 |

## 接口规范

### 统一约定

- API 前缀：`/api/v1`
- 请求格式：`application/json`
- 统一响应包络：`{ code, message, data, traceId, timestamp }`
- 错误码：全部引自 `docs/api/response-and-errors.md`
- 服务间调用传递 `X-Trace-Id`；网关传入时原样使用，缺失时本模块生成 `trace_` 前缀 ID
- 写操作支持 `Idempotency-Key`：相同 Key + 相同请求体复用首次结果，Key 相同但请求体不同返回 HTTP `409` 业务码 `40901`

### `GET /health`

健康检查。

```bash
curl -s http://localhost:8002/health
```

成功响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "service": "data-ingestion",
    "status": "healthy"
  },
  "traceId": "trace_xxx",
  "timestamp": "2026-07-22T02:00:00Z"
}
```

### `POST /api/v1/data/ingest`

**主流程中调用的核心接口。** 接收源端密文批次，验证每条读数的签名和哈希，登记数据资产并返回 `assetId`。

#### 请求字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `readingBatchId` | string | 是 | 源端生成的批次 ID |
| `ownerDid` | string | 是 | 数据所有者 DID |
| `readings` | array\<object\> | 是 | 密文读数列表 |

`readings[].`：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `readingId` | string | 是 | 单条读数 ID |
| `meterId` | string | 是 | 电表 ID |
| `ciphertext` | string | 是 | AES 加密后的密文（Base64） |
| `signature` | string | 是 | 设备私钥签名（Base64） |
| `hash` | string | 是 | SHA-256 摘要哈希 |
| `timestamp` | string | 是 | 读数时间（ISO 8601） |

#### 请求示例

```bash
curl -s -X POST http://localhost:8002/api/v1/data/ingest \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: test-ingest-001" \
  -H "X-Trace-Id: trace_demo_001" \
  -d '{
    "readingBatchId": "batch_001",
    "ownerDid": "did:vpp:load-aggregator:001",
    "readings": [
      {
        "readingId": "reading_001",
        "meterId": "meter_001",
        "ciphertext": "dGVzdC1jaXBoZXJ0ZXh0LTAwMQ==",
        "signature": "dGVzdC1zaWduYXR1cmUtMDAx",
        "hash": "sha256:abc123def456",
        "timestamp": "2026-07-22T10:00:00+08:00"
      },
      {
        "readingId": "reading_002",
        "meterId": "meter_002",
        "ciphertext": "dGVzdC1jaXBoZXJ0ZXh0LTAwMg==",
        "signature": "dGVzdC1zaWduYXR1cmUtMDAy",
        "hash": "sha256:ghi789jkl012",
        "timestamp": "2026-07-22T10:05:00+08:00"
      }
    ]
  }'
```

#### 成功响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "assetId": "asset_001",
    "readingBatchId": "batch_001",
    "ownerDid": "did:vpp:load-aggregator:001",
    "assetType": "meter_readings",
    "sensitivityLevel": "private",
    "status": "registered"
  },
  "traceId": "trace_demo_001",
  "timestamp": "2026-07-22T02:00:00Z"
}
```

#### 可能错误

| 错误码 | message | HTTP | 场景 |
|---|---|---|---|
| `40001` | `invalid request` | 400 | 缺少必填字段或字段格式错误 |
| `40005` | `payload too large` | 413 | 请求体超过大小限制 |
| `40102` | `invalid did` | 401 | `ownerDid` 格式非法（不以 `did:vpp:` 开头） |
| `40103` | `invalid signature` | 401 | 签名校验失败 |
| `40104` | `invalid hash` | 401 | `hash` 不以 `sha256:` 开头或校验不匹配 |
| `40901` | `idempotency conflict` | 409 | 相同幂等键对应不同请求体 |
| `42202` | `insufficient updates` | 422 | `readings` 为空 |

### `POST /api/v1/data/assets`

独立登记资产元信息，不参与第一周一键演示主流程。不要求提交读数内容。

#### 请求示例

```bash
curl -s -X POST http://localhost:8002/api/v1/data/assets \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: test-asset-001" \
  -d '{
    "readingBatchId": "batch_001",
    "ownerDid": "did:vpp:load-aggregator:001",
    "assetType": "meter_readings",
    "sensitivityLevel": "private",
    "purpose": "federated_training"
  }'
```

#### 成功响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "assetId": "asset_xxx",
    "readingBatchId": "batch_001",
    "ownerDid": "did:vpp:load-aggregator:001",
    "assetType": "meter_readings",
    "sensitivityLevel": "private",
    "purpose": "federated_training",
    "status": "registered",
    "createdAt": "2026-07-22T02:00:00Z"
  },
  "traceId": "trace_xxx",
  "timestamp": "2026-07-22T02:00:00Z"
}
```

#### 可能错误

| 错误码 | message | HTTP | 场景 |
|---|---|---|---|
| `40001` | `invalid request` | 400 | 缺少必填字段 |
| `40102` | `invalid did` | 401 | `ownerDid` 格式非法 |
| `40901` | `idempotency conflict` | 409 | 相同幂等键对应不同请求体 |

### `GET /api/v1/data/assets/{assetId}`

查询资产元信息（只读），不返回原始明文数据。

```bash
curl -s http://localhost:8002/api/v1/data/assets/asset_001
```

成功 `data`：

```json
{
  "assetId": "asset_001",
  "ownerDid": "did:vpp:load-aggregator:001",
  "assetType": "meter_readings",
  "sensitivityLevel": "private",
  "status": "registered",
  "createdAt": "2026-07-22T02:00:00Z"
}
```

## Mock 实现要点（第一周）

1. **ID 生成** — `assetId` 使用 `vpp_common.new_id("asset_")`
2. **验签** — Mock 阶段 `signature` 字段非空且为 Base64 格式即视为签名有效
3. **验哈希** — 校验 `hash` 以 `sha256:` 开头即视为哈希有效
4. **`assetType`** — 固定 `meter_readings`
5. **`sensitivityLevel`** — 固定 `private`
6. **`status`** — 固定 `registered`
7. **`createdAt`** — 使用 `vpp_common` 的 UTC 时间工具生成
8. **幂等仓库** — 内存字典 `{ idempotency_key: (request_hash, response_data) }`
9. **DID 校验** — Mock 阶段校验 `ownerDid` 以 `did:vpp:` 开头
10. **错误抛出** — 业务失败统一 `raise ServiceError(ErrorCode.xxx)`，不走 `return failure()`

## 目录结构（预期）

```
services/data-ingestion/
  pyproject.toml
  README.md                  ← 本文件
  Dockerfile
  src/
    data_ingestion/
      __init__.py
      main.py                # FastAPI 应用入口 / 路由注册
      api.py                 # 路由定义（4 个接口）
      schemas.py             # 请求/响应 Pydantic 模型
      repository.py          # 幂等仓库 + 资产存储
      service.py             # 业务逻辑（验签、验哈希、登记资产）
  tests/
    __init__.py
    test_health.py           # /health 测试
    test_ingest.py           # ingest 正常/失败/幂等测试
    test_assets.py           # asset 登记/查询/失败测试
```

## 相关文档

| 文档 | 内容 |
|---|---|
| `docs/design/module-contracts.md` | 模块 2 — 数据接入模块详细职责与接口清单 |
| `docs/design/main-flow.md` | 主流程编排与 data-ingestion 在链路中的位置 |
| `docs/api/openapi.md` | 第 6 节 — 接口 Schema、字段、示例 |
| `docs/api/response-and-errors.md` | 统一响应包络、错误码、追踪、幂等规则 |
| `packages/common/README.md` | 公共包安装与使用 |
