from fastapi import FastAPI
from .api import router

# 接入公共包的 FastAPI 支持与响应封装
from vpp_common import install_exception_handlers, success
from vpp_common.schemas import HealthData

# 创建FastAPI应用
app = FastAPI(title="Privacy Compute Service", version="0.1.0")

# 注册全局异常/追踪中间件与处理器
install_exception_handlers(app)

# 注册路由（把api.py里的接口都注册进来）
app.include_router(router)

@app.get("/health")
def health():
    """健康检查接口，返回统一包络"""
    return success(HealthData(service="privacy-compute", status="healthy"))

if __name__ == "__main__":
    import uvicorn
    # 启动服务器：host=0.0.0.0 表示允许外部访问，port=8000 表示端口号
    uvicorn.run(app, host="0.0.0.0", port=8000)