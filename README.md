# vpp-trusted-data-space

面向虚拟电厂跨主体交易的可信数据空间协同计算与审计平台。

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
