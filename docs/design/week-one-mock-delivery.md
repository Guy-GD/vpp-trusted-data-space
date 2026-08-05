# 第一周全链路 Mock 交付设计

> **文档职责**：本文档定义第一周的团队分工、技术基线、跨模块依赖、七天执行节奏、验收门槛、风险控制和最终演示标准。模块长期职责以 `docs/design/module-contracts.md` 为准，HTTP 接口字段以 `docs/api/openapi.md` 为准，统一响应和错误码以 `docs/api/response-and-errors.md` 为准。

## 1. 背景与目标

团队共 10 人：

- 1 人负责技术统筹、接口契约、公共包和最终验收。
- 8 人分别负责 8 个后端服务。
- 1 人负责前端展示。

团队可连续 7 天投入大部分开发时间。仓库当前已经具备模块目录、接口契约、Issue/PR 模板和基础 CI，但各服务、前端、部署和测试仍以目录骨架为主。

第一周唯一最高优先级目标是：

```text
在一台全新环境中执行 Docker Compose 一键启动，
用户通过前端点击一次“开始演示”，
系统通过真实 HTTP 调用完成全链路 Mock，
并展示数据批次、资产、授权、训练、隐私聚合、模型、存证和 Agent 结果。
```

### 1.1 第一周交付原则

```text
业务能力允许 Mock，工程链路必须真实。
```

允许 Mock 的内容：

- 内存存储。
- 可重复的模拟电表数据。
- 模拟密文、签名和哈希。
- 模拟 DID 和授权审批。
- 模拟本地训练、模型更新、FedAvg 指标和模型版本。
- 模拟安全掩码、同态加密和 MPC 聚合结果。
- 内存哈希链代替真实区块链。
- 稳定模板代替真实 Agent 模型推理。

必须真实完成的内容：

- FastAPI HTTP 服务。
- 请求和响应 Schema 校验。
- 服务间 HTTP 调用。
- 动态业务 ID 和状态流转。
- 统一错误响应、追踪 ID 和基本幂等。
- Docker 镜像和 Compose 编排。
- 前端真实调用网关。
- 单元测试、接口测试和端到端测试。
- 异常路径和可定位错误信息。

### 1.2 非目标

第一周不实现：

- 生产数据库。
- FISCO BCOS 或其他真实区块链网络。
- 真实 AES 密钥体系和生产级数字签名。
- 真实跨节点联邦学习。
- 生产级同态加密和 MPC。
- 真实大模型或外部 Agent 平台调用。
- MQTT 接入。
- 复杂多页面前端、权限系统和微前端。

上述能力在后续阶段替换对应 Mock 实现，不改变第一周冻结的模块边界和 HTTP 契约。

## 2. 技术基线

### 2.1 后端

8 个后端服务统一使用：

```text
语言：Python 3.11
Web 框架：FastAPI
数据模型：Pydantic v2
服务启动：Uvicorn
服务通信：HTTP/1.1 + JSON
HTTP 客户端：httpx
测试：pytest + FastAPI TestClient/httpx
```

依赖要求：

- 每个模块锁定自己的直接依赖版本。
- FastAPI 必须使用兼容 Pydantic v2 的版本。
- 不允许成员自行替换为 Flask、Django、Spring Boot 或其他框架。
- 模块间不得通过导入对方源码完成业务调用。

### 2.2 前端

前端统一使用：

```text
运行时：Node.js 24 LTS
框架：Vue 3
构建工具：Vite
语言：JavaScript
组件库：Element Plus
HTTP 客户端：Axios
```

第一周不使用 TypeScript、Pinia、Nuxt 和复杂自定义组件体系。前端只实现一页演示控制台。

### 2.3 编码与文件格式

- 所有源码、Markdown、YAML、JSON 和环境变量示例使用 UTF-8。
- Windows PowerShell 5 读取 UTF-8 无 BOM 文档时必须显式使用 `Get-Content -Encoding UTF8`。
- 禁止提交真实 `.env`、密钥、令牌、密码、生产数据和模型参数。
- 提交 `.env.example`，仅包含非敏感示例值。

## 3. 第一周统一编排边界

第一周由 `api-gateway` 统一编排跨模块业务流程。除健康检查外，前端只调用网关；业务服务不直接写账本。

```text
web-dashboard
  -> api-gateway
      -> meter-simulator
      -> identity-did
      -> data-ingestion
      -> federated-learning
      -> privacy-compute
      -> ledger-service
      -> ai-agent
```

第一周主流程顺序：

1. 前端调用 `POST /api/v1/demo/run`。
2. 网关调用 `meter-simulator` 生成动态读数批次。
3. 网关调用 `ledger-service` 记录采集事件。
4. 网关调用 `identity-did` 验证主体与设备身份。
5. 网关调用 `data-ingestion` 接收批次并登记资产。
6. 网关调用 `ledger-service` 记录资产事件。
7. 网关创建并审批授权申请。
8. 网关调用 `ledger-service` 记录授权事件。
9. 网关创建并启动联邦训练任务，取得第 1 轮 `currentRound` 与 `updates`。
10. 每轮由网关先调用 `privacy-compute` 完成安全聚合，再将聚合结果交给 `federated-learning` 执行 FedAvg。
11. 非最终轮按 FL 返回的 `nextRound` 与下一轮完整 `updates` 继续步骤 10；最终轮取得模型版本、哈希和指标。
12. 网关记录每轮训练、聚合和最终模型事件。
13. 网关调用 `ai-agent` 完成预测、交易策略和审计报告。
14. 网关记录 Agent 调用事件并返回完整汇总结果。

### 3.1 已冻结决策与完成状态

以下联调决策已经冻结并同步到正式契约，完成状态为“已完成”；实现者不得再自行发明替代字段或调用方向：

1. 第一周统一由网关编排；联邦学习服务不直接调用隐私计算或账本，其他业务服务也不直接写账本。
2. `POST /api/v1/fl/tasks/{taskId}/start` 返回第 1 轮 `currentRound` 和完整 `updates`，更新项包含 `participantDid`、`sampleCount`、`modelUpdateUri`、`updateHash`。
3. 每轮网关先调用 privacy secure-aggregate，再调用 FL aggregate。非最终轮返回 `status: running`、整数 `nextRound` 和下一轮完整 `updates`；最终轮返回 `status: completed`、`nextRound: null`、`updates: []` 及最终模型版本、哈希、指标。
4. 更新提交与 FL aggregate 的 `taskId`、`roundId` 只来自路径；请求体不重复路径 ID。
5. `POST /api/v1/data/ingest` 返回 `assetId`；`POST /api/v1/data/assets` 是独立资产元信息登记接口，不参与主流程。
6. `POST /api/v1/demo/run` 的业务 `data` 统一包含 `businessId`、模型指标、Agent 结果标识和存证交易 ID；`traceId` 只存在于公共响应包络，并与响应头 `X-Trace-Id` 一致。

上述完成状态由契约测试持续校验；任何后续变更仍须遵循第 10.2 节流程。

## 4. 人员分工

采用“模块主责 + 横向副职责”。模块负责人对自己的目录、接口、测试、Dockerfile 和 README 负责，同时承担一个横向工程职责。

| 角色 | 第一主责 | 横向副职责 |
|---|---|---|
| 技术负责人 | 技术统筹、接口契约、`packages/common`、PR 决策、最终验收 | 每日集成、风险清单、版本冻结 |
| api-gateway 负责人 | 网关、下游客户端和主流程状态 | 集成测试负责人 |
| meter-simulator 负责人 | 采集 Mock 服务 | 标准 Mock 数据与测试夹具 |
| data-ingestion 负责人 | 数据接入 Mock 服务 | 接口契约一致性检查 |
| identity-did 负责人 | DID 与授权 Mock 服务 | 身份、授权和失败场景检查 |
| federated-learning 负责人 | 训练任务、轮次、指标和模型版本 Mock | 后端工程规范复核 |
| privacy-compute 负责人 | 参数保护与聚合 Mock | Docker Compose 和环境变量 |
| ledger-service 负责人 | 存证、事件和证据链 Mock | 审计事件完整性检查 |
| ai-agent 负责人 | 预测、策略、问答和报告 Mock | 演示数据与演示脚本 |
| web-dashboard 负责人 | Vue 一键演示页面 | 前端验收截图和操作说明 |

## 5. 技术负责人的职责

技术负责人第一周不再承包完整业务模块，主要交付如下。

### 5.1 Day 1 直接交付

负责 `packages/common` 第一版：

```text
packages/common/
  response.py
  errors.py
  schemas.py
  id_generator.py
  time_utils.py
  tracing.py
  tests/
  pyproject.toml
  README.md
```

公共包只包含跨模块基础能力：

- `ApiResponse`、成功响应和失败响应构造。
- 稳定公共错误码。
- `traceId` 读取与生成。
- ISO 8601 时间生成。
- 统一业务 ID 前缀和生成逻辑。
- 跨模块基础 Schema。

公共包禁止包含：

- 模块专属 DTO。
- 数据库模型。
- 网关工作流。
- 加密、联邦学习、隐私计算或账本业务逻辑。
- 任何服务的环境配置。

公共包第一版必须在 Day 1 中午前冻结。之后只接受解决阻塞问题的兼容性修改。

### 5.2 持续职责

- 审核接口路径、字段、状态和错误码变更。
- 保证 `openapi.md`、`module-contracts.md`、`main-flow.md` 和公共错误码一致。
- 分配 Issue，检查负责人、依赖、截止时间和验收命令。
- 每天至少执行一次全量合并和 Compose 主流程检查。
- 维护 Blocked 清单并在当天处理跨模块阻塞。
- 控制范围，禁止第一周提前实现真实算法挤占联调时间。
- 主持 Day 7 全新环境验收并冻结 `week1-mock-v0.1.0`。

## 6. 各模块任务与验收

### 6.1 api-gateway

必须实现：

- `POST /api/v1/demo/run`
- `GET /api/v1/demo/status/{businessId}`
- `GET /health`
- 7 个业务服务的异步 HTTP 客户端。
- 主流程状态机。
- `X-Trace-Id` 生成和下游透传。
- 下游超时、不可用和非法响应转换。
- `Idempotency-Key` 重试结果复用。

验收：

- 网关不得自己伪造全部下游结果。
- 停止任意一个关键下游后，返回对应 `5xxxx` 错误和 `traceId`。
- 相同幂等键、相同请求体返回相同 `businessId`。
- 相同幂等键、不同请求体返回 `40901`。
- 状态查询不重复执行主流程。

### 6.2 meter-simulator

必须实现：

- `POST /api/v1/meter/readings/generate`
- `GET /health`
- 动态 `readingBatchId` 和 `readingId`。
- 固定随机种子下可复现的模拟读数。
- 格式稳定的 Mock `ciphertext`、`signature` 和 `hash`。

验收：

- 返回读数数量与 `count` 一致。
- 每条读数包含完整契约字段。
- 非法 `count`、无效 DID 等请求返回公共错误码。
- 相同幂等键不会生成第二个批次。

### 6.3 data-ingestion

必须实现：

- `POST /api/v1/data/ingest`
- `POST /api/v1/data/assets`
- `GET /api/v1/data/assets/{assetId}`
- `GET /health`
- 内存资产仓库。
- Mock 验签和验哈希逻辑。

验收：

- 接收合法批次后可使用 `assetId` 查询。
- 篡改 `hash` 返回 `40104`。
- 篡改 `signature` 返回 `40103`。
- 响应和日志不出现原始明文数据。

### 6.4 identity-did

必须实现：

- `POST /api/v1/identity/subjects`
- `POST /api/v1/identity/devices`
- `POST /api/v1/identity/verify`
- `POST /api/v1/auth/requests`
- `POST /api/v1/auth/requests/{authId}/approve`
- `GET /api/v1/auth/requests/{authId}`
- `GET /health`
- 内存主体、设备和授权仓库。

验收：

- 主体和设备创建后可以验证。
- 授权按 `requested -> approved` 流转。
- 未知 DID 返回 `40102`。
- 已过期授权返回 `40303`。
- 非法状态重复审批返回 `40902`。

### 6.5 federated-learning

必须实现：

- `POST /api/v1/fl/tasks`
- `POST /api/v1/fl/tasks/{taskId}/start`
- `POST /api/v1/fl/tasks/{taskId}/rounds/{roundId}/updates`
- `POST /api/v1/fl/tasks/{taskId}/rounds/{roundId}/aggregate`
- `GET /api/v1/fl/tasks/{taskId}`
- `GET /api/v1/fl/tasks/{taskId}/metrics`
- `GET /api/v1/fl/models/{modelVersion}`
- `GET /health`
- 3 个参与方、3 轮训练的内存状态机。
- 动态模型版本和稳定 Mock 指标。

验收：

- 任务状态按 `created -> running -> completed` 流转。
- 启动结果提供当前轮次模型更新摘要。
- 更新数量不足返回 `42202`。
- 未完成安全聚合时不能生成模型。
- 完成后可查询 `global_model_v1` 和 MAE/RMSE/MAPE。

### 6.6 privacy-compute

必须实现：

- `POST /api/v1/privacy/model-updates/encrypt`
- `POST /api/v1/privacy/model-updates/mask`
- `POST /api/v1/privacy/secure-aggregate`
- `GET /api/v1/privacy/aggregates/{aggregateId}`
- `GET /health`
- 内存聚合结果仓库。

验收：

- 支持 `homomorphic_demo`、`secure_masking` 和 `mpc_demo` 的稳定 Mock 输出。
- 聚合结果可按 `aggregateId` 查询。
- 参与方数量与输入更新一致。
- 不支持的模式返回 `42203`。
- 更新数量不足返回 `42202`。
- 响应不返回单个参与方的明文更新。

### 6.7 ledger-service

必须实现：

- `POST /api/v1/ledger/events`
- `GET /api/v1/ledger/events/{eventId}`
- `GET /api/v1/ledger/traces/{businessId}`
- `GET /health`
- 内存事件仓库和简化哈希链。

验收：

- 新事件关联 `previousHash` 并生成 `currentHash`。
- 可按 `businessId` 返回时间有序的完整证据链。
- 相同事件幂等重试不产生重复记录。
- 冲突重复事件返回 `40903`。
- 账本数据只包含事件、摘要、URI 和审计元数据。

### 6.8 ai-agent

必须实现：

- `POST /api/v1/agent/predict`
- `POST /api/v1/agent/trading-strategy`
- `POST /api/v1/agent/audit-question`
- `POST /api/v1/agent/audit-report`
- `GET /health`
- 可重复、可展示的模板化业务结果。

验收：

- 指定模型版本后生成动态 `predictionId`。
- 交易策略引用预测结果并提供安全裕度和解释。
- 审计问答返回证据事件 ID。
- 审计报告包含模型版本、参与主体、风险级别和建议。
- 不存在的模型版本返回 `40404`。

### 6.9 web-dashboard

必须实现一个单页演示控制台：

- 系统名称和服务状态区。
- 场景参数和“一键开始演示”按钮。
- 采集、接入、授权、训练、聚合、模型、Agent 步骤状态。
- 批次、资产、授权、训练任务、模型版本和指标展示。
- 存证交易和审计报告展示。
- 失败阶段、错误码、`message` 和 `traceId` 展示。
- 使用 `businessId` 重新查询状态。

验收：

- 只调用 `api-gateway`。
- 请求中有加载状态，执行期间禁止重复点击。
- 后端失败时不显示“成功完成”。
- API 基础地址通过环境变量配置。
- `npm run build` 成功。
- Compose 环境中可访问网关。

## 7. 横向工程任务

### 7.1 Docker Compose

由 privacy-compute 负责人主责，技术负责人和网关负责人复核。

必须交付：

- 根级或 `infra/docker-compose` 下的 Compose 文件。
- 8 个后端、前端共 9 个服务。
- 服务环境变量。
- 健康检查。
- 启动依赖。
- 独立 Dockerfile。
- `.env.example`。

端口冻结如下：

| 服务 | 容器端口 | 本机端口 |
|---|---:|---:|
| web-dashboard | `80` | `3000` |
| api-gateway | `8000` | `8000` |
| meter-simulator | `8000` | `8001` |
| data-ingestion | `8000` | `8002` |
| identity-did | `8000` | `8003` |
| federated-learning | `8000` | `8004` |
| privacy-compute | `8000` | `8005` |
| ledger-service | `8000` | `8006` |
| ai-agent | `8000` | `8007` |

容器间使用服务名访问，例如：

```text
http://ledger-service:8000
```

### 7.2 集成与端到端测试

由 api-gateway 负责人主责，ai-agent 和 web-dashboard 负责人协助。

必须覆盖：

- 8 个服务健康检查。
- 主流程正常路径。
- 状态查询。
- 相同幂等键重试。
- 无效 DID 或篡改数据失败。
- 下游服务不可用。
- 账本证据链完整性。
- 前端一键演示。

### 7.3 CI

当前 CI 只检查目录存在，第一周必须增加：

- Python 依赖安装和公共包测试。
- 8 个后端模块测试。
- 前端依赖安装和生产构建。
- Compose 配置校验。
- 接口路径覆盖校验。
- 禁止提交真实 `.env` 和常见密钥文件。

CI 不要求在 GitHub Actions 中运行完整 Compose E2E；完整 E2E 可以作为本地或验收环境命令，但必须可复现。

## 8. 七天执行节奏

| 日期 | 合并门槛 |
|---|---|
| Day 1 | 契约歧义清零；公共包第一版合并；8 个服务可启动且 `/health` 通过；前端工程可启动；Compose 初版存在 |
| Day 2 | 各模块全部契约接口完成正常路径；前端完成静态页面和示例 JSON 展示 |
| Day 3 | 各模块完成失败路径、动态 ID、状态、幂等和模块测试；网关下游客户端完成 |
| Day 4 | 网关通过真实 HTTP 串通全部后端；Compose 能启动 9 个服务 |
| Day 5 | 前端接入真实网关；一键演示首次完整跑通 |
| Day 6 | 完成异常场景、CI、E2E、README、UTF-8 和环境兼容问题 |
| Day 7 | 全新环境最终验收、演示彩排、问题清零并冻结版本 |

控制规则：

- 首次全链路联调不得晚于 Day 4。
- 首次前端完整演示不得晚于 Day 5。
- Day 5 未跑通时，立即停止页面装饰、额外算法和非关键接口优化。
- Day 6 后原则上不再接受接口破坏性变更。

## 9. 完成定义

### 9.1 单模块 Definition of Done

后端模块必须同时满足：

1. 可独立启动。
2. `GET /health` 返回统一成功响应。
3. `openapi.md` 中该模块全部接口已实现。
4. 正常路径字段和类型符合契约。
5. 至少两个模块级失败场景通过。
6. 写接口至少有一个幂等测试。
7. 响应包含并透传 `traceId`。
8. 创建后可查询，不使用全局固定业务 ID。
9. 测试命令通过。
10. Docker 镜像可构建和启动。
11. README 包含启动、测试和 curl 示例。
12. PR 包含验证证据。

最低测试要求：

```text
1 个健康检查测试
每个接口至少 1 个正常路径测试
整个模块至少 2 个失败路径测试
至少 1 个幂等测试
```

### 9.2 全链路 Definition of Done

在全新环境执行：

```bash
docker compose up --build
```

必须通过：

1. 前端和 8 个后端容器全部运行并通过健康检查。
2. 前端点击一次“开始演示”。
3. 网关真实调用各业务服务。
4. 返回的业务 ID 非空且相互关联。
5. 页面展示模型指标、存证交易和 Agent 报告。
6. 证据链包含采集、资产、授权、训练、聚合、模型和 Agent 事件。
7. `businessId` 状态查询成功。
8. 相同幂等键不会创建第二套业务数据。
9. 人为停止一个关键下游后，前端显示正确错误码和 `traceId`。
10. CI 和所有约定测试通过。

## 10. 协作与管理机制

### 10.1 每日节奏

- 上午 15 分钟：每人只汇报昨日可验证结果、今日交付和阻塞。
- 晚上 20 至 30 分钟：合并到 `develop`，执行健康检查、Compose 和主流程检查。
- 阻塞超过 2 小时必须进入 `Blocked` 并通知技术负责人。

看板状态：

```text
Backlog -> Ready -> In Progress -> In Review -> Integration -> Done
                                              \-> Blocked
```

`Done` 表示已经合并并通过验收；“代码写完但未联调”只能进入 `Integration`。

### 10.2 接口变更流程

```text
提出变更理由和调用方影响
-> 技术负责人审核
-> 先更新 openapi.md
-> 同步 module-contracts.md
-> 影响流程时更新 main-flow.md
-> 影响公共协议时更新 response-and-errors.md
-> 修改代码
-> 受影响模块重新联调
```

未经技术负责人批准，成员不得自行新增同义字段、错误码或状态。

### 10.3 PR 规则

- 一个 PR 聚焦一个模块或一个横向任务。
- PR 必须关联 Issue。
- PR 必须提供实际测试命令和结果。
- 接口变更必须明确文档同步情况。
- 涉及网关调用的模块必须说明联调状态。
- Day 4 前优先合并可联调的小 PR，不等待模块全部完成后提交大 PR。

## 11. 第一周遗漏项与处理

以下事项此前没有独立负责人或完整定义，纳入本周：

| 遗漏项 | 处理方式 | 负责人 |
|---|---|---|
| 公共包 | Day 1 冻结最小公共 API | 技术负责人 |
| 技术版本约束 | Python 3.11、Node.js 24 LTS；依赖锁定 | 技术负责人 |
| 服务端口和发现名称 | 使用本文端口表和 Compose 服务名 | privacy-compute |
| Dockerfile 模板 | 统一 Python 服务模板 | federated-learning + privacy-compute |
| Compose 和健康检查 | Day 1 建立、持续补齐 | privacy-compute |
| `.env.example` | 提供非敏感配置样例 | privacy-compute |
| CORS | 只允许前端经网关访问业务能力 | api-gateway |
| CI 过弱 | 增加测试、构建和契约校验 | api-gateway |
| 集成测试无人主责 | 纳入网关副职责 | api-gateway |
| E2E 无人主责 | 网关主责，前端和 Agent 协助 | api-gateway |
| 日志和追踪 | 结构化日志并贯穿 `traceId` | 技术负责人 + 全体后端 |
| HTTP 超时 | 网关下游默认 5 秒 | api-gateway |
| Readiness 与 healthiness | `/health` 表示可接收请求 | 全体后端 |
| UTF-8 显示兼容 | 文档和命令明确编码 | 技术负责人 |
| ID 前缀 | 由公共包统一生成 | 技术负责人 |
| Mock 可重复性 | 使用固定随机种子 | meter-simulator |
| 契约歧义 | Day 1 完成文档同步 | 技术负责人 |
| 版本标签 | Day 7 冻结 `week1-mock-v0.1.0` | 技术负责人 |

统一 ID 前缀：

```text
demo_
batch_
reading_
asset_
auth_
fl_task_
aggregate_
global_model_v
prediction_
strategy_
report_
evt_
tx_
trace_
```

## 12. 风险与降级策略

| 风险 | 预警信号 | 处理 |
|---|---|---|
| 接口字段各自变化 | 同一字段出现多个命名 | 暂停合并，由技术负责人冻结契约 |
| 网关成为瓶颈 | Day 3 下游客户端未完成 | 集成测试副职责人员协助客户端和夹具 |
| Compose 最后才开始 | Day 2 仍没有可解析配置 | 暂停 privacy 非关键功能，优先部署 |
| 前端经验不足 | Day 3 仍未完成静态页面 | 只保留单页和 Element Plus 标准组件 |
| 过早实现真实算法 | 出现数据库、链 SDK 或复杂训练框架 | 移出第一周 Issue |
| 模块只返回固定 JSON | 所有请求返回同一个 ID | 拒绝验收，要求内存状态和动态 ID |
| Windows 编码问题 | 中文文档或日志乱码 | 统一 UTF-8 并在 PowerShell 显式指定编码 |
| 大 PR 难以合并 | Day 4 才首次提交模块 | 拆分健康检查、正常路径、失败路径和部署 PR |

若 Day 5 尚未跑通，按以下顺序砍范围：

1. 取消非主页面和复杂图表。
2. 保留每个模块全部接口，但减少非主链路页面展示。
3. 取消额外动画和视觉装饰。
4. 保留一种隐私聚合模式进入主流程，其他模式仍完成独立接口测试。
5. 不削减统一响应、错误处理、健康检查、Compose 和主链路存证。

## 13. 第一周验收输出

Day 7 最终应形成：

- 可一键启动的 Compose 环境。
- 可操作的前端全链路演示。
- 8 个符合契约的 FastAPI 服务。
- 可复用的 Python 公共包。
- 完整 Mock 证据链。
- 模块测试、集成测试和前端构建结果。
- 每个模块的 README。
- 演示操作说明和失败恢复说明。
- 第一周完成清单、遗留问题和第二周真实能力替换顺序。

第二周优先替换顺序：

```text
模拟数据集和真实轻量 FedAvg
-> 真实源端哈希、签名与验签
-> 持久化存储
-> 哈希链或联盟链
-> 参数安全聚合增强
-> Agent 真实模型调用
```
