from fastapi import APIRouter, HTTPException, Request
from .schemas import SecureAggregateRequest, EncryptRequest, MaskRequest
from .service import PrivacyService
from .repository import PrivacyRepository

# 创建路由器（相当于"服务员"）
router = APIRouter(prefix="/api/v1/privacy", tags=["privacy"])

# 创建仓库和服务实例
repository = PrivacyRepository()
service = PrivacyService(repository)

# 幂等性存储（防止重复提交）
_idempotency_store = {}

@router.post("/secure-aggregate", response_model=dict)
async def secure_aggregate(request: Request, payload: SecureAggregateRequest):
    """安全聚合接口"""
    # 检查幂等键（防止同一请求重复处理）
    idempotency_key = request.headers.get("Idempotency-Key")
    if idempotency_key:
        if idempotency_key in _idempotency_store:
            existing = _idempotency_store[idempotency_key]
            if existing != payload.model_dump():
                raise HTTPException(
                    status_code=409,
                    detail={"code": "40901", "message": "Same key with different body"}
                )
            return {"data": _idempotency_store.get(f"result_{idempotency_key}")}
    
    try:
        result = service.secure_aggregate(payload)
        if idempotency_key:
            _idempotency_store[idempotency_key] = payload.model_dump()
            _idempotency_store[f"result_{idempotency_key}"] = result.model_dump()
        return {"data": result.model_dump()}
    except ValueError as e:
        if "least 2 updates" in str(e):
            raise HTTPException(status_code=422, detail={"code": "42202", "message": str(e)})
        raise HTTPException(status_code=422, detail={"code": "42203", "message": str(e)})

@router.get("/aggregate/{aggregate_id}")
async def get_aggregate(aggregate_id: str):
    """查询聚合结果"""
    result = service.get_aggregate(aggregate_id)
    if not result:
        raise HTTPException(status_code=404, detail={"code": "40401", "message": "Aggregate not found"})
    return {"data": result.model_dump()}

@router.post("/encrypt")
async def encrypt_data(payload: EncryptRequest):
    """加密数据接口"""
    result = service.encrypt_data(payload.plaintext, payload.participantDid)
    return {"data": result}

@router.post("/mask")
async def mask_update(payload: MaskRequest):
    """掩码数据接口"""
    result = service.mask_update(payload.updateId, payload.maskingType)
    return {"data": result}