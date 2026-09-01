import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import httpx
import pytest


SERVICE_ROOT = Path(__file__).resolve().parents[1]
DEMO_PATH = SERVICE_ROOT / "scripts" / "demo.py"


@pytest.fixture
def demo() -> ModuleType:
    spec = importlib.util.spec_from_file_location("identity_did_demo", DEMO_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dockerfile_copies_only_runtime_package_files() -> None:
    dockerfile = (SERVICE_ROOT / "Dockerfile").read_text(encoding="utf-8")
    copy_sources = {
        line.split()[1]
        for line in dockerfile.splitlines()
        if line.strip().startswith("COPY ")
    }

    assert copy_sources == {
        "packages/common/pyproject.toml",
        "packages/common/README.md",
        "packages/common/src",
        "services/identity-did/pyproject.toml",
        "services/identity-did/src",
    }
    for required in (
        "FROM python:3.11-slim",
        "-e /app/packages/common",
        "-e /app/services/identity-did",
        "USER appuser",
        "EXPOSE 8000",
        '"identity_did.main:app"',
        '"--port", "8000"',
    ):
        assert required in dockerfile


def test_readme_contains_repeatable_week_one_commands_and_contract() -> None:
    readme = (SERVICE_ROOT / "README.md").read_text(encoding="utf-8")

    for required in (
        'python -m pip install -e packages/common -e "services/identity-did[test]"',
        "python -m uvicorn identity_did.main:app --reload --port 8003",
        "python -m pytest services/identity-did/tests -v",
        "docker build -f services/identity-did/Dockerfile -t vpp/identity-did:week1 .",
        "docker run --rm -p 8003:8000 vpp/identity-did:week1",
        "did:vpp:operator:001",
        "did:vpp:load-aggregator:001",
        "did:vpp:renewable-plant:001",
        "did:vpp:storage:001",
        "bW9jay1wdWJsaWMta2V5",
        "四个预置主体共用同一个 Mock 公钥字符串",
        "不要先进行 Base64 解码",
        '":" + payloadHash',
        "SHA-256",
        "公开的联调约定",
        "不是秘密、私钥或生产凭据",
        "40102",
        "40303",
        "40401",
        "40901",
        "40902",
        "Mock-only",
    ):
        assert required in readme

    assert "py -" + "3.12" not in readme
    assert "app.main:app" not in readme


def test_demo_runs_create_approve_get_with_seeded_callers(
    demo: ModuleType,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content) if request.content else None
        calls.append(
            {
                "method": request.method,
                "path": request.url.path,
                "body": body,
                "headers": request.headers,
            }
        )
        status = "requested" if len(calls) == 1 else "approved"
        return httpx.Response(
            200,
            json={
                "code": 0,
                "message": "ok",
                "data": {"authId": "auth_demo", "status": status},
                "traceId": f"trace_{len(calls)}",
            },
        )

    with httpx.Client(
        base_url="http://identity-did.test",
        transport=httpx.MockTransport(handler),
    ) as client:
        demo.run_demo(
            client,
            run_id="test-run",
            expire_at="2099-01-01T00:00:00+00:00",
        )

    assert [(call["method"], call["path"]) for call in calls] == [
        ("POST", "/api/v1/auth/requests"),
        ("POST", "/api/v1/auth/requests/auth_demo/approve"),
        ("GET", "/api/v1/auth/requests/auth_demo"),
    ]
    assert calls[0]["body"]["requesterDid"] == "did:vpp:operator:001"
    assert calls[0]["body"]["ownerDid"] == "did:vpp:load-aggregator:001"
    assert calls[0]["headers"]["X-Caller-Did"] == "did:vpp:operator:001"
    assert calls[1]["headers"]["X-Caller-Did"] == (
        "did:vpp:load-aggregator:001"
    )
    assert calls[0]["headers"]["Idempotency-Key"] == "demo-create-test-run"
    assert calls[1]["headers"]["Idempotency-Key"] == "demo-approve-test-run"

    output = capsys.readouterr().out
    assert '"authId": "auth_demo"' in output
    assert '"code"' not in output
    assert '"message"' not in output
    assert '"traceId"' not in output


def test_demo_reports_public_error_envelope_with_request_url(
    demo: ModuleType,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            409,
            json={
                "code": 40901,
                "message": "idempotency conflict",
                "data": None,
                "traceId": "trace_conflict",
            },
        )

    with httpx.Client(
        base_url="http://identity-did.test",
        transport=httpx.MockTransport(handler),
    ) as client:
        with pytest.raises(demo.DemoError) as caught:
            demo.run_demo(
                client,
                run_id="conflict",
                expire_at="2099-01-01T00:00:00+00:00",
            )

    message = str(caught.value)
    assert "http://identity-did.test/api/v1/auth/requests" in message
    assert "40901" in message
    assert "idempotency conflict" in message


def test_demo_rejects_unexpected_business_state(demo: ModuleType) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "code": 0,
                "message": "ok",
                "data": {"authId": "auth_wrong", "status": "approved"},
                "traceId": "trace_wrong",
            },
        )

    with httpx.Client(
        base_url="http://identity-did.test",
        transport=httpx.MockTransport(handler),
    ) as client:
        with pytest.raises(demo.DemoError, match="requested"):
            demo.run_demo(
                client,
                run_id="wrong-state",
                expire_at="2099-01-01T00:00:00+00:00",
            )


def test_main_reports_connection_error_without_traceback(
    demo: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class FailingClient:
        def __enter__(self) -> "FailingClient":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def post(self, path: str, **kwargs: object) -> httpx.Response:
            request = httpx.Request("POST", f"{demo.BASE_URL}{path}")
            raise httpx.ConnectError("connection refused", request=request)

    monkeypatch.setattr(demo.httpx, "Client", lambda **kwargs: FailingClient())

    exit_code = demo.main()

    captured = capsys.readouterr()
    assert exit_code == 1
    assert f"{demo.BASE_URL}/api/v1/auth/requests" in captured.err
    assert "connection refused" in captured.err
    assert "Traceback" not in captured.err
