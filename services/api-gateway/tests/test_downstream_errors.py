import httpx
from fastapi.testclient import TestClient

from conftest import build_workflow
from api_gateway.clients.meter import MeterClient
from api_gateway.main import app
import api_gateway.api as api_module

PAYLOAD = {
    "scenario": "vpp_day_ahead_trading",
    "participants": ["aggregator-A"],
    "meterCount": 1,
    "trainingRounds": 1,
}


def _timeout_handler(request: httpx.Request) -> httpx.Response:
    raise httpx.ReadTimeout("downstream timed out")


def _unavailable_handler(request: httpx.Request) -> httpx.Response:
    raise httpx.ConnectError("connection refused")


def _install(workflow, monkeypatch):
    monkeypatch.setattr(api_module, "workflow", workflow)


def test_downstream_timeout_returns_50401(monkeypatch):
    failing = MeterClient(transport=httpx.MockTransport(_timeout_handler))
    _install(build_workflow(meter=failing), monkeypatch)

    client = TestClient(app)
    response = client.post("/api/v1/demo/run", json=PAYLOAD)

    assert response.status_code == 504
    body = response.json()
    assert body["code"] == 50401


def test_downstream_unavailable_returns_50203(monkeypatch):
    failing = MeterClient(transport=httpx.MockTransport(_unavailable_handler))
    _install(build_workflow(meter=failing), monkeypatch)

    client = TestClient(app)
    response = client.post("/api/v1/demo/run", json=PAYLOAD)

    assert response.status_code == 502
    body = response.json()
    assert body["code"] == 50203