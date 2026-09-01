import httpx
import pytest

from api_gateway.clients.meter import MeterClient
from api_gateway.clients.ingestion import IngestionClient
from api_gateway.clients.identity import IdentityClient
from api_gateway.clients.fl import FLClient
from api_gateway.clients.privacy import PrivacyClient
from api_gateway.clients.ledger import LedgerClient
from api_gateway.clients.agent import AgentClient
from api_gateway.workflows.demo import DemoWorkflow


def _ok(data: dict, trace_id: str) -> dict:
    return {"code": 0, "message": "ok", "data": data, "traceId": trace_id}


def downstream_handler(request: httpx.Request) -> httpx.Response:
    """Frozen downstream mock responses (uniform envelope, valid ID prefixes)."""
    path = request.url.path
    trace_id = request.headers.get("X-Trace-Id", "trace_test")

    if path == "/api/v1/meter/readings/generate":
        data = {
            "readingId": "reading_test0001",
            "meters": [
                {"meterId": "meter_1", "power": 100, "voltage": 220, "frequency": 50}
            ],
            "count": 1,
            "traceId": trace_id,
        }
        return httpx.Response(200, json=_ok(data, trace_id))

    if path == "/api/v1/data/ingest":
        data = {
            "assetId": "asset_test0001",
            "source": "meter-simulator",
            "status": "REGISTERED",
            "meterCount": 1,
            "traceId": trace_id,
        }
        return httpx.Response(200, json=_ok(data, trace_id))

    if path == "/api/v1/auth/requests":
        data = {
            "authorizationId": "auth_test0001",
            "participants": [],
            "authorized": True,
            "status": "AUTHORIZED",
            "traceId": trace_id,
        }
        return httpx.Response(200, json=_ok(data, trace_id))

    if path == "/api/v1/fl/tasks":
        data = {
            "globalModelVersion": "global_model_v1",
            "rounds": 2,
            "assetId": "asset_test0001",
            "accuracy": 0.96,
            "status": "MODEL_READY",
            "traceId": trace_id,
        }
        return httpx.Response(200, json=_ok(data, trace_id))

    if path == "/api/v1/privacy/secure-aggregate":
        data = {
            "taskId": "aggregate_test0001",
            "modelVersion": "global_model_v1",
            "algorithm": "secure-aggregation",
            "status": "COMPLETED",
            "traceId": trace_id,
        }
        return httpx.Response(200, json=_ok(data, trace_id))

    if path == "/api/v1/ledger/events":
        data = {
            "eventId": "evt_test0001",
            "assetId": "asset_test0001",
            "recordStatus": "CONFIRMED",
            "traceId": trace_id,
        }
        return httpx.Response(200, json=_ok(data, trace_id))

    if path == "/api/v1/agent/audit-report":
        data = {
            "agentReportId": "report_test0001",
            "modelVersion": "global_model_v1",
            "recommendation": "day-ahead trading optimization",
            "status": "AGENT_COMPLETED",
            "traceId": trace_id,
        }
        return httpx.Response(200, json=_ok(data, trace_id))

    return httpx.Response(404, json=_ok({"error": "not found"}, trace_id))


def build_workflow(**overrides) -> DemoWorkflow:
    """Build a DemoWorkflow whose clients use httpx.MockTransport."""
    def _default(cls):
        return cls(transport=httpx.MockTransport(downstream_handler))

    clients = {
        "meter": _default(MeterClient),
        "ingestion": _default(IngestionClient),
        "identity": _default(IdentityClient),
        "fl": _default(FLClient),
        "privacy": _default(PrivacyClient),
        "ledger": _default(LedgerClient),
        "agent": _default(AgentClient),
    }
    clients.update(overrides)
    return DemoWorkflow(**clients)


@pytest.fixture
def app_workflow(monkeypatch):
    """Replace the app-level workflow with a MockTransport-backed one."""
    import api_gateway.api as api_module

    workflow = build_workflow()
    monkeypatch.setattr(api_module, "workflow", workflow)
    return workflow