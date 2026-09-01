# Sanitized Week-One Issues Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate 10 complete local week-one task books and publish 10 sanitized GitHub Issues without disclosing interfaces, architecture, error codes, or file-level implementation details.

**Architecture:** The approved owner packet remains the source for private task books. Each task section is copied into the responsible module's local `WEEK1-TASK.md`, while independently authored sanitized Issue bodies expose only role, target day, generic deliverable types, team gates, and close conditions. Local Git exclude rules prevent accidental staging, and publication is gated by a deny-list scan plus post-write GitHub API verification.

**Tech Stack:** Markdown, Git local exclude rules, PowerShell read-only verification, GitHub CLI or GitHub REST API for Issue creation.

## Global Constraints

- Target repository is exactly `Guy-GD/vpp-trusted-data-space`.
- Publish exactly 10 sanitized Issues and do not create labels, milestones, Projects, assignees, or permission changes.
- Public Issue bodies must not contain API paths, HTTP methods, request/response fields, error codes, architecture relationships, internal document links, source-file lists, or detailed implementation steps.
- Generate exactly 10 local `WEEK1-TASK.md` files containing the full reviewed owner packets.
- Do not stage, commit, push, or otherwise publish any `WEEK1-TASK.md`.
- Protect all local task books through `.git/info/exclude`, without changing the shared `.gitignore`.
- Reuse an existing same-title Issue only when it contains the exact hidden marker `codex-week1-sanitized-task:N`; stop on an unmarked title conflict.
- Do not persist GitHub tokens in repository files, task books, plan files, or result files.

---

## File Structure

- `packages/common/WEEK1-TASK.md`: technical lead contract and common-package task book.
- `services/meter-simulator/WEEK1-TASK.md`: trusted collection Mock task book.
- `services/data-ingestion/WEEK1-TASK.md`: ingestion verification and asset Mock task book.
- `services/identity-did/WEEK1-TASK.md`: DID and authorization Mock task book.
- `services/federated-learning/WEEK1-TASK.md`: training rounds and model registry Mock task book.
- `services/privacy-compute/WEEK1-TASK.md`: privacy Mock and Compose task book.
- `services/ledger-service/WEEK1-TASK.md`: in-memory evidence-chain task book.
- `services/ai-agent/WEEK1-TASK.md`: prediction, strategy, and audit task book.
- `services/api-gateway/WEEK1-TASK.md`: orchestration, integration, CI, and E2E task book.
- `apps/web-dashboard/WEEK1-TASK.md`: beginner-friendly Vue console task book.
- `.git/info/exclude`: local-only protection for the 10 task books.
- No tracked file is modified by the task-book generation stage.

### Task 1: Generate and protect the 10 local task books

**Files:**

- Create: `packages/common/WEEK1-TASK.md`
- Create: `services/meter-simulator/WEEK1-TASK.md`
- Create: `services/data-ingestion/WEEK1-TASK.md`
- Create: `services/identity-did/WEEK1-TASK.md`
- Create: `services/federated-learning/WEEK1-TASK.md`
- Create: `services/privacy-compute/WEEK1-TASK.md`
- Create: `services/ledger-service/WEEK1-TASK.md`
- Create: `services/ai-agent/WEEK1-TASK.md`
- Create: `services/api-gateway/WEEK1-TASK.md`
- Create: `apps/web-dashboard/WEEK1-TASK.md`
- Modify locally only: `.git/info/exclude`
- Source: `docs/superpowers/plans/2026-07-16-week-one-owner-issue-packets.md`

**Interfaces:**

- Consumes: the 10 ordered `### Task N:` sections from the reviewed owner packet.
- Produces: one self-contained Markdown task book per owner, with a common confidentiality header and the complete corresponding source section.

- [ ] **Step 1: Write each task book with a confidentiality header**

Each file must begin with:

```markdown
# 第一周模块任务书

> 分发范围：对应模块负责人、技术负责人。
>
> 本文件包含详细接口、架构依赖和实施计划。本次仅生成在本地，不提交、不推送；由技术负责人线下私发。

## 使用说明

- 公开 GitHub Issue 只用于进度跟踪，本文件是详细执行依据。
- 接口冲突时，以仓库中的正式契约文档为准，并先通知技术负责人。
- 未经技术负责人确认，不得扩大第一周 Mock 范围或引入真实基础设施。

---
```

Append the complete matching `### Task N:` section without shortening its interface list, file list, implementation steps, or acceptance criteria.

- [ ] **Step 2: Add local Git exclude protection**

Append these exact lines to `.git/info/exclude`, omitting duplicates:

```text
/packages/common/WEEK1-TASK.md
/services/meter-simulator/WEEK1-TASK.md
/services/data-ingestion/WEEK1-TASK.md
/services/identity-did/WEEK1-TASK.md
/services/federated-learning/WEEK1-TASK.md
/services/privacy-compute/WEEK1-TASK.md
/services/ledger-service/WEEK1-TASK.md
/services/ai-agent/WEEK1-TASK.md
/services/api-gateway/WEEK1-TASK.md
/apps/web-dashboard/WEEK1-TASK.md
```

- [ ] **Step 3: Verify task-book count and completeness**

Run:

```powershell
$paths = @(
  'packages/common/WEEK1-TASK.md',
  'services/meter-simulator/WEEK1-TASK.md',
  'services/data-ingestion/WEEK1-TASK.md',
  'services/identity-did/WEEK1-TASK.md',
  'services/federated-learning/WEEK1-TASK.md',
  'services/privacy-compute/WEEK1-TASK.md',
  'services/ledger-service/WEEK1-TASK.md',
  'services/ai-agent/WEEK1-TASK.md',
  'services/api-gateway/WEEK1-TASK.md',
  'apps/web-dashboard/WEEK1-TASK.md'
)
$missing = @($paths | Where-Object { -not (Test-Path -LiteralPath $_) })
$empty = @($paths | Where-Object { (Get-Item -LiteralPath $_).Length -lt 1000 })
$markers = @($paths | Where-Object {
  (Get-Content -LiteralPath $_ -Raw -Encoding UTF8) -notmatch '### Task \d+:'
})
[pscustomobject]@{
  Count = @($paths | Where-Object { Test-Path -LiteralPath $_ }).Count
  Missing = $missing.Count
  TooShort = $empty.Count
  MissingTaskMarker = $markers.Count
}
```

Expected:

```text
Count             : 10
Missing           : 0
TooShort          : 0
MissingTaskMarker : 0
```

- [ ] **Step 4: Verify Git cannot see or stage the task books**

Run:

```powershell
$git = 'C:\Program Files\Git\cmd\git.exe'
$paths | ForEach-Object { & $git check-ignore -q -- $_; "$_=$($LASTEXITCODE -eq 0)" }
& $git status --short
```

Expected: all 10 values are `True`, and no `WEEK1-TASK.md` appears in Git status.

### Task 2: Build and scan the 10 sanitized Issue bodies

**Files:**

- No repository file is created or modified.
- Issue bodies are constructed in memory from fixed sanitized templates.

**Interfaces:**

- Consumes: approved titles, owner roles, target days, module directory names, generic deliverable categories, team gates, and close conditions.
- Produces: 10 Markdown strings carrying `<!-- codex-week1-sanitized-task:N -->`.

- [ ] **Step 1: Construct the fixed public metadata**

Use these exact title and target mappings:

```text
1  [P0][公共] 冻结契约并实现 vpp_common 公共包
   技术负责人 | Day 1 中午冻结；Day 7 主持验收 | packages/common
2  [P0][源端采集] 实现 meter-simulator 动态 Mock 批次
   meter-simulator 负责人 | Day 3 | services/meter-simulator
3  [P0][数据接入] 实现 data-ingestion 验签验哈希与资产登记 Mock
   data-ingestion 负责人 | Day 3 | services/data-ingestion
4  [P0][DID] 实现主体设备 DID 与授权状态流转 Mock
   identity-did 负责人 | Day 3 | services/identity-did
5  [P0][联邦学习] 实现三轮训练状态与模型版本 Mock
   federated-learning 负责人 | Day 3 | services/federated-learning
6  [P0][隐私计算][部署] 实现安全聚合 Mock 与九服务 Compose
   privacy-compute 负责人 | 隐私模块 Day 3；Compose Day 4 | services/privacy-compute
7  [P0][存证] 实现事件存证与 businessId 证据链 Mock
   ledger-service 负责人 | Day 3 | services/ledger-service
8  [P0][Agent] 实现预测、交易策略与审计报告 Mock
   ai-agent 负责人 | Day 3 | services/ai-agent
9  [P0][网关][测试] 实现全链路编排、状态、CI 与 E2E
   api-gateway 负责人 | 网关 Day 4；CI/E2E Day 6 | services/api-gateway
10 [P0][前端] 实现 Vue 一键全链路 Mock 演示页
   web-dashboard 负责人 | Day 5 | apps/web-dashboard
```

- [ ] **Step 2: Use the approved sanitized Issue layout**

Each body must contain:

```markdown
<!-- codex-week1-sanitized-task:N -->

## 任务目标

[One generic sentence describing the module's week-one Mock outcome.]

## 负责人和时间

- **负责人角色**：[role]
- **目标完成**：[target]
- **模块目录**：`[directory]`
- **详细任务书**：由技术负责人线下发放；本 Issue 不包含内部接口、架构和实施细节。

## Day 1～Day 7 团队门禁

- [ ] **Day 1**：工程可启动，健康检查和基础契约准备完成。
- [ ] **Day 2**：正常路径完成并可独立演示。
- [ ] **Day 3**：失败路径、状态、动态 ID、幂等和模块测试完成。
- [ ] **Day 4**：后端 HTTP 链路与容器编排完成联调。
- [ ] **Day 5**：前端首次完成全链路演示。
- [ ] **Day 6**：CI、E2E、异常演练和运行文档完成。
- [ ] **Day 7**：全新环境验收、演示彩排和版本冻结完成。

## 本模块公开交付物

[A short list limited to service/page/container/test/document deliverable categories.]

## 关闭条件

- [ ] 模块能够按约定方式启动，并提供可重复的 Mock 演示。
- [ ] 正常路径、失败路径和模块级自动化检查通过。
- [ ] 已提交关联 PR，并附测试、截图或日志证据。
- [ ] 未引入未批准的范围扩张、真实凭据或破坏性契约变更。
- [ ] 跨模块阻塞已及时通知技术负责人。
```

- [ ] **Step 3: Run the deny-list scan before publication**

For every Issue body, reject publication when it matches any of:

```regex
/(api|health|v1|v2)/|GET\s|POST\s|PUT\s|PATCH\s|DELETE\s
request|response|payload|schema|errorCode|traceId
docs/api/|docs/design/|WEEK1-TASK\.md
main\.py|routes?\.py|models?\.py|clients?\.py|tests?/
AES|SHA-?256|FedAvg|MPC|DID:
```

The module directory itself is permitted only in the dedicated `模块目录` line. All other source-file paths are forbidden.

- [ ] **Step 4: Verify public-body structure**

Expected for every body:

```text
hidden marker count = 1
Day headings present = 7
close-condition checkboxes = 5
deny-list matches = 0
detailed-task-book link count = 0
```

### Task 3: Publish and verify the 10 sanitized GitHub Issues

**Files:**

- No local repository file is modified.
- External target: GitHub Issues in `Guy-GD/vpp-trusted-data-space`.

**Interfaces:**

- Consumes: the 10 scanned sanitized Issue bodies from Task 2.
- Produces: 10 GitHub Issue URLs and a fresh read-back verification result.

- [ ] **Step 1: Authenticate interactively without persisting a project token**

Use GitHub's official browser/device authorization. Request only the access needed to create Issues in the public target repository. Keep the resulting token in process memory and clear it after publication.

- [ ] **Step 2: Read existing Issues and enforce title-conflict rules**

Fetch all Issues, excluding pull requests.

For each target title:

- create when no same-title Issue exists;
- update only when the same-title Issue body contains the exact matching sanitized marker;
- stop before any write when a same-title Issue exists without the marker.

- [ ] **Step 3: Create or update in dependency order**

Use this order:

```text
Task 1
Tasks 2 through 8
Task 9
Task 10
```

Do not add assignees, labels, milestones, Projects, dependency graphs, comments, or attachments.

- [ ] **Step 4: Read back every Issue**

Verify:

```text
repository = Guy-GD/vpp-trusted-data-space
issue count = 10
all titles exactly match approved titles
all hidden markers exactly match task numbers
all bodies include Day 1 through Day 7
all bodies include target day and five close conditions
all bodies pass the same deny-list scan
no assignees, labels, or milestones were added by this operation
```

- [ ] **Step 5: Report the publication result**

Return a compact table containing Issue number, title, target day, action (`created` or `updated`), and URL. Separately list the 10 local task-book paths and state that Git reports them ignored and untracked.
