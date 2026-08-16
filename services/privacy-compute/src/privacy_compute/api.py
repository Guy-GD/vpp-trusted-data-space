from fastapi import APIRouter, Request
from .schemas import SecureAggregateRequest, EncryptRequest, MaskRequest
from .service import PrivacyService
from .repository import PrivacyRepository

# 使用仓内公共包的异常/错误码/响应封装
from vpp_common import ServiceError, ErrorCode
from vpp_common.schemas import ErrorDetail
from vpp_common import success

# 创建路由器（相当于"服务员"）
router = APIRouter(prefix="/api/v1/privacy", tags=["privacy"])

# 创建仓库和服务实例
repository = PrivacyRepository()
service = PrivacyService(repository)

# 幂等性存储（防止重复提交）
_idempotency_store = {}

@router.post("/secure-aggregate")
async def secure_aggregate(request: Request, payload: SecureAggregateRequest):
    """安全聚合接口"""
    # 检查幂等键（防止同一请求重复处理）
    idempotency_key = request.headers.get("Idempotency-Key")
    if idempotency_key:
        if idempotency_key in _idempotency_store:
            existing = _idempotency_store[idempotency_key]
            if existing != payload.model_dump():
                raise ServiceError(ErrorCode.IDEMPOTENCY_CONFLICT, details=[ErrorDetail(field="idempotencyKey", reason="Same key with different body")])
            return success(_idempotency_store.get(f"result_{idempotency_key}"))
    
    try:
        result = service.secure_aggregate(payload)
        if idempotency_key:
            _idempotency_store[idempotency_key] = payload.model_dump()
            _idempotency_store[f"result_{idempotency_key}"] = result.model_dump()
        return success(result.model_dump())
    except ValueError as e:
        msg = str(e)
        if "at least 2" in msg or "Need at least 2" in msg:
            raise ServiceError(ErrorCode.INSUFFICIENT_UPDATES, details=[ErrorDetail(field="updates", reason=msg)])
        # 不支持的模式等
        raise ServiceError(ErrorCode.UNSUPPORTED_PRIVACY_MODE, details=[ErrorDetail(field="privacyMode", reason=msg)])

@router.get("/aggregates/{aggregateId}")
async def get_aggregate(aggregateId: str):
    """查询聚合结果（按契约名称 aggregateId）"""
    result = service.get_aggregate(aggregateId)
    if not result:
        raise ServiceError(ErrorCode.RESOURCE_NOT_FOUND, details=[ErrorDetail(field="aggregateId", reason="Aggregate not found")])
    return success(result.model_dump())

@router.post("/model-updates/encrypt")
async def encrypt_data(payload: EncryptRequest):
    """加密数据接口（模型更新相关路径）"""
    result = service.encrypt_data(payload.plaintext, payload.participantDid)
    return success(result)

@router.post("/model-updates/mask")
async def mask_update(payload: MaskRequest):
    """掩码数据接口（模型更新相关路径）"""
    result = service.mask_update(payload.updateId, payload.maskingType)
    return success(result)