# Task 1: 冻结运行时与公共基础协议

## 目标

复核并完成当前工作区中已经开始的技术负责人 Day 1 基线：技术版本、UTF-8、`vpp_common` 公共包、统一错误码、`traceId` 和 ID 前缀。不得修改模块业务实现。

## 所有权文件

- `.python-version`
- `.nvmrc`
- `.editorconfig`
- `.gitignore`
- `README.md`
- `docs/api/response-and-errors.md`
- `packages/common/README.md`
- `packages/common/pyproject.toml`
- `packages/common/src/vpp_common/*.py`
- `packages/common/tests/*.py`

不得修改 `docs/api/openapi.md`、`docs/design/main-flow.md`、`docs/design/module-contracts.md` 或 `tests/integration/test_contract_docs.py`；这些属于 Task 2。

## 冻结值

- Python `3.11`，`.python-version` 内容必须是 `3.11`。
- Node.js `24 LTS`，`.nvmrc` 内容必须是 `24`。
- FastAPI `>=0.115,<1`，Pydantic `>=2,<3`。
- 测试依赖：httpx `>=0.28,<1`、pytest `>=8,<9`。
- 前端：Vue 3、Vite、JavaScript、Element Plus、Axios；第一周不使用 TypeScript、Pinia、Nuxt。
- 服务通信：HTTP/1.1 + JSON。
- 文本编码 UTF-8、LF；Windows PowerShell 示例显式使用 `-Encoding UTF8`。
- 公共包名 `vpp-common`，版本 `0.1.0`，Python 要求 `>=3.11,<3.12`。

## 公共 API

`vpp_common.__init__` 必须导出：`ApiResponse`、`ErrorCode`、`ServiceError`、`failure`、`install_exception_handlers`、`new_id`、`resolve_trace_id`、`success`、`utc_now_iso`。

公共包只允许包含响应、错误、FastAPI 异常/追踪支持、UTC 时间、ID 和 `HealthData`/`ErrorDetail` 基础 Schema。禁止模块 DTO、数据库模型、业务逻辑、环境配置。

## 错误码与响应

- `docs/api/response-and-errors.md` 是单一来源，共 34 个错误码：`40001`-`40005`、`40101`-`40104`、`40301`-`40303`、`40401`-`40404`、`40901`-`40903`、`42201`-`42204`、`42901`、`50001`-`50003`、`50201`-`50203`、`50301`-`50303`、`50401`。
- 成功包络：`code=0`、`message=ok`、`data`、`traceId`；失败包络：非零 `code`、稳定 message、`data=null`、`traceId`、可选 `details`。
- HTTP 状态由错误码前三位映射。
- 未捕获异常不得泄漏内部异常消息。

## traceId

- Header 固定为 `X-Trace-Id`。
- 合法值以 `trace_` 开头，仅允许字母、数字、点、下划线、冒号、连字符，总长度不超过 128。
- 合法入站值原样保留；缺失或非法时生成。
- 当前请求的响应体与响应头使用同一个值；下游应复用，不得重生成。
- `install_exception_handlers(app)` 安装追踪中间件和统一异常处理。

## ID 前缀

必须且只能包含：`demo_`、`batch_`、`reading_`、`asset_`、`auth_`、`fl_task_`、`aggregate_`、`global_model_v`、`prediction_`、`strategy_`、`report_`、`evt_`、`tx_`、`trace_`。未知前缀抛出 `ValueError`。

## 测试与交付

当前测试已由控制器先写并确认 RED：`vpp_common` 尚未存在时，4 个测试模块在收集阶段报 `ModuleNotFoundError`。复核测试质量，修复实现后运行：

```powershell
$python = 'C:\Users\David\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$deps = Join-Path $env:TEMP 'vpp-test-deps'
$src = Join-Path (Get-Location) 'packages/common/src'
$env:PYTHONPATH = "$deps;$src"
& $python -m pytest packages/common/tests -q
```

测试输出必须通过且无项目代码警告。只提交所有权文件，提交信息：`feat: add common package and repository baseline`。

