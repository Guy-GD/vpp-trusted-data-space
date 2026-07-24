from fastapi import FastAPI
from .api import router

# 创建FastAPI应用
app = FastAPI(title="Privacy Compute Service", version="0.1.0")

# 注册路由（把api.py里的接口都注册进来）
app.include_router(router)

@app.get("/health")
async def health():
    """健康检查接口"""
    return {"status": "healthy", "service": "privacy-compute"}

if __name__ == "__main__":
    import uvicorn
    # 启动服务器：host=0.0.0.0 表示允许外部访问，port=8000 表示端口号
    uvicorn.run(app, host="0.0.0.0", port=8000)