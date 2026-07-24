# services/api-gateway/app/main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api import health, demo
from app.core.exceptions import AppException

app = FastAPI(title="VPP Trusted Data Gateway", version="1.0.0")

# 注册路由
app.include_router(health.router)
app.include_router(demo.router)

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error_code": exc.error_code}
    )

@app.get("/")
async def root():
    return {"message": "Gateway is running", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)