# Task 1：冻结运行时与公共基础协议——实施报告

## 实现

- 复核并完善第一周运行时基线：Python `3.11`、Node.js `24`、UTF-8/LF 编辑规则、忽略规则与仓库 README。
- 完成 `vpp-common==0.1.0`：受限 Python/FastAPI/Pydantic 依赖、34 个冻结错误码、统一成功/失败包络、UTC 时间、14 个 ID 前缀、基础 Schema、FastAPI 异常与追踪支持，以及冻结的公共导出。
- 将 `trace_` 识别为合法的最短 traceId；规则仍限制为 `trace_` 前缀、允许字符集与总长不超过 128。
- 修复 FastAPI 错误响应：现在始终保留协议强制的 `data: null`，仅在无详情时省略可选 `details`。
- 更新公共响应与错误码单一来源文档、公共包 README 和根 README。

## 测试命令与结果

简报命令（以提升权限读取控制器已准备的临时依赖目录后执行）：

```powershell
$python = 'C:\Users\David\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$deps = Join-Path $env:TEMP 'vpp-test-deps'
$src = Join-Path (Get-Location) 'packages/common/src'
$env:PYTHONPATH = "$deps;$src"
& $python -m pytest packages/common/tests -q
```

结果：`30 passed, 1 warning in 0.87s`。警告来自临时依赖中的 `fastapi/testclient.py`（Starlette 的弃用提示），不是项目代码警告。

另运行：`git diff --check`，退出码 `0`。

## RED 证据

- 控制器提供的先行 RED 证据：`vpp_common` 尚不存在时，4 个测试模块在收集阶段因 `ModuleNotFoundError` 失败。
- 复核时新增 `trace_` 边界回归：`packages/common/tests/test_tracing.py -q` 为 `1 failed, 4 passed`；现有正则错误地替换了合法的 `trace_`。
- 完整测试的首轮复核为 `1 failed, 29 passed`：`test_service_error_uses_unified_envelope` 发现错误响应缺少强制字段 `data: null`。

## GREEN 证据

- 边界回归修复后：`5 passed`。
- 完整 Task 1 测试集修复后：`30 passed`。

## 文件列表

所有权范围内的基线文件：`.python-version`、`.nvmrc`、`.editorconfig`、`.gitignore`、`README.md`、`docs/api/response-and-errors.md`、`packages/common/README.md`、`packages/common/pyproject.toml`。

所有权范围内的公共包和测试：`packages/common/src/vpp_common/__init__.py`、`errors.py`、`response.py`、`schemas.py`、`tracing.py`、`fastapi_support.py`、`id_generator.py`、`time_utils.py`，以及 `packages/common/tests/test_response.py`、`test_tracing.py`、`test_ids.py`、`test_fastapi_support.py`。

## 自审与关注点

- 已逐项检查冻结版本、34 个错误码、HTTP 映射、公共导出、追踪规则、ID 前缀和公共包范围；未发现模块 DTO、数据库模型、业务逻辑或环境配置混入公共包。
- 已确认 Task 2 专属文件 `docs/api/openapi.md`、`docs/design/main-flow.md`、`docs/design/module-contracts.md` 与 `tests/integration/test_contract_docs.py` 保持未暂存。
- 需关注：测试使用简报指定的缓存运行时（其当前为 CPython 3.12），而包元数据和冻结运行时仍严格声明 Python `>=3.11,<3.12`；本任务没有可用的本地 Python 3.11 可执行文件可额外验证。
- 需关注：完整测试只有一个第三方 FastAPI/Starlette 的弃用警告；项目测试与项目代码本身没有警告。

## 审查修复：HTTPException 统一响应

### 实现

- 在 `install_exception_handlers()` 中显式注册 `starlette.exceptions.HTTPException` 处理器。实际运行时验证显示 `fastapi.exceptions.HTTPException` 不是同一类型、但继承自该 Starlette 类型，因此该处理器同时覆盖 FastAPI 与 Starlette HTTP 异常。
- 冻结 HTTP→业务码映射集中在私有 `_HTTP_STATUS_ERROR_CODES`：`400→40001`、`401→40101`、`403→40301`、`404→40401`、`409→40901`、`422→42201`、`429→42901`、`500→50001`、`502→50201`、`503→50301`、`504→50401`；其他 HTTP 状态安全回退到 `50001`。
- 新处理器复用 `_json_error()`，因而状态码、`data: null`、响应头/响应体 traceId 一致性和内部详情不泄露均与既有统一错误路径一致。

### 新 RED/GREEN 证据

- RED：新增真实 FastAPI `HTTPException(status_code=404, detail="secret HTTP exception detail")` 路由后，以下聚焦命令得到 `1 failed, 4 passed, 1 warning`，失败于响应默认包络缺少 `code`：

```powershell
$python = 'C:\Users\David\AppData\Local\Temp\vpp-python311\python.exe'
$deps = 'C:\Users\David\AppData\Local\Temp\vpp-test-deps311'
$env:PYTHONPATH = "$deps;$(Join-Path (Get-Location) 'packages/common/src')"
& $python -m pytest packages/common/tests/test_fastapi_support.py -q
```

- GREEN（同一命令）：`5 passed, 1 warning in 0.70s`。
- 完整验证（同一 `PYTHONPATH`，命令为 `& $python -m pytest packages/common/tests -q`）：`31 passed, 1 warning in 0.72s`。
- 运行时验证：`C:\Users\David\AppData\Local\Temp\vpp-python311\python.exe --version` 输出 `Python 3.11.9`。
- 两次警告均来自临时依赖 `vpp-test-deps311\fastapi\testclient.py` 的 Starlette 弃用提示，而非项目代码。

### 本次文件与自审

- 修改：`packages/common/src/vpp_common/fastapi_support.py`、`packages/common/tests/test_fastapi_support.py`；本报告追加于忽略的 `.superpowers/sdd/task-1-report.md`，不提交。
- 新回归测试使用真实请求，断言 HTTP `404`、业务码 `40401`、`data is null`、入站 traceId 与响应体/响应头一致，并断言 `detail` 和原始详情均不泄露。
- `git diff --check` 退出码 `0`；Task 2 文件仍为既有未暂存改动，未包含在本次修复范围或提交中。
