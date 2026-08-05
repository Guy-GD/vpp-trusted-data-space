# Development Issue and PR Templates Implementation Plan

> **文档职责**：本计划定义开发功能 Issue 与 Pull Request 模板的更新步骤和验证方式。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the minimal GitHub templates with a single development-task Issue template and an interface-contract-aware PR template.

**Architecture:** Keep the current two GitHub template file locations. The Issue template will specify one bounded development task, while the PR template will prove that the task's module, API contract, verification, integration, and security obligations have been addressed.

**Tech Stack:** GitHub Issue forms in Markdown front matter, GitHub Pull Request Markdown templates.

## Global Constraints

- Templates serve feature-development work only.
- Preserve the existing `.github/ISSUE_TEMPLATE/task.md` and `.github/pull_request_template.md` file locations.
- Do not require unselected application frameworks, databases, or test commands.
- Require interface-document synchronization only when API paths, methods, fields, enums, states, or error codes change.
- Backend work must report health-check and unified-response verification; frontend work must report gateway-only backend access.

---

### Task 1: Replace the development Issue template

**Files:**
- Modify: `.github/ISSUE_TEMPLATE/task.md`
- Test: `.github/ISSUE_TEMPLATE/task.md`

**Interfaces:**
- Consumes: `docs/design/module-contracts.md`, `docs/api/openapi.md`, and `docs/api/response-and-errors.md`.
- Produces: A Markdown Issue form for a bounded development task with priority, module, dependency, contract, implementation requirements, and acceptance checks.

- [ ] **Step 1: Write the failing structural check**

Run:

```powershell
$required = @('优先级','所属模块','依赖或阻塞','任务目标','不在本任务范围','接口契约','实现要求','验收清单','交付物')
$required | Where-Object { -not (Select-String -LiteralPath '.github/ISSUE_TEMPLATE/task.md' -SimpleMatch $_ -Quiet) }
```

Expected before the change: missing required sections are printed.

- [ ] **Step 2: Replace the template content**

Use checkboxes for priority, affected API, backend/frontend obligations, and acceptance evidence. Keep YAML front matter with `name`, `description`, `title`, `labels`, and `assignees` so GitHub recognizes the template.

- [ ] **Step 3: Run the structural check**

Run the command from Step 1.

Expected after the change: no output and exit code `0`.

### Task 2: Replace the Pull Request template

**Files:**
- Modify: `.github/pull_request_template.md`
- Test: `.github/pull_request_template.md`

**Interfaces:**
- Consumes: `.github/ISSUE_TEMPLATE/task.md` and the four project design/API documents.
- Produces: A PR description that records issue linkage, interface impact, contract synchronization, validation evidence, integration status, and risk.

- [ ] **Step 1: Write the failing structural check**

Run:

```powershell
$required = @('关联 Issue','模块与改动摘要','接口影响','契约文档同步','验证证据','联调与部署影响','数据安全与隐私检查','风险与回滚')
$required | Where-Object { -not (Select-String -LiteralPath '.github/pull_request_template.md' -SimpleMatch $_ -Quiet) }
```

Expected before the change: missing required sections are printed.

- [ ] **Step 2: Replace the template content**

Require an explicit choice for API impact and documentation synchronization, and include conditional checks for backend health checks, frontend gateway-only calls, integration status, and sensitive-data review.

- [ ] **Step 3: Run the structural check**

Run the command from Step 1.

Expected after the change: no output and exit code `0`.

### Task 3: Verify both templates together

**Files:**
- Test: `.github/ISSUE_TEMPLATE/task.md`
- Test: `.github/pull_request_template.md`

**Interfaces:**
- Consumes: The two updated GitHub templates.
- Produces: Evidence that the templates have valid GitHub front matter, all required sections, and no unintentional placeholders.

- [ ] **Step 1: Check Issue front matter and all required sections**

Run:

```powershell
$issue = Get-Content -Raw -Encoding utf8 '.github/ISSUE_TEMPLATE/task.md'
if (-not $issue.StartsWith('---')) { throw 'Issue template has no YAML front matter' }
if ($issue -notmatch '(?m)^name: Task$') { throw 'Issue template name is invalid' }
if ($issue -notmatch '(?m)^title: "\[P0\]\[模块名\] 任务名称"$') { throw 'Issue title format is missing' }
```

Expected: exit code `0`.

- [ ] **Step 2: Check PR linkage and contract sections**

Run:

```powershell
$pr = Get-Content -Raw -Encoding utf8 '.github/pull_request_template.md'
if ($pr -notmatch 'Closes #') { throw 'PR template lacks Issue linkage' }
if ($pr -notmatch '无接口变更') { throw 'PR template lacks explicit no-API-change option' }
if ($pr -notmatch 'GET /health') { throw 'PR template lacks backend health-check evidence' }
```

Expected: exit code `0`.

- [ ] **Step 3: Commit**

```powershell
git add .github/ISSUE_TEMPLATE/task.md .github/pull_request_template.md docs/superpowers/specs/2026-07-11-development-issue-pr-templates-design.md docs/superpowers/plans/2026-07-11-development-issue-pr-templates.md
git commit -m "docs: improve development issue and PR templates"
```

Expected: Git records the template update in one documentation commit.
