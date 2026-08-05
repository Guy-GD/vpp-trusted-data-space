# Final Fix Wave: 全分支审查发现闭环

## 目标

一次性修复最终全分支审查中所有影响当前核心交付的 Critical/Important，以及与这些问题直接相关、成本较低的 Minor。保持第一周 Mock 范围，不实现任何业务模块。

## 1. 保留标准 HTTPException 语义

当前统一处理器会把未映射 HTTP 状态（例如 405）改为 500，并丢弃 `Allow`、`WWW-Authenticate`、`Retry-After`。

要求：

- 显式冻结所有 HTTPException 的策略：保留原 HTTP 状态；已知状态映射到最接近的冻结业务错误码；其他 4xx 使用 `40001`，其他 5xx 使用 `50001`，不得把 405 改成 500。
- `_json_error` 支持显式 HTTP status override。
- 只按不区分大小写的白名单透传协议头：`Allow`、`WWW-Authenticate`、`Retry-After`；不得透传 Cookie、内部调试头或任意自定义头。
- 增加真实 HTTP 401、405、429 回归测试：统一包络、原 HTTP status、冻结业务码、响应体/头 traceId 一致、允许的标准头保留、异常 detail 不泄漏。

## 2. 锁死稳定 message

- `success()` 的 message 固定为 `ok`，移除公开覆盖参数。
- `failure()` 始终使用 `ERROR_MESSAGES[code]`，移除公开覆盖参数。
- `ServiceError` 不接受公开 message 覆盖，也不得把内部异常文本返回客户端。
- 更新测试和 README 示例，确保所有业务错误码对应唯一稳定 message。

## 3. 统一响应实际键集合

- 删除 `docs/api/response-and-errors.md` 中公共模型不支持的 `requestId`。
- 成功响应经真实 FastAPI 序列化后，键集合必须精确为 `code`、`message`、`data`、`traceId`、`timestamp`；不得含 `details`。
- 失败响应始终包含 `code`、`message`、`data: null`、`traceId`、`timestamp`，只有存在字段详情时才包含 `details`。
- 可以使用稳定的 Pydantic v2 序列化机制或拆分内部模型，但必须保留冻结的公开导出 `ApiResponse` 与 `success`/`failure`。
- 增加真实 HTTP JSON 精确键集合测试。

## 4. 冻结多轮 FL 的唯一交接

采用以下唯一方案并同步 `main-flow.md`、`openapi.md`、`module-contracts.md`：

- `POST .../start` 返回第 1 轮 `currentRound` 和 `updates[]`。
- 每轮网关调用 privacy secure-aggregate，再调用 FL aggregate。
- 非最终轮 FL aggregate 响应包含 `status: running`、`nextRound`（整数）和下一轮完整 `updates[]`；最终轮包含 `status: completed`、`nextRound: null`、`updates: []`，并返回最终 `globalModelVersion`、`modelHash`、`metrics`。
- `POST .../rounds/{roundId}/updates` 请求体只包含 `participantDid`、`sampleCount`、`modelUpdateUri`、`updateHash`；`taskId`、`roundId` 只来自路径，禁止在请求体重复。
- FL aggregate 请求体只包含 `aggregateId`、`aggregateResultUri`、`aggregateHash`；`taskId`、`roundId` 只来自路径。
- 契约测试解析 JSON 并验证首轮、非最终轮/最终轮交接以及路径 ID 不在请求体。

## 5. 扩充契约测试与 OpenAPI 完整度

- 覆盖矩阵中的每个业务端点必须存在唯一正文 H3 章节，矩阵与正文双向精确匹配；`GET /health` 可由公共健康章节统一描述。
- 每个端点正文至少明确：请求来源/Schema（无 body 时明确“无请求体”）、字段类型、必填性、成功 `data` 结构或可解析 JSON 示例、可能错误、幂等规则（查询接口明确“不适用”）。
- 可用集中 Schema 表减少重复，但每个 endpoint 必须明确引用；实现者不能再猜字段类型或可选性。
- 为全部现有接口补齐上述信息，不增加接口、不改变第一周 Mock 范围。
- 错误只引用公共错误目录，不复制新错误码目录。
- 契约测试至少验证每个矩阵端点有正文、有请求说明、有成功说明、有错误说明、有幂等说明，并对关键 FL/Agent/demo JSON 做结构解析。

## 6. 收紧公共包模块职责文档

将 `module-contracts.md` 公共包章节限制为：统一响应、错误码、traceId、UTC 时间、冻结 ID、`HealthData`/`ErrorDetail`。明确模块专属 DTO、哈希、签名、加密及业务工具不属于公共包；哈希/签名归源端采集或相应业务模块。

## 7. UTF-8 与设计状态

- 清除 `docs/design/module-contracts.md` 的 UTF-8 BOM，并检查本次修改的正式 Markdown/Python/TOML 文件均可严格按 UTF-8 解码。
- 新增 `.gitattributes`，为文本文件冻结 LF（例如 `* text=auto eol=lf`，必要的二进制扩展标为 binary）。
- 将 `week-one-mock-delivery.md` 的“当前歧义”改为“已冻结决策/完成状态”，明确 `traceId` 只在公共响应包络。
- 既有已跟踪 `docs/superpowers` 文件不在本波删除范围；如需处理，只修正 `.gitignore` 注释使其不再声称已跟踪文件绝不发布，不得删除用户文件。

## 约束

- 不实现业务服务、数据库、区块链、真实算法、Compose 或前端。
- 不引入模块 DTO 到公共包。
- 不修改 34 个错误码数值、稳定 message 或 14 个 ID 前缀。
- 不泄漏内部异常详情、凭据或敏感数据。
- 你不是唯一工作者；不要回滚现有提交或删除用户文件。

## TDD 与验证

先为每个代码/契约缺口补充会失败的测试并记录 RED，再实现到 GREEN。使用：

```powershell
$python = 'C:\Users\David\AppData\Local\Temp\vpp-python311\python.exe'
$deps = 'C:\Users\David\AppData\Local\Temp\vpp-test-deps311'
$src = Join-Path (Get-Location) 'packages/common/src'
$env:PYTHONPATH = "$deps;$src"
& $python -m pytest packages/common/tests -q
& $python -m pytest tests/integration/test_contract_docs.py -q -p no:cacheprovider
```

还必须运行 `git diff --check`、UTF-8 严格解码检查，并确认 `git status` 不包含临时依赖、报告或缓存。

创建一个修复提交，报告写入 `.superpowers/sdd/final-fix-report.md`，包含完整 RED/GREEN、文件列表、自审及未处理项。
