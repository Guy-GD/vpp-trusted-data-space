from uuid import uuid4
import hashlib
import json


from ..audit import audit_service

from ..clients.meter import MeterClient
from ..clients.ingestion import IngestionClient
from ..clients.identity import IdentityClient
from ..clients.fl import FLClient
from ..clients.privacy import PrivacyClient
from ..clients.ledger import LedgerClient
from ..clients.agent import AgentClient


from ..repository import repository


from ..schemas import (
    DemoRequest,
    DemoResult,
    WorkflowState,
)



class DemoWorkflow:
    """
    Demo workflow orchestration.

    Add audit trail support.
    """


    def __init__(self):

        self.meter = MeterClient()

        self.ingestion = IngestionClient()

        self.identity = IdentityClient()

        self.fl = FLClient()

        self.privacy = PrivacyClient()

        self.ledger = LedgerClient()

        self.agent = AgentClient()



    def _hash_request(
        self,
        request: DemoRequest,
    ) -> str:

        content = json.dumps(
            request.model_dump(),
            sort_keys=True,
        )

        return hashlib.sha256(
            content.encode()
        ).hexdigest()



    async def run(
        self,
        request: DemoRequest,
        trace_id: str,
    ) -> DemoResult:


        business_id = (
            f"demo_{uuid4().hex[:8]}"
        )


        request_hash = self._hash_request(
            request
        )


        state = WorkflowState(
            businessId=business_id,
            request_hash=request_hash,
            status="RUNNING",
            currentStage="CREATED",
            traceId=trace_id,
        )


        repository.save(state)


        try:

            # ==========================
            # 1. Meter Data Collection
            # ==========================

            meter_data = await self.meter.collect_readings(
                request.meterCount,
                trace_id,
            )


            state.currentStage = (
                "DATA_COLLECTED"
            )

            repository.save(state)


            await audit_service.record(
                trace_id,
                business_id,
                "DATA_COLLECTED",
                "meter-simulator",
                "collect_readings",
            )



            # ==========================
            # 2. Data Registration
            # ==========================

            asset = await self.ingestion.register_asset(
                meter_data,
                trace_id,
            )


            state.currentStage = (
                "DATA_REGISTERED"
            )

            repository.save(state)


            await audit_service.record(
                trace_id,
                business_id,
                "DATA_REGISTERED",
                "data-ingestion",
                "register_asset",
            )



            # ==========================
            # 3. Identity Authorization
            # ==========================

            await self.identity.authorize(
                request.participants,
                trace_id,
            )


            state.currentStage = (
                "AUTHORIZED"
            )

            repository.save(state)


            await audit_service.record(
                trace_id,
                business_id,
                "AUTHORIZED",
                "identity-service",
                "authorize",
            )



            # ==========================
            # 4. Federated Learning
            # ==========================

            model = await self.fl.train(
                asset["assetId"],
                request.trainingRounds,
                trace_id,
            )


            state.currentStage = (
                "MODEL_READY"
            )

            repository.save(state)


            await audit_service.record(
                trace_id,
                business_id,
                "MODEL_READY",
                "federated-learning",
                "train",
                {
                    "modelVersion":
                    model["globalModelVersion"]
                },
            )



            # ==========================
            # 5. Privacy Compute
            # ==========================

            await self.privacy.execute(
                model["globalModelVersion"],
                trace_id,
            )


            state.currentStage = (
                "PRIVACY_COMPLETED"
            )

            repository.save(state)


            await audit_service.record(
                trace_id,
                business_id,
                "PRIVACY_COMPLETED",
                "privacy-compute",
                "execute",
            )



            # ==========================
            # 6. Ledger Record
            # ==========================

            await self.ledger.record(
                asset["assetId"],
                trace_id,
            )


            state.currentStage = (
                "LEDGER_RECORDED"
            )

            repository.save(state)


            await audit_service.record(
                trace_id,
                business_id,
                "LEDGER_RECORDED",
                "trusted-ledger",
                "record",
            )



            # ==========================
            # 7. Agent Report
            # ==========================

            report = await self.agent.generate_report(
                model["globalModelVersion"],
                trace_id,
            )


            state.currentStage = (
                "AGENT_COMPLETED"
            )

            repository.save(state)


            await audit_service.record(
                trace_id,
                business_id,
                "AGENT_COMPLETED",
                "agent-service",
                "generate_report",
            )



            result = DemoResult(
                businessId=business_id,
                assetId=asset["assetId"],
                globalModelVersion=model[
                    "globalModelVersion"
                ],
                agentReportId=report[
                    "agentReportId"
                ],
                status="COMPLETED",
                metrics={
                    "accuracy": model["accuracy"],
                    "rounds": model["rounds"],
                },
            )


            state.status = "COMPLETED"

            state.currentStage = (
                "AGENT_COMPLETED"
            )

            state.result = result


            repository.save(state)


            return result



        except Exception:

            state.status = "FAILED"

            state.currentStage = (
                "ERROR"
            )


            repository.save(state)


            raise