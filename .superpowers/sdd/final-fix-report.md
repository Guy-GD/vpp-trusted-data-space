# Final Fix Wave 实施报告

## 状态

- 结果：完成，已创建最终单提交。
- 起始 HEAD：`58d1501a2640a39701929a181046ef3a49124947`。
- 分支：`feature/github-templates`，普通工作区（`.git` 等于 common git dir）。
- 架构歧义：无；未报告 `NEEDS_CONTEXT`。
- 范围：仅公共包、正式契约文档、契约/公共包测试、`.gitattributes` 与 `.gitignore` 注释；未触碰 Compose、服务实现、前端或业务模块。

## 逐项实现

### 1. 标准 HTTPException 语义

- `_json_error` 新增显式 `status_code` override 与响应头输入。
- HTTPException 保留原 HTTP status；冻结映射覆盖 400/401/403/404/409/422/429/500/502/503/504，其他 4xx 映射 `40001`，其他状态回退 `50001`，其中其他 5xx 明确由回退覆盖。
- 协议头按不区分大小写的白名单过滤并规范输出：`Allow`、`WWW-Authenticate`、`Retry-After`。
- Cookie、内部调试头和任意自定义头不透传；异常 `detail` 不进入包络。
- 真实 HTTP 回归覆盖 401、路由生成的 405、429，以及已知/未知 4xx/5xx 状态。

### 2. 稳定 message

- `success()` 移除公开 message 参数并固定 `ok`。
- `failure()` 移除公开 message 参数并只使用 `ERROR_MESSAGES[code]`。
- `ServiceError` 移除公开 message 参数；异常处理器只返回冻结目录 message。
- 测试验证三个 API 签名拒绝覆盖，并逐个验证 34 个错误码的唯一稳定 message。
- `packages/common/README.md` 与公共响应文档同步公开规则。

### 3. 实际响应键集合

- `ApiResponse` 保留公开导出，并使用 Pydantic v2 wrap serializer 只在 `details is None` 时省略该键；`data: null` 始终保留。
- 真实 FastAPI 成功 JSON 精确为 `code/message/data/traceId/timestamp`。
- 失败 JSON 始终含上述基础键；仅有字段详情时增加 `details`。
- `response-and-errors.md` 删除不受支持的 `requestId`，将 `timestamp` 冻结为必填并同步示例。

### 4. 多轮 FL 唯一交接

- `openapi.md`、`main-flow.md`、`module-contracts.md` 同步冻结：start 无请求体并返回第 1 轮；每轮先 privacy secure-aggregate、再 FL aggregate。
- updates 请求体精确为 `participantDid/sampleCount/modelUpdateUri/updateHash`；aggregate 请求体精确为 `aggregateId/aggregateResultUri/aggregateHash`；路径 ID 不在 body 重复。
- 非最终轮返回 `status: running`、整数 `nextRound`、下一轮完整 `updates[]`。
- 最终轮返回 `status: completed`、`nextRound: null`、`updates: []`、最终 `globalModelVersion/modelHash/metrics`。
- 契约测试解析所有关键 JSON 并验证首轮、非最终轮、最终轮及路径/body 边界。

### 5. 契约测试与 OpenAPI 完整度

- 31 个矩阵端点与 31 个唯一正文 H3 双向精确匹配，`GET /health` 由公共正文 H3 描述。
- 每个端点包含请求来源/Schema 或无请求体、字段类型和必填性、成功 `data` 结构/JSON、公共错误目录引用、幂等规则；GET 明确“不适用”。
- demo、FL、privacy、四个 Agent 关键请求/响应示例均为可解析 JSON。
- 未增加端点、错误码目录或第一周范围。

### 6. 公共包职责

- `module-contracts.md` 的总览与公共包章节均限制为统一响应、错误码、`traceId`、UTC 时间、冻结 ID、`HealthData`/`ErrorDetail`。
- 明确模块 DTO、哈希、签名、加密和业务工具不属于公共包；哈希/签名归源端采集或对应业务模块。

### 7. UTF-8、LF 与设计状态

- 清除 `module-contracts.md` UTF-8 BOM，并将本波 13 个文本文件规范为严格 UTF-8、无 BOM、LF。
- 新增 `.gitattributes`：`* text=auto eol=lf`，并标记常见图片、模型、PDF、压缩包为 binary。
- `week-one-mock-delivery.md` 将旧歧义章节改为“已冻结决策与完成状态”，明确 `traceId` 只在公共响应包络。
- 仅修正 `.gitignore` 注释，未删除已跟踪 `docs/superpowers` 或任何用户文件。

## TDD 证据

### 基线

```text
packages/common/tests: 31 passed, 1 dependency warning
tests/integration/test_contract_docs.py: 9 passed
```

### RED：公共包行为

命令：

```powershell
& $python -m pytest packages/common/tests/test_response.py packages/common/tests/test_fastapi_support.py -q
```

输出摘要：`7 failed, 21 passed, 1 warning`。失败精确命中 message 覆盖、成功响应多出 `details`、418/501 状态被改写、401/405/429 标准头或原状态丢失。

### GREEN：公共包行为

同一命令输出：`28 passed, 1 warning`。

### RED：正式文档契约

命令：

```powershell
& $python -m pytest tests/integration/test_contract_docs.py -q -p no:cacheprovider
```

初始输出摘要：`9 failed, 9 passed`。失败精确命中 FL 交接/path ID、关键 JSON、矩阵与 `/health` H3、端点完整度、响应键、公共包边界、冻结状态、`.gitattributes`/BOM。

补充自审 RED：

- start 无请求体冻结：`1 failed`，修正文档后 `1 passed`。
- 成功说明显式 `data` 完整度：完整门禁曾为 `1 failed, 17 passed`，修正标签后全绿。

### GREEN：正式文档契约

聚焦命令最终输出：`18 passed`。

## 最终门禁

解释器：`Python 3.11.9`。

```powershell
$python = 'C:\Users\David\AppData\Local\Temp\vpp-python311\python.exe'
$deps = 'C:\Users\David\AppData\Local\Temp\vpp-test-deps311'
$src = Join-Path (Get-Location) 'packages/common/src'
$env:PYTHONPATH = "$deps;$src"
& $python -m pytest packages/common/tests -q
```

最终输出：`50 passed, 1 warning in 0.72s`。警告为测试依赖中的 `StarletteDeprecationWarning`（httpx/TestClient 兼容层），本波未改依赖范围。

```powershell
& $python -m pytest tests/integration/test_contract_docs.py -q -p no:cacheprovider
```

最终输出：`18 passed in 0.05s`。

附加检查：

```text
UTF-8 strict/no BOM/LF: 13 files
git diff --check: exit 0, no output
```

## 文件列表

- `.gitattributes`（新增）
- `.gitignore`
- `docs/api/openapi.md`
- `docs/api/response-and-errors.md`
- `docs/design/main-flow.md`
- `docs/design/module-contracts.md`
- `docs/design/week-one-mock-delivery.md`
- `packages/common/README.md`
- `packages/common/src/vpp_common/fastapi_support.py`
- `packages/common/src/vpp_common/response.py`
- `packages/common/tests/test_fastapi_support.py`
- `packages/common/tests/test_response.py`
- `tests/integration/test_contract_docs.py`

## 自审

- 逐条回读 `final-fix-brief.md`，七组要求均有实现和自动化证据。
- 34 个错误码数值/message 与 14 个 ID 前缀未修改；对应冻结测试通过。
- `ApiResponse`、`success`、`failure` 公开导出保持；仅按简报移除 message 覆盖参数。
- 未泄漏 HTTPException detail、内部异常、Cookie 或自定义/调试头。
- 矩阵、正文 H3、模块外部接口三方匹配；关键 JSON 均由 `json.loads` 解析。
- 未触碰 Compose、服务实现、数据库、区块链、算法、前端或业务模块。
- 当前环境无子代理；按 code-reviewer 检查目标执行了两遍人工 diff/契约审查。

## 未处理项与关注点

- 未处理项：无。
- 关注点：公共包门禁有 1 个来自外部测试依赖的 Starlette/httpx 弃用警告，不影响退出码或本波契约；依赖升级不在本波范围。

## 提交

- 标题：`fix: close final contract review findings`
- SHA：`e12fad906f8b5040d16d280a71dd30cfe39b7d3d`。

---

# 最终复审跟进波（1 Important + 3 Minor）

## 状态与范围

- 起始 HEAD：`e12fad906f8b5040d16d280a71dd30cfe39b7d3d`，未改写历史。
- 完成 `failure()` HTTP 使用边界、OpenAPI 维护规则、31 端点精确冻结、根 README 编码及错误目录一致性五项闭环。
- 未增加响应体中间件，未修改业务模块、服务实现、Compose 或前端。

## 实现

1. `failure()` 保持冻结导出和 `ApiResponse` 返回类型，新增公开 docstring，明确仅供异常处理器和非 HTTP 场景构造包络；`details=[]` 规范化为 `None`，序列化不含 `details`。
2. `packages/common/README.md` 新增正确 FastAPI 路由示例：业务失败 `raise ServiceError(...)`；醒目标明禁止直接 `return failure(...)`，并解释普通返回会错误保持 HTTP 200。
3. `response-and-errors.md` 同步同一边界、空 details 语义和“不使用响应体中间件”的决策。
4. 新增真实 FastAPI 409 路由回归，验证非 200 状态、冻结业务码/message、trace 头体一致和精确基础键。
5. `openapi.md` 维护规则改为每端点必须有“可能错误”并引用公共错误目录，不再要求逐端点错误响应 JSON。
6. 契约测试硬编码 31 个 `(module, method, path)`，与覆盖矩阵精确比较；包含 `所有服务 GET /health`。
7. 根 `README.md` 清除 UTF-8 BOM 并规范为 LF；加入正式 UTF-8/no-BOM/LF 门禁。
8. 契约测试解析 `response-and-errors.md` 的 34 行错误码/message，并与 `ErrorCode`/`ERROR_MESSAGES` 精确比较。

## TDD 证据

### RED：公共包

```powershell
& $python -m pytest packages/common/tests/test_response.py packages/common/tests/test_fastapi_support.py -q
```

输出：`2 failed, 29 passed, 1 warning`。失败原因分别为 `failure(details=[])` 未规范化及 `failure()` 缺少公开使用边界 docstring；新增真实 ServiceError 路由回归通过现有异常处理路径。

### RED：契约

```powershell
& $python -m pytest tests/integration/test_contract_docs.py -q -p no:cacheprovider
```

输出：`3 failed, 18 passed`。失败原因分别为两份公开边界说明缺失、OpenAPI 仍要求失败示例、根 README 含 BOM；31 端点精确集合与 34 条错误目录比较直接通过。

### 聚焦 GREEN

- 公共包聚焦：`31 passed, 1 warning`。
- 契约聚焦：`21 passed`。

## 当前唯一完整门禁

解释器：`Python 3.11.9`。

```powershell
& $python -m pytest packages/common/tests -q
```

输出：`53 passed, 1 warning in 0.83s`。

```powershell
& $python -m pytest tests/integration/test_contract_docs.py -q -p no:cacheprovider
```

输出：`21 passed in 0.43s`。

```text
UTF-8 strict/no BOM/LF: 17 files
git diff --check: exit 0, no output
```

## 本波文件

- `README.md`
- `docs/api/openapi.md`
- `docs/api/response-and-errors.md`
- `packages/common/README.md`
- `packages/common/src/vpp_common/response.py`
- `packages/common/tests/test_fastapi_support.py`
- `packages/common/tests/test_response.py`
- `tests/integration/test_contract_docs.py`

## 自审与未处理项

- `ApiResponse`、`failure` 导出及返回类型未改变；没有响应体中间件。
- 真实 HTTP 路由以 `ServiceError` 产生 409，响应键和 trace 契约由测试锁定。
- 31 个端点和 34 条错误码/message 均为精确集合比较，无法通过同步删增静默漂移。
- 根 README 与其余正式文件均严格 UTF-8、无 BOM、LF。
- 未处理项：无。
- 关注点：唯一警告仍是外部测试依赖的 Starlette/httpx 弃用提示，依赖升级不在本波范围。

## 新提交

- 标题：`fix: harden failure and contract boundaries`
- SHA：`98b4decc6fc31486ae8845c47e1dc6b56102d547`。
