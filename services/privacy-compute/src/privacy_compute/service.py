import hashlib
import uuid
from datetime import datetime
from typing import Dict, Optional
from .schemas import SecureAggregateRequest, AggregateResponse
from .repository import PrivacyRepository


class PrivacyService:
    def __init__(self, repository: PrivacyRepository):
        self.repo = repository
        self._mock_results: Dict[str, AggregateResponse] = {}

    def secure_aggregate(self, request: SecureAggregateRequest) -> AggregateResponse:
        # 检查参与者数量（至少需要2人）
        if len(request.updates) < 2:
            raise ValueError("Need at least 2 updates for aggregation")
        
        # 生成聚合ID（使用公共包的新 ID 生成器）
        from vpp_common import new_id
        aggregate_id = new_id("aggregate_")
        
        # 模拟聚合（生成哈希值作为指纹）
        aggregate_hash = self._simulate_aggregation(request)
        
        # 构建响应对象
        response = AggregateResponse(
            aggregateId=aggregate_id,
            trainingTaskId=request.trainingTaskId,
            roundId=request.roundId,
            aggregateResultUri=f"memory://aggregates/{request.trainingTaskId}/round_{request.roundId}/result.json",
            aggregateHash=aggregate_hash,
            participantCount=len(request.updates),
            privacyMode=request.privacyMode,
        )
        
        # 存储结果
        self.repo.save_aggregate(aggregate_id, response.model_dump())
        self._mock_results[aggregate_id] = response
        
        return response

    def _simulate_aggregation(self, request: SecureAggregateRequest) -> str:
        """模拟聚合 - 正式环境下会做真正的计算"""
        content = f"{request.trainingTaskId}:{request.roundId}:{request.privacyMode}"
        for update in request.updates:
            content += f":{update.participantDid}:{update.updateHash}"
        return f"sha256:{hashlib.sha256(content.encode()).hexdigest()[:16]}"

    def get_aggregate(self, aggregate_id: str) -> Optional[AggregateResponse]:
        data = self.repo.get_aggregate(aggregate_id)
        return AggregateResponse(**data) if data else None

    def encrypt_data(self, plaintext: str, participant_did: str) -> Dict:
        """模拟加密 - 存储记录但绝不返回原始数据"""
        from vpp_common import new_id
        # 使用允许的 ID 前缀（evt_ 用于事件/操作）
        encryption_id = new_id("evt_")
        self.repo.save_encryption_record(encryption_id, {
            "participant_did": participant_did,
            "encrypted": f"encrypted:{plaintext[::-1]}",  # 简单模拟：反转字符串
            "created_at": datetime.utcnow().isoformat()
        })
        return {
            "encryptionId": encryption_id,
            "status": "encrypted",
            "participantDid": participant_did
        }

    def mask_update(self, update_id: str, masking_type: str) -> Dict:
        """模拟掩码 - 保护原始更新数据"""
        from vpp_common import new_id
        # 使用允许的 ID 前缀（evt_ 用于事件/操作）
        mask_id = new_id("evt_")
        self.repo.save_mask_record(mask_id, {
            "update_id": update_id,
            "masking_type": masking_type,
            "masked": f"masked_{masking_type}",
            "created_at": datetime.utcnow().isoformat()
        })
        return {
            "maskId": mask_id,
            "updateId": update_id,
            "maskingType": masking_type,
            "status": "masked"
        }