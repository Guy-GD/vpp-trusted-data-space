---
name: Task
description: 开发功能任务（接口契约与联调）
title: "[P0][模块名] 任务名称"
labels: []
assignees: []
---

## 基本信息

- 优先级：`P0` / `P1` / `P2` / `P3`
- 所属模块：`api-gateway` / `meter-simulator` / `data-ingestion` / `identity-did` / `federated-learning` / `privacy-compute` / `ledger-service` / `ai-agent` / `web-dashboard` / `packages/common`
- 负责人：@
- 截止时间：
- 依赖或阻塞：`无` / `#Issue编号`

## 任务目标

说明本任务要交付的可验证能力，而不是笼统描述整个模块。

## 不在本任务范围

明确本次不实现的能力，避免任务范围扩张。

## 接口契约

- [ ] 本任务不涉及 HTTP 接口变更。
- [ ] 本任务新增或修改 HTTP 接口；请填写下表。

| 调用方 | HTTP 方法与路径 | 请求关键字段 | 响应关键字段 | 错误码 | 契约来源 |
|---|---|---|---|---|---|
|  |  |  |  |  | `docs/api/openapi.md` |

涉及路径、方法、字段、枚举、状态或错误码变更时，先更新 `docs/api/openapi.md`，再同步 `docs/design/module-contracts.md`；影响跨模块时序时同步 `docs/design/main-flow.md`；公共响应或错误码变化时同步 `docs/api/response-and-errors.md`。

## 实现要求

- [ ] 后端服务提供 `GET /health`，并使用统一 `{ code, message, data, traceId }` 响应包络。
- [ ] 写操作按契约处理 `Idempotency-Key`。
- [ ] 服务间调用传递 `X-Trace-Id`；适用时传递 `X-Caller-Did`。
- [ ] 前端只调用 `api-gateway`，不直连业务服务。
- [ ] 不输出原始电表明文、未保护模型参数、密钥、令牌或敏感个人信息。
- [ ] P0 任务使用稳定 Mock 数据打通链路，不提前实现未排期的真实算法。

不适用的项目请写明原因：

## 验收清单

- [ ] 正常路径已验证，结果符合 OpenAPI 字段和类型。
- [ ] 至少一个失败路径已验证，错误码符合 `docs/api/response-and-errors.md`。
- [ ] 涉及写操作时，已验证相同 `Idempotency-Key` 的重复请求行为。
- [ ] 后端服务已验证 `GET /health`；前端已验证仅通过网关调用。
- [ ] `api-gateway` 调用本模块接口的联调状态已说明。
- [ ] 已说明本任务对 `docker-compose` 的影响：无影响 / 已更新 / 尚不适用。

## 交付物

- [ ] 源码或前端页面。
- [ ] 单元测试、接口测试或可复现的手工验证步骤。
- [ ] 模块 README 中的启动与测试说明（如本任务首次引入该模块）。
- [ ] 必要的契约文档更新。
