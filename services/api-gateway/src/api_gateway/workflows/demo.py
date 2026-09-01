from vpp_common import new_id

from ..clients.meter import MeterClient
from ..clients.ingestion import IngestionClient
from ..clients.identity import IdentityClient
from ..clients.fl import FLClient
from ..clients.privacy import PrivacyClient
from ..clients.ledger import LedgerClient
from ..clients.agent import AgentClient
from ..repository import repository
from ..schemas import DemoRequest, DemoResult, WorkflowState


class DemoWorkflow:
    """
    Demo workflow orchestration (7-stage skeleton).

    Downstream clients perform real HTTP calls.
    """

    def __init__(
        self,
        *,
        meter=None,
        ingestion=None,
        identity=None,
        fl=None,
        privacy=None,
        ledger=None,
        agent=None,
    ):
        self.meter = meter or MeterClient()
        self.ingestion = ingestion or IngestionClient()
        self.identity = identity or IdentityClient()
        self.fl = fl or FLClient()
        self.privacy = privacy or PrivacyClient()
        self.ledger = ledger or LedgerClient()
        self.agent = agent or AgentClient()

    def _hash_request(self, request: DemoRequest) -> str:
        import hashlib
        import json
        content = json.dumps(request.model_dump(), sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    async def run(self, request: DemoRequest, trace_id: str) -> DemoResult:
        business_id = new_id("demo_")
        request_hash = self._hash_request(request)

        state = WorkflowState(
            businessId=business_id,
            request_hash=request_hash,
            status="RUNNING",
            currentStage="CREATED",
            traceId=trace_id,
        )
        repository.save(state)

        try:
            # 1. Meter data collection
            meter_data = await self.meter.collect_readings(
                request.meterCount, trace_id
            )
            state.currentStage = "DATA_COLLECTED"
            repository.save(state)

            # 2. Data registration
            asset = await self.ingestion.register_asset(meter_data, trace_id)
            asset_id = asset["assetId"]
            state.currentStage = "DATA_REGISTERED"
            repository.save(state)

            # 3. Identity authorization
            await self.identity.authorize(request.participants, trace_id)
            state.currentStage = "AUTHORIZED"
            repository.save(state)

            # 4. Federated learning
            model = await self.fl.train(
                asset_id, request.trainingRounds, trace_id
            )
            model_version = model["globalModelVersion"]
            state.currentStage = "MODEL_READY"
            repository.save(state)

            # 5. Privacy compute
            await self.privacy.execute(model_version, trace_id)
            state.currentStage = "PRIVACY_COMPLETED"
            repository.save(state)

            # 6. Ledger record
            await self.ledger.record(asset_id, trace_id)
            state.currentStage = "LEDGER_RECORDED"
            repository.save(state)

            # 7. Agent report
            report = await self.agent.generate_report(model_version, trace_id)
            state.currentStage = "AGENT_COMPLETED"
            repository.save(state)

            result = DemoResult(
                businessId=business_id,
                assetId=asset_id,
                globalModelVersion=model_version,
                agentReportId=report["agentReportId"],
                status="COMPLETED",
                metrics={
                    "accuracy": model.get("accuracy"),
                    "rounds": model.get("rounds"),
                },
            )

            state.status = "COMPLETED"
            state.currentStage = "AGENT_COMPLETED"
            state.result = result
            repository.save(state)

            return result

        except Exception:
            state.status = "FAILED"
            state.currentStage = "ERROR"
            repository.save(state)
            raise