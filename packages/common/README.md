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
from vpp_common import install_exception_handlers, new_id, success

app = FastAPI()
install_exception_handlers(app)


@app.get("/health")
def health():
    return success({"service": "example", "status": "healthy"})


asset_id = new_id("asset_")
```

`install_exception_handlers()` 同时安装追踪中间件：读取或生成 `X-Trace-Id`，在当前请求的响应体、响应头及下游调用中复用同一个值。

## 公共 API 冻结规则

- 当前公共 API 版本：`0.1.0`。
- 接口变更必须先更新正式契约文档并由技术负责人批准。
- 只允许向后兼容的阻塞修复进入第一周公共包。
- 错误码与 ID 前缀分别以 `docs/api/response-and-errors.md` 和本包常量为准。
