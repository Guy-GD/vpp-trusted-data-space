# vpp-common

`vpp-common` 是八个 FastAPI 后端共享的最小公共包，版本冻结为 `0.1.0`。它只提供统一响应、错误码、异常处理、`traceId`、业务 ID、UTC 时间和跨模块基础 Schema。

## 安装

在仓库根目录使用 Python 3.11：

```powershell
python -m pip install -e "packages/common[test]"
```

业务服务必须依赖此包，不得复制响应或错误码实现。模块专属 DTO、数据库模型、环境配置和业务逻辑不得放入公共包。

## 使用

```python
from fastapi import FastAPI
from vpp_common import (
    ErrorCode,
    ServiceError,
    install_exception_handlers,
    new_id,
    success,
)
from vpp_common.schemas import ErrorDetail

app = FastAPI()
install_exception_handlers(app)


@app.get("/health")
def health():
    return success({"service": "example", "status": "healthy"})


@app.get("/assets/{asset_id}")
def get_asset(asset_id: str):
    if asset_id != "asset_001":
        raise ServiceError(
            ErrorCode.RESOURCE_NOT_FOUND,
            details=[ErrorDetail(field="assetId", reason="not found")],
        )
    return success({"assetId": asset_id, "status": "registered"})


asset_id = new_id("asset_")
```

`install_exception_handlers()` 同时安装追踪中间件：读取或生成 `X-Trace-Id`，在当前请求的响应体、响应头及下游调用中复用同一个值。

`success(data)` 的 `message` 固定为 `ok`；`failure(code)` 和 `ServiceError(code)` 的 `message` 固定取自错误码目录，三个公开 API 均不接受调用方覆盖 message。成功 JSON 固定包含 `code`、`message`、`data`、`traceId`、`timestamp`；失败 JSON 只有存在字段详情时才增加 `details`。

### HTTP 失败边界

`failure()` 保持冻结公开导出并返回 `ApiResponse`，但它只用于异常处理器/非 HTTP 场景的包络构造器。HTTP 路由业务失败必须 `raise ServiceError(code, details=...)`，由统一异常处理器同时确定非 200 HTTP 状态和错误包络。

> **禁止**：禁止在 FastAPI 路由中直接 `return failure(...)`。FastAPI 会把普通返回值按成功路径序列化，导致 HTTP 状态错误地保持为 `200`；本包不会使用响应体中间件猜测并改写状态。

传入 `failure(..., details=[])` 会规范化为 `details=None`，序列化 JSON 不包含 `details`。

标准 HTTP 异常保留原 HTTP 状态，只透传 `Allow`、`WWW-Authenticate`、`Retry-After` 三个协议头，且不会把异常 `detail` 返回客户端。

## 公共 API 冻结规则

- 当前公共 API 版本：`0.1.0`。
- 接口变更必须先更新正式契约文档并由技术负责人批准。
- 只允许向后兼容的阻塞修复进入第一周公共包。
- 错误码与 ID 前缀分别以 `docs/api/response-and-errors.md` 和本包常量为准。
