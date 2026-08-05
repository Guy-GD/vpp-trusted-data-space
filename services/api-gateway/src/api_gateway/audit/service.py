from datetime import datetime

from .models import AuditEvent
from .hash import calculate_event_hash
from . import repository
from .database import (
    init_database,
    insert_event,
)



class AuditService:
    """
    Audit service.

    Responsible for creating
    trusted audit chain.
    """


    def __init__(self):

        # 初始化数据库

        init_database()



    async def record(
        self,
        trace_id: str,
        business_id: str,
        stage: str,
        service: str,
        action: str,
        detail: dict | None = None,
    ):

        if detail is None:
            detail = {}


        # 获取上一条审计记录

        previous_hash = (
            repository
            .get_last_hash(
                business_id
            )
        )


        event = AuditEvent(

            traceId=trace_id,

            businessId=business_id,

            stage=stage,

            service=service,

            action=action,

            status="SUCCESS",

            timestamp=datetime.utcnow(),

            detail=detail,

            previousHash=previous_hash,

        )


        # 计算当前事件hash

        event_data = event.model_dump(
            mode="json"
        )


        event_hash = (
            calculate_event_hash(
                event_data
            )
        )


        event.eventHash = event_hash



        # 保存到内存仓库

        repository.save(
            event
        )


        # 保存数据库

        insert_event(
            event.model_dump(
                mode="json"
            )
        )


        return event



# 全局实例

audit_service = AuditService()