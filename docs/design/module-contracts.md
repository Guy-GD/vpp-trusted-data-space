# 模块化架构与接口契约说明

本文档用于指导团队基于“虚拟电厂跨主体数据协同交易与审计”场景开展模块化开发。所有成员使用 Agent 写代码时，必须先阅读本文档，并严格按照模块职责、输入输出和接口契约实现。

> **相关文档职责**：本文档负责模块边界、职责、输入输出和模块级接口清单；`docs/design/main-flow.md` 负责跨模块主流程、状态、存证节点和失败处理；`docs/api/openapi.md` 负责所有 HTTP 接口的完整路径、字段和示例；`docs/api/response-and-errors.md` 负责统一响应包络、错误码、HTTP 状态码、追踪和幂等规则。三份文档必须保持一致，接口变更先更新 `openapi.md`，再同步本文件。

## 1. 总体原则

本系统采用“统一编排 + 模块化能力服务”的方式实现完整链路。

核心原则：

1. 前端只调用 `api-gateway`，不直接调用各业务模块。
2. 完整业务流程由 `api-gateway` 统一编排。
3. 每个模块只负责自己的能力边界，对外暴露固定 HTTP API。
4. 每个模块必须提供 `GET /health` 健康检查接口。
5. 所有接口返回统一格式：`{ code, message, data }`。
6. 关键操作由 `api-gateway` 调用 `ledger-service` 进行存证。
7. 第一阶段先实现 Mock 版本跑通链路，再逐步替换真实算法。
8. 任何接口字段修改，必须先更新 `docs/api/openapi.md` 并经技术负责人确认。

统一响应格式（完整规则见 [`docs/api/response-and-errors.md`](../api/response-and-errors.md)）：

```json
{
  "code": 0,
  "message": "ok",
  "data": {},
  "traceId": "trace_20260710_000001"
}
```

统一错误格式（完整错误码见 [`docs/api/response-and-errors.md`](../api/response-and-errors.md)）：

```json
{
  "code": 40103,
  "message": "invalid signature",
  "data": null,
  "traceId": "trace_20260710_000001"
}
```

统一健康检查：

```http
GET /health
```

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "service": "service-name",
    "status": "healthy"
  },
  "traceId": "trace_20260710_000001"
}
```

## 2. 模块总览

| 编号 | 模块 | 目录 | 核心职责 | 主要调用方 |
|---|---|---|---|---|
| 0 | 统一编排模块 | `services/api-gateway` | 编排完整业务链路，提供演示总入口 | `web-dashboard` |
| 1 | 源端可信采集模块 | `services/meter-simulator` | 模拟电表数据、源端加密、签名、哈希 | `api-gateway` |
| 2 | 安全传输与数据接入模块 | `services/data-ingestion` | 接收密文数据、验签、登记数据资产 | `api-gateway` |
| 3 | DID 与授权模块 | `services/identity-did` | 主体身份、设备身份、授权申请与审批 | `api-gateway` |
| 4 | 联邦学习模块 | `services/federated-learning` | 真实轻量本地训练、模型参数上传、FedAvg 聚合、模型版本与指标管理 | `api-gateway` |
| 5 | 隐私计算模块 | `services/privacy-compute` | 同态加密参数保护、MPC/安全掩码聚合、参数摘要 | `api-gateway` / `federated-learning` |
| 6 | 区块链存证模块 | `services/ledger-service` | 关键操作、数据哈希、模型版本、Agent 调用存证 | `api-gateway` |
| 7 | Agent 业务模块 | `services/ai-agent` | 预测、交易策略、审计问答、报告生成 | `api-gateway` |
| 8 | 前端展示模块 | `apps/web-dashboard` | 系统可视化、链路展示、报告展示 | 用户 / `api-gateway` |
| 9 | 公共包模块 | `packages/common` | 公共模型、响应格式、工具函数、类型定义 | 所有后端模块 |

## 3. 完整业务链路

主流程为：

```text
前端点击“开始演示”
  -> api-gateway 接收请求
  -> meter-simulator 生成电表数据、加密、签名、哈希
  -> ledger-service 记录数据哈希存证
  -> identity-did 校验设备 DID 与主体 DID
  -> data-ingestion 接收密文数据并登记数据资产
  -> identity-did 创建并审批授权申请
  -> ledger-service 记录授权存证
  -> federated-learning 启动本地训练并生成模型参数
  -> ledger-service 记录训练轮次存证
  -> privacy-compute 对参数进行同态加密/安全掩码/MPC 安全聚合
  -> ledger-service 记录参数摘要和聚合结果存证
  -> federated-learning 执行 FedAvg 并生成 global_model_vN
  -> ledger-service 记录模型版本存证
  -> ai-agent 调用最新模型生成预测、交易策略、审计报告
  -> ledger-service 记录 Agent 调用存证
  -> api-gateway 汇总结果返回前端
```

主流程和状态规则见 [`docs/design/main-flow.md`](./main-flow.md)。主流程总入口：

```http
POST /api/v1/demo/run
```

返回示例：

```json
{
  "code": 0,
  "message": "demo finished",
  "data": {
    "readingBatchId": "batch_001",
    "assetId": "asset_001",
    "authId": "auth_001",
    "trainingTaskId": "fl_task_001",
    "globalModelVersion": "global_model_v1",
    "auditReportId": "report_001",
    "ledgerTxIds": [
      "tx_data_hash_001",
      "tx_auth_001",
      "tx_training_001",
      "tx_param_001",
      "tx_model_001",
      "tx_agent_001"
    ]
  }
}
```

## 4. 模块 0：统一编排模块

目录：`services/api-gateway`

### 功能与职责

`api-gateway` 是系统的主控模块，负责把各独立模块串成完整业务流程。

它负责：

1. 接收前端请求。
2. 调用各业务模块。
3. 控制完整演示流程顺序。
4. 收集各模块返回结果。
5. 调用 `ledger-service` 完成关键事件存证。
6. 将完整链路结果返回给前端。

它不负责：

1. 不实现具体加密算法。
2. 不实现联邦学习算法。
3. 不直接保存原始电表数据。
4. 不直接生成 AI 报告内容。

### 输入

来自前端的业务请求，例如：

```json
{
  "scenario": "vpp_day_ahead_trading",
  "participants": [
    "did:vpp:load-aggregator:001",
    "did:vpp:renewable-plant:001",
    "did:vpp:storage:001"
  ],
  "meterCount": 3,
  "trainingRounds": 3
}
```

### 输出

完整业务链路结果，包括数据批次、授权、训练任务、模型版本、存证交易、Agent 报告等。

### 具体操作

1. 调用 `meter-simulator` 生成源端可信数据。
2. 调用 `ledger-service` 记录数据哈希。
3. 调用 `identity-did` 校验 DID。
4. 调用 `data-ingestion` 登记数据资产。
5. 调用 `identity-did` 发起和审批授权。
6. 调用 `federated-learning` 创建训练任务。
7. 调用 `privacy-compute` 加密参数并安全聚合。
8. 调用 `federated-learning` 生成全局模型。
9. 调用 `ai-agent` 生成预测、策略和审计报告。
10. 调用 `ledger-service` 记录关键事件。

### 封装内容

建议封装：

```text
clients/meter_client.py
clients/identity_client.py
clients/ingestion_client.py
clients/fl_client.py
clients/privacy_client.py
clients/ledger_client.py
clients/agent_client.py
workflows/demo_workflow.py
```

### 对外接口

```http
POST /api/v1/demo/run
GET /api/v1/demo/status/{businessId}
GET /health
```

## 5. 模块 1：源端可信采集模块

目录：`services/meter-simulator`

### 功能与职责

模拟智能电表或采集终端，完成电表数据生成、源端加密、数字签名、时间戳和哈希。

它负责：

1. 模拟生成用电数据。
2. 使用 AES 对数据内容加密。
3. 使用设备私钥对数据摘要签名。
4. 生成 SHA-256 哈希。
5. 生成时间戳和批次 ID。

它不负责：

1. 不负责长期保存数据。
2. 不负责数据资产登记。
3. 不负责链上存证。
4. 不负责联邦学习训练。

### 输入

```json
{
  "meterId": "meter_001",
  "ownerDid": "did:vpp:load-aggregator:001",
  "count": 10,
  "intervalSeconds": 5
}
```

### 输出

```json
{
  "readingBatchId": "batch_001",
  "readings": [
    {
      "readingId": "reading_001",
      "meterId": "meter_001",
      "ownerDid": "did:vpp:load-aggregator:001",
      "ciphertext": "base64-ciphertext",
      "signature": "base64-signature",
      "hash": "sha256:abc123",
      "timestamp": "2026-07-10T10:00:00+08:00"
    }
  ]
}
```

### 具体操作

1. 生成明文用电数据，例如功率、电压、电流。
2. 将明文数据序列化为 JSON。
3. 使用 AES 加密 JSON。
4. 对密文和时间戳计算 SHA-256 哈希。
5. 使用设备私钥签名哈希。
6. 返回密文、签名、哈希和时间戳。

### 封装内容

```text
generate_reading()
generate_batch()
encrypt_reading()
sign_reading()
hash_reading()
```

### 对外接口

```http
POST /api/v1/meter/readings/generate
GET /health
```

## 6. 模块 2：安全传输与数据接入模块

目录：`services/data-ingestion`

### 功能与职责

接收源端密文数据，完成签名校验、数据元信息登记和数据资产目录发布。

它负责：

1. 接收密文电表数据。
2. 校验数据签名和哈希。
3. 保存数据元信息。
4. 登记数据资产。
5. 标记数据敏感级别和用途。

它不负责：

1. 不负责生成电表数据。
2. 不负责授权审批。
3. 不负责模型训练。
4. 不负责链上存证。

### 输入

```json
{
  "readingBatchId": "batch_001",
  "ownerDid": "did:vpp:load-aggregator:001",
  "readings": [
    {
      "readingId": "reading_001",
      "meterId": "meter_001",
      "ciphertext": "base64-ciphertext",
      "signature": "base64-signature",
      "hash": "sha256:abc123",
      "timestamp": "2026-07-10T10:00:00+08:00"
    }
  ]
}
```

### 输出

```json
{
  "assetId": "asset_001",
  "readingBatchId": "batch_001",
  "ownerDid": "did:vpp:load-aggregator:001",
  "assetType": "meter_readings",
  "sensitivityLevel": "private",
  "status": "registered"
}
```

### 具体操作

1. 接收 `meter-simulator` 输出的数据批次。
2. 根据 DID 公钥校验签名。
3. 重新计算哈希并与传入哈希比对。
4. 生成数据资产 ID。
5. 保存数据资产元信息。
6. 返回资产登记结果。

### 封装内容

```text
receive_encrypted_data()
verify_signature()
verify_hash()
register_data_asset()
get_asset_metadata()
```

### 对外接口

```http
POST /api/v1/data/ingest
POST /api/v1/data/assets
GET /api/v1/data/assets/{assetId}
GET /health
```

## 7. 模块 3：DID 与授权模块

目录：`services/identity-did`

### 功能与职责

管理参与主体、设备身份和数据使用授权流程。

它负责：

1. 注册主体 DID。
2. 注册设备 DID。
3. 校验主体身份。
4. 发起数据授权申请。
5. 审批或拒绝授权申请。
6. 查询授权状态。

它不负责：

1. 不负责保存原始电表数据。
2. 不负责训练模型。
3. 不负责存证实现。
4. 不负责前端页面展示。

### 输入

主体注册：

```json
{
  "name": "负荷聚合商 A",
  "type": "load_aggregator",
  "publicKey": "base64-public-key"
}
```

授权申请：

```json
{
  "requesterDid": "did:vpp:operator:001",
  "ownerDid": "did:vpp:load-aggregator:001",
  "assetId": "asset_001",
  "purpose": "federated_training_for_day_ahead_trading",
  "expireAt": "2026-08-01T00:00:00+08:00"
}
```

### 输出

```json
{
  "authId": "auth_001",
  "status": "approved",
  "requesterDid": "did:vpp:operator:001",
  "ownerDid": "did:vpp:load-aggregator:001",
  "assetId": "asset_001"
}
```

### 具体操作

1. 生成 DID 标识。
2. 绑定主体类型和公钥。
3. 校验请求方身份。
4. 创建授权申请。
5. 审批授权申请。
6. 返回授权结果。

### 封装内容

```text
register_subject()
register_device()
verify_did()
create_auth_request()
approve_auth_request()
get_auth_status()
```

### 对外接口

```http
POST /api/v1/identity/subjects
POST /api/v1/identity/devices
POST /api/v1/identity/verify
POST /api/v1/auth/requests
POST /api/v1/auth/requests/{authId}/approve
GET /api/v1/auth/requests/{authId}
GET /health
```

## 8. 模块 4：联邦学习模块

目录：`services/federated-learning`

### 功能与职责

负责实现轻量真实联邦学习 MVP，包括多主体本地训练、模型参数上传、FedAvg 聚合、全局模型版本管理和模型指标评估。

本项目需要真实联邦学习，但不做复杂生产级联邦学习平台。第一版采用“单服务内模拟多本地客户端”的方式实现，保证可运行、可解释、可演示。

它负责：

1. 创建联邦学习任务。
2. 为负荷聚合商、新能源场站、储能运营方模拟本地训练客户端。
3. 每个本地客户端只读取自己的本地数据分片。
4. 训练轻量模型并生成本地模型参数或梯度。
5. 接收或生成各主体模型更新摘要。
6. 调用 `privacy-compute` 执行参数保护或安全聚合。
7. 执行 FedAvg 生成全局模型。
8. 维护 `global_model_vN` 模型版本。
9. 输出 MAE、RMSE、MAPE 等模型效果指标。
10. 为 Agent 提供最新模型预测能力。

它不负责：

1. 不负责源端数据加密和签名。
2. 不负责 DID 授权审批。
3. 不负责同态加密和 MPC 算法本身。
4. 不直接写链，由 `api-gateway` 调用 `ledger-service` 存证。
5. 不第一阶段引入复杂跨机器训练框架。

### 真实联邦学习 MVP 范围

第一版建议范围：

```text
任务：虚拟电厂日前负荷预测 / 可调节容量预测
参与方：3 个主体
主体：负荷聚合商、新能源场站、储能运营方
模型：线性回归、轻量 MLP 或可解释的简单回归模型
轮次：3-5 轮
聚合算法：FedAvg
指标：MAE、RMSE、MAPE
部署：单服务内模拟多客户端，后续再拆为多服务或多机器
```

不建议第一版实现：

```text
复杂深度神经网络
完整工业级联邦学习平台
真实生产电力数据接入
全量同态加密训练
十几个节点跨机器训练
```

### 内部子组件

建议内部结构：

```text
services/federated-learning/
  server/
    task_manager        训练任务管理
    aggregator          FedAvg 聚合
    model_registry      模型版本管理
    metrics             MAE/RMSE/MAPE 指标计算
  clients/
    load_client         负荷聚合商本地训练节点
    renewable_client    新能源场站本地训练节点
    storage_client      储能运营方本地训练节点
  data/
    local_partitions    各主体本地数据分片
```

### 输入

创建训练任务：

```json
{
  "taskName": "虚拟电厂日前负荷预测联邦训练",
  "modelType": "load_forecast",
  "algorithm": "fedavg",
  "rounds": 3,
  "participants": [
    "did:vpp:load-aggregator:001",
    "did:vpp:renewable-plant:001",
    "did:vpp:storage:001"
  ],
  "assetIds": ["asset_001", "asset_002", "asset_003"],
  "target": "adjustable_capacity_kw"
}
```

本地参数上传：

```json
{
  "trainingTaskId": "fl_task_001",
  "roundId": 1,
  "participantDid": "did:vpp:load-aggregator:001",
  "sampleCount": 500,
  "modelUpdateUri": "storage://updates/fl_task_001/round_1/load_client.json",
  "updateHash": "sha256:update001"
}
```

### 输出

创建任务输出：

```json
{
  "trainingTaskId": "fl_task_001",
  "status": "created",
  "rounds": 3,
  "participants": [
    "did:vpp:load-aggregator:001",
    "did:vpp:renewable-plant:001",
    "did:vpp:storage:001"
  ]
}
```

聚合输出：

```json
{
  "trainingTaskId": "fl_task_001",
  "roundId": 3,
  "globalModelVersion": "global_model_v1",
  "modelHash": "sha256:model123",
  "participantCount": 3,
  "metrics": {
    "mae": 2.31,
    "rmse": 3.72,
    "mape": 0.081
  }
}
```

### 具体操作

1. 创建联邦学习任务。
2. 根据参与方 DID 加载各主体本地数据分片。
3. 初始化全局模型参数。
4. 每轮将当前全局模型下发给本地客户端。
5. 各本地客户端在本地数据上训练，生成模型参数更新。
6. 计算每个本地更新的哈希和样本数。
7. 将参数更新交给 `privacy-compute` 进行安全处理。
8. 获取安全聚合后的参数结果。
9. 执行 FedAvg 得到新一轮全局模型。
10. 计算 MAE、RMSE、MAPE。
11. 生成模型版本号和模型哈希。
12. 返回训练结果给 `api-gateway`。

### 封装内容

```text
create_training_task()
start_training()
load_local_partition()
start_local_training()
generate_model_update()
submit_model_update()
collect_model_updates()
fedavg_aggregate()
evaluate_model()
publish_global_model()
get_model_version()
get_training_metrics()
```

### 对外接口

```http
POST /api/v1/fl/tasks
POST /api/v1/fl/tasks/{taskId}/start
POST /api/v1/fl/tasks/{taskId}/rounds/{roundId}/updates
POST /api/v1/fl/tasks/{taskId}/rounds/{roundId}/aggregate
GET /api/v1/fl/tasks/{taskId}
GET /api/v1/fl/tasks/{taskId}/metrics
GET /api/v1/fl/models/{modelVersion}
GET /health
```

### 与其他模块关系

1. `api-gateway` 调用本模块创建任务和启动训练。
2. 本模块将模型参数摘要交给 `privacy-compute` 处理。
3. `api-gateway` 将训练开始、参数提交、模型生成等事件交给 `ledger-service` 存证。
4. `ai-agent` 通过 `api-gateway` 使用最新 `global_model_vN` 完成预测和报告生成。
## 9. 模块 5：隐私计算模块

目录：`services/privacy-compute`

### 功能与职责

负责模型参数上传前的隐私保护、安全聚合和参数摘要生成。

它负责：

1. 对模型参数进行同态加密演示。
2. 对模型参数添加安全掩码。
3. 执行 MPC 风格安全聚合。
4. 生成参数摘要哈希。
5. 输出安全聚合结果。

它不负责：

1. 不负责本地模型训练。
2. 不负责最终模型版本管理。
3. 不负责授权审批。
4. 不负责 Agent 报告。

### 输入

```json
{
  "trainingTaskId": "fl_task_001",
  "roundId": 1,
  "updates": [
    {
      "participantDid": "did:vpp:load-aggregator:001",
      "modelUpdateUri": "storage://updates/fl_task_001/round_1/sub_001.json",
      "updateHash": "sha256:update001"
    }
  ],
  "privacyMode": "secure_masking"
}
```

### 输出

```json
{
  "trainingTaskId": "fl_task_001",
  "roundId": 1,
  "aggregateResultUri": "storage://aggregates/fl_task_001/round_1/result.json",
  "aggregateHash": "sha256:agg001",
  "participantCount": 3,
  "privacyMode": "secure_masking"
}
```

### 具体操作

1. 接收各主体模型参数摘要和参数地址。
2. 对参数进行同态加密或安全掩码处理。
3. 执行安全聚合。
4. 生成聚合结果文件。
5. 计算聚合结果哈希。
6. 返回聚合结果摘要。

### 封装内容

```text
encrypt_model_update()
mask_model_update()
generate_update_hash()
secure_aggregate()
mpc_secure_aggregate()
verify_aggregate_result()
```

### 对外接口

```http
POST /api/v1/privacy/model-updates/encrypt
POST /api/v1/privacy/model-updates/mask
POST /api/v1/privacy/secure-aggregate
GET /api/v1/privacy/aggregates/{aggregateId}
GET /health
```

## 10. 模块 6：区块链存证模块

目录：`services/ledger-service`

### 功能与职责

负责记录关键操作和关键数据摘要，形成完整审计证据链。

它负责：

1. 记录 DID 注册事件。
2. 记录数据哈希。
3. 记录授权事件。
4. 记录训练轮次。
5. 记录模型参数摘要。
6. 记录安全聚合结果摘要。
7. 记录模型版本哈希。
8. 记录 Agent 调用和报告生成事件。
9. 按业务 ID 查询完整证据链。

它不负责：

1. 不保存原始电表数据。
2. 不保存明文模型参数。
3. 不执行联邦训练。
4. 不判断业务是否合理。

### 输入

```json
{
  "eventType": "global_model_created",
  "businessId": "fl_task_001",
  "subjectDid": "did:vpp:operator:001",
  "payloadHash": "sha256:model123",
  "payloadUri": "storage://models/global_model_v1.pkl",
  "description": "global_model_v1 generated by secure FedAvg",
  "metadata": {
    "modelVersion": "global_model_v1",
    "rounds": 3,
    "participantCount": 3
  }
}
```

### 输出

```json
{
  "ledgerTxId": "tx_001",
  "eventId": "evt_001",
  "blockHeight": 1024,
  "currentHash": "sha256:event001"
}
```

### 具体操作

1. 接收存证事件。
2. 校验事件字段完整性。
3. 生成事件 ID。
4. 计算当前事件哈希。
5. 关联上一事件哈希，形成哈希链。
6. 写入模拟链或联盟链。
7. 返回交易 ID。
8. 支持按 `businessId` 查询证据链。

### 封装内容

```text
record_event()
record_data_hash()
record_auth_event()
record_training_round()
record_param_digest()
record_model_version()
record_agent_call()
query_trace()
```

### 对外接口

```http
POST /api/v1/ledger/events
GET /api/v1/ledger/events/{eventId}
GET /api/v1/ledger/traces/{businessId}
GET /health
```

建议固定事件类型：

```text
did_registered
meter_data_collected
meter_data_ingested
data_asset_registered
auth_requested
auth_approved
training_started
training_finished
model_update_submitted
secure_aggregation_finished
global_model_created
agent_prediction_called
agent_report_generated
audit_trace_queried
```

## 11. 模块 7：Agent 业务模块

目录：`services/ai-agent`

### 功能与职责

负责将模型结果转化为业务能力，包括预测、交易策略、审计问答和报告生成。

它负责：

1. 调用最新全局模型进行预测。
2. 生成虚拟电厂交易策略建议。
3. 查询审计链路并回答问题。
4. 生成交易审计报告。
5. 输出可展示的业务结论。

它不负责：

1. 不直接访问原始电表数据。
2. 不训练模型。
3. 不审批授权。
4. 不直接写链，由 `api-gateway` 编排存证。

### 输入

预测请求：

```json
{
  "modelVersion": "global_model_v1",
  "scenario": "day_ahead_trading",
  "input": {
    "date": "2026-07-11",
    "temperature": 34,
    "marketPrice": 0.68
  }
}
```

审计报告请求：

```json
{
  "businessId": "fl_task_001",
  "reportType": "transaction_audit"
}
```

### 输出

```json
{
  "auditReportId": "report_001",
  "title": "虚拟电厂日前交易审计报告",
  "summary": "本次交易使用 global_model_v1 完成可调节容量预测，参与主体 3 个，原始数据未出域，关键操作均已存证。",
  "riskLevel": "low",
  "recommendations": [
    "建议申报可调节容量 120MW",
    "建议保留 10% 安全裕度"
  ]
}
```

### 具体操作

1. 获取最新模型版本或指定模型版本。
2. 调用模型预测接口或本地模型文件。
3. 生成可调节容量预测。
4. 生成交易策略建议。
5. 查询 ledger 证据链摘要。
6. 生成审计报告。
7. 返回给 `api-gateway`。

### 封装内容

```text
predict_capacity()
generate_trading_strategy()
answer_audit_question()
generate_audit_report()
get_model_explanation()
```

### 对外接口

```http
POST /api/v1/agent/predict
POST /api/v1/agent/trading-strategy
POST /api/v1/agent/audit-question
POST /api/v1/agent/audit-report
GET /health
```

## 12. 模块 8：前端展示模块

目录：`apps/web-dashboard`

### 功能与职责

负责系统可视化展示和演示操作入口。

它负责：

1. 展示系统总览。
2. 提供“一键演示”按钮。
3. 展示源端数据可信采集结果。
4. 展示授权审批状态。
5. 展示联邦训练任务和模型版本。
6. 展示链上审计证据链。
7. 展示 Agent 预测、交易策略和审计报告。

它不负责：

1. 不直接调用除 `api-gateway` 以外的后端模块。
2. 不实现业务算法。
3. 不保存核心业务数据。

### 输入

用户点击、筛选条件、业务 ID。

### 输出

页面展示、报告预览、审计链路图。

### 具体操作

1. 调用 `POST /api/v1/demo/run`。
2. 展示返回的业务 ID 和链路结果。
3. 调用 `GET /api/v1/demo/status/{businessId}` 查询状态。
4. 展示报告和审计链路。

### 封装页面

```text
Dashboard 首页
Demo 一键演示页
源端可信采集页
联邦学习任务页
隐私计算页
链上审计页
Agent 报告页
```

### 对外接口

前端本身不对外提供业务接口，只调用 `api-gateway`。

## 13. 模块 9：公共包模块

目录：`packages/common`

### 功能与职责

沉淀所有模块共享的数据结构、响应格式、错误码和工具函数。

它负责：

1. 定义统一响应结构。
2. 定义通用错误码。
3. 定义业务 ID 命名规则。
4. 定义通用 DTO/Schema。
5. 提供哈希、时间、签名等通用工具函数。

### 建议封装

```text
response.py
errors.py
schemas.py
hashing.py
time_utils.py
id_generator.py
```

## 14. 模块开发顺序

### 阶段一：Mock 链路打通

目标：所有模块先返回固定 JSON，让完整链路跑通。这个阶段不追求算法复杂度，只追求系统可集成、前端可演示、接口可稳定。

开发顺序：

1. `packages/common`：统一响应格式、错误码、ID 命名规则。
2. `api-gateway`：实现 `POST /api/v1/demo/run` 的 Mock 编排。
3. `ledger-service`：实现 `POST /api/v1/ledger/events` Mock 存证。
4. `meter-simulator`：实现 `POST /api/v1/meter/readings/generate` Mock 数据。
5. `identity-did`：实现主体注册和授权审批 Mock。
6. `data-ingestion`：实现数据资产登记 Mock。
7. `federated-learning`：实现训练任务、训练轮次、模型版本和指标的 Mock 返回。
8. `privacy-compute`：实现参数摘要和安全聚合 Mock。
9. `ai-agent`：实现审计报告 Mock。
10. `web-dashboard`：实现一键演示页面。
11. `infra/docker-compose`：一键启动所有 Mock 服务。

验收标准：

```text
前端点击“开始演示”后，能看到完整链路结果：数据批次、资产 ID、授权 ID、训练任务、模型版本、模型指标、存证交易、Agent 报告。
```

### 阶段二：真实轻量联邦学习 MVP

目标：在不引入重型联邦学习平台的前提下，实现真实可运行的 FedAvg。这个阶段是方案可信度的核心。

开发顺序：

1. `datasets/synthetic-vpp`：准备可训练数据，字段至少包含时间、天气、负荷、新能源出力、储能状态、电价和预测目标。
2. `federated-learning`：实现 2-3 个本地客户端的数据分片加载。
3. `federated-learning`：实现轻量本地训练模型，优先选择线性回归、轻量 MLP 或可解释回归模型。
4. `federated-learning`：实现本地模型参数或梯度输出。
5. `federated-learning`：实现 FedAvg 聚合。
6. `federated-learning`：实现 `global_model_vN` 模型版本管理。
7. `federated-learning`：输出 MAE、RMSE、MAPE 指标。
8. `ledger-service`：记录 `training_started`、`model_update_submitted`、`global_model_created`、`model_evaluated`。
9. `api-gateway`：将 Mock 训练流程替换为真实训练流程。
10. `ai-agent`：使用真实 `global_model_vN` 生成预测和交易建议。

验收标准：

```text
系统可完成 3 个主体、3-5 轮真实 FedAvg 训练，生成 global_model_v1，输出 MAE/RMSE/MAPE，并能由 Agent 调用该模型完成预测。
```

### 阶段三：源端可信与链上审计真实能力替换

目标：把安全链路从 Mock 升级为可演示的真实能力。

开发顺序：

1. `meter-simulator`：实现真实用电数据生成、AES 加密、签名、SHA-256 哈希。
2. `identity-did`：实现 DID 注册、公钥绑定和验签支持。
3. `data-ingestion`：实现签名校验、哈希校验和资产登记。
4. `ledger-service`：实现哈希链式存证或接入 FISCO BCOS。
5. `web-dashboard`：展示真实数据哈希、授权记录、训练轮次和模型版本证据链。

验收标准：

```text
源端数据可加密签名，篡改后验签失败，关键操作可按 businessId 查询完整存证链路。
```

### 阶段四：隐私计算增强与比赛展示

目标：形成可打分、可演示、可写进报告的创新能力。该阶段增强参数隐私保护，但不阻塞阶段二的真实联邦学习。

开发顺序：

1. `privacy-compute`：实现参数安全掩码聚合。
2. `privacy-compute`：实现同态加密参数聚合 demo。
3. `privacy-compute`：实现 MPC 风格安全聚合 demo。
4. 增加传输劫持对比演示：明文方案 vs 加密方案。
5. 增加数据篡改检测演示：篡改后验签失败。
6. 增加联邦模型效果对比：单主体模型 vs 联邦模型。
7. 增加审计效率指标：按 `businessId` 秒级查询证据链。
8. 增加 Agent 审计问答和交易策略解释。
9. 完成部署手册、操作说明、演示视频脚本。

验收标准：

```text
系统能展示“源端可信、数据不出域、真实联邦训练、参数不可见、模型可追溯、Agent 可解释”的完整闭环。
```

### 实现策略总结

```text
Mock 先串通链路，真实 FedAvg 证明核心能力，隐私计算增强展示创新，链上审计贯穿全过程。
```
## 15. Issue 拆分建议

第一批 P0 Issue：Mock 链路与接口契约

```text
[P0][架构] 编写 docs/design/main-flow.md
[P0][架构] 编写 docs/api/openapi.md
[P0][公共] 定义统一响应格式和错误码
[P0][网关] 实现 POST /api/v1/demo/run Mock 编排
[P0][存证] 实现 POST /api/v1/ledger/events Mock 存证
[P0][部署] 实现 docker-compose 启动所有 Mock 服务
[P0][前端] 实现一键演示页面
```

第二批 P1 Issue：真实轻量联邦学习 MVP

```text
[P1][数据] 构建可训练的 synthetic-vpp 数据集
[P1][联邦学习] 实现本地客户端数据分片加载
[P1][联邦学习] 实现本地训练和模型参数生成
[P1][联邦学习] 实现 FedAvg 聚合
[P1][联邦学习] 实现 global_model_vN 模型版本管理
[P1][联邦学习] 输出 MAE、RMSE、MAPE 指标
[P1][存证] 增加训练轮次、参数提交、模型版本、模型评估事件
[P1][Agent] 使用真实 global_model_vN 完成预测和交易建议
```

第三批 P2 Issue：源端可信与审计真实能力

```text
[P2][源端采集] 实现电表数据生成、AES 加密、签名、哈希
[P2][DID] 实现主体 DID 注册与设备 DID 注册
[P2][数据接入] 实现密文数据接收、签名校验和哈希校验
[P2][存证] 实现按 businessId 查询审计链路
[P2][前端] 展示训练轮次、参数摘要、模型版本和审计链路
```

第四批 P3 Issue：隐私计算增强与比赛展示

```text
[P3][隐私计算] 实现参数安全掩码聚合
[P3][隐私计算] 实现同态加密参数保护 demo
[P3][隐私计算] 实现 MPC 风格安全聚合 demo
[P3][安全演示] 实现数据截获和篡改对比演示
[P3][模型评估] 实现单主体模型 vs 联邦模型对比
[P3][Agent] 实现审计问答和交易策略解释
[P3][文档] 完成部署手册、操作说明和演示视频脚本
```
## 16. 给 Agent 的开发提示词模板

每个成员使用 Agent 写代码时，必须使用类似提示词：

```text
你正在开发 vpp-trusted-data-space 项目的 [模块名] 服务。

请严格遵守：
1. 不要修改其他模块代码。
2. 只在 services/[模块名] 下开发。
3. 必须提供 GET /health。
4. 必须实现 Issue 中指定的接口。
5. 请求和响应必须符合 docs/api/openapi.md。
6. 返回格式必须是 { code, message, data }。
7. 必须提供 README.md，说明如何启动和测试。
8. 必须提供最小测试或 curl 调用示例。
9. 不要改变接口字段名，除非先修改 docs/api/openapi.md 并通知技术负责人。

当前任务：
[粘贴 Issue 内容]
```

## 17. 最终协作规则

1. 模块负责人只改自己模块目录。
2. 接口修改必须先改文档，再改代码。
3. 所有 PR 必须说明调用方、接口、输入、输出和验收方式。
4. `api-gateway` 合并前必须能调用该模块接口。
5. `docker-compose` 启动失败的 PR 不允许合并到 `develop`。
6. 第一周目标不是算法最强，而是链路最先跑通。

7. 所有接口路径和字段必须与 [`docs/api/openapi.md`](../api/openapi.md) 一致。
8. 所有错误码必须与 [`docs/api/response-and-errors.md`](../api/response-and-errors.md) 一致，不得在模块内自定义同义错误码。

一句话总结：

```text
模块负责能力，api-gateway 负责编排，ledger-service 负责存证，web-dashboard 负责展示。
```

