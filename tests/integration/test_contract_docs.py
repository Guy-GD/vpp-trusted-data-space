import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GATEWAY_ONLY_POLICY = (
    "第一周仅 `api-gateway` 负责跨模块编排和调用 `ledger-service`；"
    "其他业务模块不得直接调用 `ledger-service`。"
)
BACKEND_MODULES = {
    "api-gateway",
    "meter-simulator",
    "data-ingestion",
    "identity-did",
    "federated-learning",
    "privacy-compute",
    "ledger-service",
    "ai-agent",
}
STANDARD_HTTP_METHODS = {
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "HEAD",
    "OPTIONS",
    "TRACE",
    "CONNECT",
}


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


def endpoint_section(text: str, endpoint: str) -> str:
    match = re.search(
        rf"^### `{re.escape(endpoint)}`\n(.*?)(?=^### `|^## |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match, f"missing endpoint section: {endpoint}"
    return match.group(0)


def json_after_label(section: str, label: str) -> dict:
    match = re.search(
        rf"{re.escape(label)}\n\n```json\n(.*?)\n```",
        section,
        flags=re.DOTALL,
    )
    assert match, f"missing JSON example after {label!r}"
    return json.loads(match.group(1))


def external_interface_http_block(module_section: str) -> str:
    match = re.search(
        r"^### 对外接口\n\n```http\n(.*?)\n```",
        module_section,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match, "missing HTTP block immediately after the external-interface heading"
    return match.group(1)


def parse_http_endpoints(http_block: str) -> list[tuple[str, str]]:
    return re.findall(r"^([A-Z]+) (\S+)$", http_block, re.MULTILINE)


def assert_required_fields(value: dict, fields: tuple[str, ...]) -> None:
    assert isinstance(value, dict)
    for field in fields:
        assert field in value


def test_gateway_is_the_only_week_one_cross_module_orchestrator():
    flow = read("docs/design/main-flow.md")
    contracts = read("docs/design/module-contracts.md")

    assert GATEWAY_ONLY_POLICY in flow
    assert GATEWAY_ONLY_POLICY in contracts
    assert "FL->>Privacy" not in flow
    assert "FL->>Ledger" not in flow
    assert "GW->>Privacy: POST /api/v1/privacy/secure-aggregate" in flow
    assert "GW->>Ledger: secure_aggregation_finished" in flow


def test_fl_start_response_json_contains_current_round_updates():
    start = endpoint_section(
        read("docs/api/openapi.md"),
        "POST /api/v1/fl/tasks/{taskId}/start",
    )
    data = json_after_label(start, "成功 `data`：")

    assert isinstance(data["updates"], list)
    assert data["updates"]
    assert_required_fields(
        data["updates"][0],
        ("participantDid", "sampleCount", "modelUpdateUri", "updateHash"),
    )


def test_privacy_secure_aggregate_request_and_response_json_are_directional():
    aggregate = endpoint_section(
        read("docs/api/openapi.md"),
        "POST /api/v1/privacy/secure-aggregate",
    )
    request = json_after_label(aggregate, "请求：")
    response = json_after_label(aggregate, "成功 `data`：")

    assert_required_fields(request, ("trainingTaskId", "roundId", "updates", "privacyMode"))
    assert isinstance(request["updates"], list)
    assert request["updates"]
    assert_required_fields(
        request["updates"][0],
        ("participantDid", "sampleCount", "modelUpdateUri", "updateHash"),
    )
    assert_required_fields(response, ("aggregateId", "aggregateResultUri", "aggregateHash"))


def test_fl_aggregate_request_json_receives_privacy_result_before_fedavg():
    aggregate = endpoint_section(
        read("docs/api/openapi.md"),
        "POST /api/v1/fl/tasks/{taskId}/rounds/{roundId}/aggregate",
    )
    request = json_after_label(aggregate, "请求：")

    assert_required_fields(request, ("aggregateId", "aggregateResultUri", "aggregateHash"))
    assert "FedAvg" in aggregate


def test_data_ingest_is_the_main_flow_while_asset_registration_stays_separate():
    openapi = read("docs/api/openapi.md")
    flow = read("docs/design/main-flow.md")
    contracts = read("docs/design/module-contracts.md")
    ingest = endpoint_section(openapi, "POST /api/v1/data/ingest")
    assets = endpoint_section(openapi, "POST /api/v1/data/assets")

    assert "GW->>Ingest: POST /api/v1/data/ingest" in flow
    assert "Ingest-->>GW: assetId" in flow
    assert "assetId" in ingest
    assert "第一周一键演示主流程" in assets
    assert "POST /api/v1/data/ingest" in numbered_section(contracts, 6)
    assert "POST /api/v1/data/assets" in numbered_section(contracts, 6)


def test_demo_data_json_and_module_contract_example_exclude_common_envelope():
    openapi = read("docs/api/openapi.md")
    contracts = read("docs/design/module-contracts.md")
    demo = endpoint_section(openapi, "POST /api/v1/demo/run")
    data = json_after_label(demo, "成功 `data`：")
    module_data = json_after_label(numbered_section(contracts, 3), "返回示例：")

    required = (
        "businessId",
        "metrics",
        "predictionId",
        "strategyId",
        "auditReportId",
        "ledgerTxIds",
    )
    assert_required_fields(data, required)
    assert_required_fields(module_data, required)
    for example in (data, module_data):
        assert "traceId" not in example
        assert "code" not in example
        assert "message" not in example
        assert "data" not in example
    assert "公共包络" in demo
    assert "response-and-errors.md" in contracts


def test_agent_audit_request_json_uses_gateway_supplied_ledger_evidence():
    openapi = read("docs/api/openapi.md")
    flow = read("docs/design/main-flow.md")
    agent_contract = numbered_section(read("docs/design/module-contracts.md"), 11)
    question = endpoint_section(openapi, "POST /api/v1/agent/audit-question")
    report = endpoint_section(openapi, "POST /api/v1/agent/audit-report")
    question_request = json_after_label(question, "请求：")
    report_request = json_after_label(report, "请求：")

    assert_required_fields(
        question_request,
        ("businessId", "modelVersion", "evidenceEventIds", "question"),
    )
    assert_required_fields(
        report_request,
        ("businessId", "modelVersion", "evidenceEventIds", "reportType"),
    )
    assert isinstance(question_request["evidenceEventIds"], list)
    assert isinstance(report_request["evidenceEventIds"], list)
    assert "网关查询账本后提供" in question
    assert "网关查询账本后提供" in report
    assert "网关提供的 `evidenceEventIds`" in agent_contract
    assert "不直接调用账本服务" in agent_contract
    assert "网关查询账本证据链后提供 `evidenceEventIds`" in flow


def test_http_endpoint_parser_accepts_all_standard_methods():
    block = "\n".join(f"{method} /example" for method in sorted(STANDARD_HTTP_METHODS))
    assert {method for method, _ in parse_http_endpoints(block)} == STANDARD_HTTP_METHODS


def test_openapi_coverage_matrix_matches_each_backend_external_interface():
    openapi = read("docs/api/openapi.md")
    contracts = read("docs/design/module-contracts.md")
    matrix = numbered_section(openapi, 3)
    matrix_rows = re.findall(
        r"^\|\s*([^|]+?)\s*\|\s*([A-Z]+)\s*\|\s*`([^`]+)`\s*\|$",
        matrix,
        flags=re.MULTILINE,
    )
    matrix_modules = {module for module, _, _ in matrix_rows}
    expected_modules = BACKEND_MODULES | {"所有服务"}

    assert matrix_modules == expected_modules
    assert len(matrix_rows) == len(set(matrix_rows))
    assert all(method in STANDARD_HTTP_METHODS for _, method, _ in matrix_rows)
    assert {
        (method, path)
        for module, method, path in matrix_rows
        if module == "所有服务"
    } == {("GET", "/health")}

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
    for module, section in module_sections.items():
        external_rows = parse_http_endpoints(external_interface_http_block(section))
        assert len(external_rows) == len(set(external_rows))
        assert all(method in STANDARD_HTTP_METHODS for method, _ in external_rows)
        assert set(external_rows) == {
            (method, path)
            for matrix_module, method, path in matrix_rows
            if matrix_module == module
        } | {("GET", "/health")}
