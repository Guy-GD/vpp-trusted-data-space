# 第一周脱敏 Issue 与本地任务书交付设计

## 1. 目标

为第一周 10 个负责人任务包建立两层交付：

1. 在公开仓库 `Guy-GD/vpp-trusted-data-space` 创建 10 条脱敏 GitHub Issues，用于团队进度跟踪。
2. 在本地各模块目录生成 `WEEK1-TASK.md`，保存完整架构、接口、实施步骤和验收标准，供技术负责人线下私发或自行决定是否推送。

本设计只处理任务分发与进度跟踪，不改变已经冻结的系统架构、接口契约或第一周 Mock 范围。

## 2. 信息边界

### 2.1 GitHub Issue 可以公开的内容

每条 Issue 仅包含：

- 模块名称与任务标题；
- 负责人角色，不包含个人姓名、邮箱或账号；
- 目标完成日；
- 通用交付物类型；
- Day 1～Day 7 团队门禁；
- 通用关闭条件；
- “详细任务书由技术负责人线下发放”的说明；
- 不含敏感信息的模块目录名称。

### 2.2 GitHub Issue 禁止公开的内容

Issue 不包含：

- 具体 API 路径、请求参数、响应结构和错误码；
- 系统架构关系、内部调用顺序和状态机；
- 文件级实现步骤、算法或安全机制细节；
- 完整验收用例、测试数据和 Mock 数据结构；
- 密钥、凭据、成员身份或其他访问控制信息；
- 本地详细任务书的可点击链接。

### 2.3 本地详细任务书

`WEEK1-TASK.md` 可以包含已审核任务包中的完整内容：

- 模块职责与边界；
- 依赖关系；
- 文件范围；
- 完整接口清单；
- Day 1～Day 7 实施步骤；
- 正常、失败、幂等和集成验收标准；
- 与公共契约、网关、Compose 和前端的联调要求。

这些文件只生成在本地工作区。本次工作不执行 `git add`、commit、push 或其他外部发布操作。

## 3. 任务书映射

| Task | 负责人角色 | 本地详细任务书 |
|---|---|---|
| 1 | 技术负责人 | `packages/common/WEEK1-TASK.md` |
| 2 | meter-simulator 负责人 | `services/meter-simulator/WEEK1-TASK.md` |
| 3 | data-ingestion 负责人 | `services/data-ingestion/WEEK1-TASK.md` |
| 4 | identity-did 负责人 | `services/identity-did/WEEK1-TASK.md` |
| 5 | federated-learning 负责人 | `services/federated-learning/WEEK1-TASK.md` |
| 6 | privacy-compute / Compose 负责人 | `services/privacy-compute/WEEK1-TASK.md` |
| 7 | ledger-service 负责人 | `services/ledger-service/WEEK1-TASK.md` |
| 8 | ai-agent 负责人 | `services/ai-agent/WEEK1-TASK.md` |
| 9 | api-gateway / 集成测试负责人 | `services/api-gateway/WEEK1-TASK.md` |
| 10 | web-dashboard 负责人 | `apps/web-dashboard/WEEK1-TASK.md` |

Task 6 的 Compose 细节保存在 privacy-compute 任务书中，并明确其工作目录还包括 `infra/docker-compose/`。Task 9 的 CI 与 E2E 细节保存在 api-gateway 任务书中，并明确其工作目录还包括 `.github/workflows/`、`tests/integration/` 和 `tests/e2e/`。

## 4. 脱敏 Issue 结构

每条公开 Issue 使用相同结构：

```markdown
## 任务目标

一句话描述该模块第一周要完成的 Mock 能力，不暴露接口或架构细节。

## 负责人和时间

- 负责人角色
- 目标完成日
- 模块目录
- 详细任务书由技术负责人线下发放

## 第一周通用推进门禁

- Day 1：工程可启动、健康检查与基础契约准备完成
- Day 2：正常路径完成
- Day 3：失败路径、状态、动态 ID、幂等和模块测试完成
- Day 4：后端 HTTP 链路与 Compose 联调
- Day 5：前端首次完整演示
- Day 6：CI、E2E、异常演练和运行文档
- Day 7：全新环境验收、彩排和版本冻结

## 本模块公开交付物

只描述服务、测试、容器、页面或文档等交付物类型。

## 关闭条件

只使用不泄露实现细节的通用验收条件。
```

Issue 不分配 assignee，因为目前没有提供 9 位成员对应的 GitHub 用户名；创建后由技术负责人手动分配。

## 5. 创建与重复处理

公开 Issue 标题沿用已审核的 10 个中文标题。

- 若不存在同标题 Issue，则创建新 Issue。
- 若存在带 `codex-week1-sanitized-task:N` 隐藏标记的同标题 Issue，则更新复用。
- 若存在没有该标记的同标题 Issue，则停止，不覆盖他人内容。
- 不新建标签、里程碑、Project 或成员权限。

Issue 按依赖顺序创建：公共任务优先，随后 7 个业务模块，再创建网关/测试任务，最后创建前端任务。公开正文不写具体依赖图，仅写“跨模块阻塞及时通知技术负责人”。

## 6. 安全措施

- 本地 `WEEK1-TASK.md` 在生成后加入 `.git/info/exclude`，避免普通 `git add .` 意外暂存。
- 不修改仓库共享 `.gitignore`，避免产生需要推送的额外仓库变更。
- 发布前对 10 条 Issue 正文执行敏感词扫描，至少检查 API 路径、HTTP 方法、请求/响应字段、错误码、架构节点、内部文档路径和代码文件路径。
- 本地任务书生成后检查数量为 10、目标路径正确、无空任务包、无 `TODO`/`TBD`。
- GitHub 发布后重新读取全部 10 条 Issue，核验标题、脱敏标记、Day 1～Day 7、目标日和关闭条件。

## 7. 验收标准

设计实施完成时必须满足：

1. 10 个目标模块目录各有一份完整 `WEEK1-TASK.md`。
2. 任务书内容来自已审核的 10 个负责人任务包，没有丢失接口、步骤或验收标准。
3. 10 份任务书均未被 Git 跟踪或暂存，并受本地 exclude 保护。
4. GitHub 上恰有 10 条本次创建或更新的脱敏 Issue。
5. 每条 Issue 都包含负责人角色、目标日、Day 1～Day 7 门禁、公开交付物和关闭条件。
6. 每条 Issue 都不包含具体接口、架构、数据结构、错误码、实施文件清单或本地任务书链接。
7. 不修改成员权限，不创建标签、里程碑或 Project，不推送本地详细任务书。

## 8. 后续使用

技术负责人可以直接把对应的 `WEEK1-TASK.md` 私发给负责人。若后续仓库改为私有并决定提交这些文件，应先重新评估访问成员和保密范围，再显式移除 `.git/info/exclude` 中对应条目并单独提交。
