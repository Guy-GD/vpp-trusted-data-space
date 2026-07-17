# Newcomer Collaboration Guide Implementation Plan

> **文档职责**：本计划记录新人协作手册的写作范围、执行步骤与验证方法，供维护者追溯本次文档交付。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide a Windows-first Chinese guide that lets a new project member understand the system and complete a safe GitHub contribution.

**Architecture:** Create one user-facing Markdown guide in the workspace root. It will use the repository's README and four design/API documents as the source of truth, and will not invent an unchosen runtime stack or unavailable startup commands.

**Tech Stack:** Markdown, Git, GitHub, PowerShell on Windows.

## Global Constraints

- Write in Chinese and target first-time project members.
- Use only documented module boundaries, API paths, response rules, and branch rules.
- State clearly where the repository has not yet selected an implementation stack.
- Do not place secrets, tokens, or real credentials in examples.

---

### Task 1: Create the newcomer guide

**Files:**
- Create: `C:/Users/David/Desktop/jiebangguashuai/项目开发协作说明书.md`

**Interfaces:**
- Consumes: `README.md`, `docs/design/main-flow.md`, `docs/design/module-contracts.md`, `docs/api/openapi.md`, and `docs/api/response-and-errors.md`.
- Produces: A standalone onboarding and collaboration guide.

- [ ] **Step 1: Write the guide outline**

Include project overview, the nine deliverable modules, a plain-language end-to-end flow, one-time Windows setup, GitHub workflow, module development rules, integration, review, and troubleshooting.

- [ ] **Step 2: Add PowerShell Git commands**

Use the repository's documented branches: `main`, `develop`, and `feature/*`. Include clone, branch, status, add, commit, push, pull, and conflict-resolution commands.

- [ ] **Step 3: Add documented system contracts**

Point new members to the four source documents. Explain the unified response envelope, `GET /health`, `X-Trace-Id`, `Idempotency-Key`, and API-change workflow without duplicating every endpoint schema.

- [ ] **Step 4: Self-review the document**

Check that all local links resolve, no `TODO`/`TBD` placeholders remain, and all references match the repository documents.

### Task 2: Verify the written artifact

**Files:**
- Test: `C:/Users/David/Desktop/jiebangguashuai/项目开发协作说明书.md`

**Interfaces:**
- Consumes: The completed guide.
- Produces: Evidence that required sections and no placeholder markers are present.

- [ ] **Step 1: Check required headings**

Run PowerShell `Select-String` for project overview, workflow, GitHub, module, integration, and troubleshooting headings.

- [ ] **Step 2: Check placeholders**

Run PowerShell `Select-String` for `TODO` and `TBD`; expected result is no matches.

- [ ] **Step 3: Review the final file path and content**

Confirm the guide is in the exact workspace-root path requested by the user.
