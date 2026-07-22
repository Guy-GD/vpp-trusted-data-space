from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]


def test_dockerfile_installs_repo_packages_and_runs_non_root() -> None:
    dockerfile = (SERVICE_ROOT / "Dockerfile").read_text(encoding="utf-8")

    for required in (
        "FROM python:3.11-slim",
        "COPY packages/common /app/packages/common",
        "COPY services/identity-did /app/services/identity-did",
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


def test_demo_uses_seeded_dids_and_external_http_service() -> None:
    demo = (SERVICE_ROOT / "scripts" / "demo.py").read_text(encoding="utf-8")

    compile(demo, str(SERVICE_ROOT / "scripts" / "demo.py"), "exec")
    assert "did:vpp:operator:001" in demo
    assert "did:vpp:load-aggregator:001" in demo
    assert "IDENTITY_DID_BASE_URL" in demo
    assert "IDENTITY_DID_TIMEOUT" in demo
    assert "uuid4" in demo
    assert "trust_env=False" in demo
    assert "TestClient" not in demo
    assert "from " + "app" not in demo
