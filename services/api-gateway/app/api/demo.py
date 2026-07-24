# services/api-gateway/app/api/demo.py

import httpx
from fastapi import APIRouter, Request
from app.core.exceptions import UpstreamServiceError

router = APIRouter(prefix="/v1", tags=["Demo"])

@router.get("/test", summary="测试接口")
async def test_endpoint():
    """
    一个简单的测试接口，证明网关能正常工作。
    后续可以在这里添加转发到 VPP 节点的逻辑。
    """
    return {"message": "Gateway is working! Ready to connect VPP nodes."}

@router.post("/data/upload", summary="模拟数据上传")
async def upload_data(request: Request):
    # 这里未来可以写转发逻辑，比如转发给内部的 Python 节点或 Java 节点
    body = await request.json()
    return {
        "received": True,
        "data_size": len(str(body)),
        "note": "Data received by Gateway (Mock)"
    }