import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GATEWAY_ONLY_POLICY = (
    "第一周仅 `api-gateway` 负责跨模块编排和调用 `ledger-service`；"
    "其他业务模块不得直接调用 `ledger-service`。"
)


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def numbered_section(text: str, number: int) -> str:
    match = re.search(
        rf"^## {number}\..*?(?=^## {number + 1}\.|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match, f"missing section {number}"
    return match.group(0)


def endpoint_section(text: str, start: str, end: str) -> str:
    return text.split(start, 1)[1].split(end, 1)[0]


def public_endpoints(module_section: str) -> set[tuple[str, str]]:
    match = re.search(
        r"### .*?\n\n```http\n(.*?)\n```",
        module_section,
        flags=re.DOTALL,
    )
    assert match, "missing external-interface HTTP block"
    return {
        (method, path)
        for method, path in re.findall(r"^(GET|POST) (/.+)$", match.group(1), re.MULTILINE)
    }


def test_gateway_is_the_only_week_one_cross_module_orchestrator():
    flow = read("docs/design/main-flow.md")
    contracts = read("docs/design/module-contracts.md")

    assert GATEWAY_ONLY_POLICY in flow
    assert GATEWAY_ONLY_POLICY in contracts
    assert "FL->>Privacy" not in flow
    assert "FL->>Ledger" not in flow
    assert "GW->>Privacy: POST /api/v1/privacy/secure-aggregate" in flow
    assert "GW->>Ledger: secure_aggregation_finished" in flow


def test_fl_start_returns_the_current_round_updates_with_all_required_fields():
    openapi = read("docs/api/openapi.md")
    contracts = read("docs/design/module-contracts.md")
    start = endpoint_section(
        openapi,
        "### `POST /api/v1/fl/tasks/{taskId}/start`",
        "### `POST /api/v1/fl/tasks/{taskId}/rounds/{roundId}/updates`",
    )
    fl_contract = numbered_section(contracts, 8)

    for text in (start, fl_contract):
        for field in ("updates", "participantDid", "sampleCount", "modelUpdateUri", "updateHash"):
            assert field in text


def test_gateway_hands_updates_to_privacy_compute_and_receives_aggregate_handoff():
    openapi = read("docs/api/openapi.md")
    flow = read("docs/design/main-flow.md")
    contracts = read("docs/design/module-contracts.md")
    aggregate = endpoint_section(
        openapi,
        "### `POST /api/v1/privacy/secure-aggregate`",
        "### `GET /api/v1/privacy/aggregates/{aggregateId}`",
    )

    assert "GW->>Privacy: POST /api/v1/privacy/secure-aggregate" in flow
    assert "Privacy-->>GW: aggregateId + aggregateResultUri + aggregateHash" in flow
    for text in (aggregate, numbered_section(contracts, 9)):
        for field in ("updates", "aggregateId", "aggregateResultUri", "aggregateHash"):
            assert field in text


def test_fl_aggregate_accepts_the_privacy_result_before_running_fedavg():
    openapi = read("docs/api/openapi.md")
    contracts = read("docs/design/module-contracts.md")
    aggregate = endpoint_section(
        openapi,
        "### `POST /api/v1/fl/tasks/{taskId}/rounds/{roundId}/aggregate`",
        "### `GET /api/v1/fl/tasks/{taskId}`",
    )
    fl_contract = numbered_section(contracts, 8)

    for text in (aggregate, fl_contract):
        for field in ("aggregateId", "aggregateResultUri", "aggregateHash"):
            assert field in text
        assert "FedAvg" in text


def test_data_ingest_is_the_main_flow_while_asset_registration_stays_separate():
    openapi = read("docs/api/openapi.md")
    flow = read("docs/design/main-flow.md")
    contracts = read("docs/design/module-contracts.md")
    ingest = endpoint_section(
        openapi,
        "### `POST /api/v1/data/ingest`",
        "### `POST /api/v1/data/assets`",
    )
    assets = endpoint_section(
        openapi,
        "### `POST /api/v1/data/assets`",
        "### `GET /api/v1/data/assets/{assetId}`",
    )

    assert "GW->>Ingest: POST /api/v1/data/ingest" in flow
    assert "Ingest-->>GW: assetId" in flow
    assert "assetId" in ingest
    assert "第一周一键演示主流程" in assets
    assert "POST /api/v1/data/ingest" in numbered_section(contracts, 6)
    assert "POST /api/v1/data/assets" in numbered_section(contracts, 6)


def test_demo_data_and_the_common_envelope_keep_trace_id_separate():
    openapi = read("docs/api/openapi.md")
    demo = endpoint_section(
        openapi,
        "### `POST /api/v1/demo/run`",
        "### `GET /api/v1/demo/status/{businessId}`",
    )
    match = re.search(r"成功 `data`：\n\n```json\n(.*?)\n```", demo, re.DOTALL)
    assert match, "missing demo success data example"
    data = json.loads(match.group(1))

    for field in (
        "businessId",
        "metrics",
        "predictionId",
        "strategyId",
        "auditReportId",
        "ledgerTxIds",
    ):
        assert field in data
    assert "traceId" not in data
    assert "公共包络" in demo
    assert "traceId" in demo


def test_agent_audit_requests_use_gateway_supplied_ledger_evidence():
    openapi = read("docs/api/openapi.md")
    flow = read("docs/design/main-flow.md")
    agent_contract = numbered_section(read("docs/design/module-contracts.md"), 11)
    question = endpoint_section(
        openapi,
        "### `POST /api/v1/agent/audit-question`",
        "### `POST /api/v1/agent/audit-report`",
    )
    report = endpoint_section(
        openapi,
        "### `POST /api/v1/agent/audit-report`",
        "## 12.",
    )

    for text, unique_field in ((question, "question"), (report, "reportType")):
        for field in ("businessId", "modelVersion", "evidenceEventIds", unique_field):
            assert field in text
        assert "网关查询账本后提供" in text
    assert "网关提供的 `evidenceEventIds`" in agent_contract
    assert "不直接调用账本服务" in agent_contract
    assert "网关查询账本证据链后提供 `evidenceEventIds`" in flow


def test_openapi_coverage_matrix_matches_every_module_external_interface():
    openapi = read("docs/api/openapi.md")
    contracts = read("docs/design/module-contracts.md")
    matrix = numbered_section(openapi, 3)
    matrix_endpoints = {
        (module, method, path)
        for module, method, path in re.findall(
            r"^\|\s*([^|]+?)\s*\|\s*(GET|POST)\s*\|\s*`([^`]+)`\s*\|$",
            matrix,
            flags=re.MULTILINE,
        )
    }
    module_sections = {
        "api-gateway": numbered_section(contracts, 4),
        "meter-simulator": numbered_section(contracts, 5),
        "data-ingestion": numbered_section(contracts, 6),
        "identity-did": numbered_section(contracts, 7),
        "federated-learning": numbered_section(contracts, 8),
        "privacy-compute": numbered_section(contracts, 9),
        "ledger-service": numbered_section(contracts, 10),
        "ai-agent": numbered_section(contracts, 11),
    }

    assert ("所有服务", "GET", "/health") in matrix_endpoints
    for module, section in module_sections.items():
        expected = {
            (method, path)
            for matrix_module, method, path in matrix_endpoints
            if matrix_module == module
        }
        expected.add(("GET", "/health"))
        assert public_endpoints(section) == expected
