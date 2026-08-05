# vpp-trusted-data-space

面向虚拟电厂跨主体交易的可信数据空间协同计算与审计平台。

## 第一周技术基线（已冻结）

后端统一采用 Python 3.11、FastAPI、Pydantic v2、Uvicorn、httpx 和 pytest；服务间协议固定为 HTTP/1.1 + JSON。公共依赖范围为 FastAPI `>=0.115,<1`、Pydantic `>=2,<3`、httpx `>=0.28,<1`、pytest `>=8,<9`，各模块必须在自己的依赖文件中锁定直接依赖，不得自行替换后端框架。

前端统一采用 Node.js 24 LTS、Vue 3、Vite、JavaScript、Element Plus 和 Axios；第一周不引入 TypeScript、Pinia 或 Nuxt。`.python-version` 和 `.nvmrc` 是本地运行时基线。

所有源码、配置、文档和测试文件统一使用 UTF-8、LF 换行。Windows PowerShell 读取中文文档时必须显式指定编码，例如：

```powershell
Get-Content -Encoding UTF8 README.md
```

模块对外通信只使用 `docs/api/openapi.md` 中的 HTTP 接口；统一响应、错误码、`traceId` 与 ID 前缀以 `docs/api/response-and-errors.md` 和 `packages/common` 为准。

## 公共包

使用 Python 3.11 在仓库根目录安装：

```powershell
python -m pip install -e "packages/common[test]"
python -m pytest packages/common/tests tests/integration/test_contract_docs.py -v
```

八个后端必须安装 `vpp-common==0.1.0` 的仓库内版本，不得在各模块复制响应、错误码、追踪或 ID 生成逻辑。模块专属 DTO 继续保留在各模块内部。

## 项目主线

源端可信采集 + 联邦学习 + 同态加密/MPC 安全聚合 + 区块链审计 + Agent 交易决策。

## 目录结构

- `apps/web-dashboard`: 前端可视化平台
- `services/api-gateway`: 统一 API 网关
- `services/meter-simulator`: 智能电表与采集终端模拟
- `services/identity-did`: DID 主体身份与授权
- `services/data-ingestion`: 数据接入与目录管理
- `services/federated-learning`: 联邦学习训练与聚合
- `services/privacy-compute`: 同态加密、MPC、安全聚合
- `services/ledger-service`: 区块链存证与审计追溯
- `services/ai-agent`: 预测、交易策略、审计报告 Agent
- `datasets/synthetic-vpp`: 虚拟电厂模拟数据集
- `infra`: Docker、Nginx 与部署配置
- `docs`: 设计、接口、部署、报告文档
- `tests`: 集成测试与端到端测试
- `demo`: 演示脚本与视频脚本

## 协作规则

- `main`: 稳定演示版本
- `develop`: 日常集成分支
- `feature/*`: 个人功能分支
- 所有任务进入 GitHub Issues
- 所有代码通过 Pull Request 合并
