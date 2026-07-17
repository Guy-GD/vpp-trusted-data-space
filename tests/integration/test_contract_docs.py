import json
import re
from pathlib import Path

from vpp_common.errors import ERROR_MESSAGES, ErrorCode


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
FROZEN_ENDPOINTS = {
    ("api-gateway", "POST", "/api/v1/demo/run"),
    ("api-gateway", "GET", "/api/v1/demo/status/{businessId}"),
    ("meter-simulator", "POST", "/api/v1/meter/readings/generate"),
    ("data-ingestion", "POST", "/api/v1/data/ingest"),
    ("data-ingestion", "POST", "/api/v1/data/assets"),
    ("data-ingestion", "GET", "/api/v1/data/assets/{assetId}"),
    ("identity-did", "POST", "/api/v1/identity/subjects"),
    ("identity-did", "POST", "/api/v1/identity/devices"),
    ("identity-did", "POST", "/api/v1/identity/verify"),
    ("identity-did", "POST", "/api/v1/auth/requests"),
    ("identity-did", "POST", "/api/v1/auth/requests/{authId}/approve"),
    ("identity-did", "GET", "/api/v1/auth/requests/{authId}"),
    ("federated-learning", "POST", "/api/v1/fl/tasks"),
    ("federated-learning", "POST", "/api/v1/fl/tasks/{taskId}/start"),
    (
        "federated-learning",
        "POST",
        "/api/v1/fl/tasks/{taskId}/rounds/{roundId}/updates",
    ),
    (
        "federated-learning",
        "POST",
        "/api/v1/fl/tasks/{taskId}/rounds/{roundId}/aggregate",
    ),
    ("federated-learning", "GET", "/api/v1/fl/tasks/{taskId}"),
    ("federated-learning", "GET", "/api/v1/fl/tasks/{taskId}/metrics"),
    ("federated-learning", "GET", "/api/v1/fl/models/{modelVersion}"),
    ("privacy-compute", "POST", "/api/v1/privacy/model-updates/encrypt"),
    ("privacy-compute", "POST", "/api/v1/privacy/model-updates/mask"),
    ("privacy-compute", "POST", "/api/v1/privacy/secure-aggregate"),
    ("privacy-compute", "GET", "/api/v1/privacy/aggregates/{aggregateId}"),
    ("ledger-service", "POST", "/api/v1/ledger/events"),
    ("ledger-service", "GET", "/api/v1/ledger/events/{eventId}"),
    ("ledger-service", "GET", "/api/v1/ledger/traces/{businessId}"),
    ("ai-agent", "POST", "/api/v1/agent/predict"),
    ("ai-agent", "POST", "/api/v1/agent/trading-strategy"),
    ("ai-agent", "POST", "/api/v1/agent/audit-question"),
    ("ai-agent", "POST", "/api/v1/agent/audit-report"),
    ("所有服务", "GET", "/health"),
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
ENDPOINT_REQUIREMENT_MARKERS = (
    "**请求说明**：",
    "**字段类型与必填性**：",
    "**成功说明**：",
    "**可能错误**：",
    "**幂等规则**：",
)
FORMAL_UTF8_FILES = (
    "README.md",
    "docs/api/openapi.md",
    "docs/api/response-and-errors.md",
    "docs/design/main-flow.md",
    "docs/design/module-contracts.md",
    "docs/design/week-one-mock-delivery.md",
    "packages/common/README.md",
    "packages/common/pyproject.toml",
    "packages/common/src/vpp_common/__init__.py",
    "packages/common/src/vpp_common/errors.py",
    "packages/common/src/vpp_common/fastapi_support.py",
    "packages/common/src/vpp_common/response.py",
    "packages/common/src/vpp_common/schemas.py",
    "packages/common/tests/test_fastapi_support.py",
    "packages/common/tests/test_response.py",
    "tests/integration/test_contract_docs.py",
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
        rf"^{re.escape(label)}\n\n```json\n(.*?)\n```",
        section,
        flags=re.MULTILINE | re.DOTALL,
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


def coverage_matrix_rows(text: str) -> list[tuple[str, str, str]]:
    return re.findall(
        r"^\|\s*([^|]+?)\s*\|\s*([A-Z]+)\s*\|\s*`([^`]+)`\s*\|$",
        numbered_section(text, 3),
        flags=re.MULTILINE,
    )


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


def test_fl_round_handoff_and_path_ids_are_frozen_in_openapi_json():
    openapi = read("docs/api/openapi.md")
    start = endpoint_section(openapi, "POST /api/v1/fl/tasks/{taskId}/start")
    update = endpoint_section(
        openapi,
        "POST /api/v1/fl/tasks/{taskId}/rounds/{roundId}/updates",
    )
    aggregate = endpoint_section(
        openapi,
        "POST /api/v1/fl/tasks/{taskId}/rounds/{roundId}/aggregate",
    )

    start_data = json_after_label(start, "成功 `data`：")
    update_request = json_after_label(update, "请求：")
    aggregate_request = json_after_label(aggregate, "请求：")
    running = json_after_label(aggregate, "非最终轮成功 `data`：")
    completed = json_after_label(aggregate, "最终轮成功 `data`：")

    assert "无请求体" in start
    assert "`taskId` 仅来自路径" in start
    assert start_data["currentRound"] == 1
    assert start_data["updates"]
    assert set(update_request) == {
        "participantDid",
        "sampleCount",
        "modelUpdateUri",
        "updateHash",
    }
    assert set(aggregate_request) == {
        "aggregateId",
        "aggregateResultUri",
        "aggregateHash",
    }
    assert running["status"] == "running"
    assert isinstance(running["nextRound"], int)
    assert running["updates"]
    assert_required_fields(
        running["updates"][0],
        ("participantDid", "sampleCount", "modelUpdateUri", "updateHash"),
    )
    assert completed["status"] == "completed"
    assert completed["nextRound"] is None
    assert completed["updates"] == []
    assert_required_fields(
        completed,
        ("globalModelVersion", "modelHash", "metrics"),
    )


def test_fl_round_handoff_is_synchronized_across_design_documents():
    flow = numbered_section(read("docs/design/main-flow.md"), 4)
    contracts = numbered_section(read("docs/design/module-contracts.md"), 8)

    update_request = json_after_label(contracts, "本地参数上传请求：")
    aggregate_request = json_after_label(contracts, "FedAvg 聚合请求：")
    running = json_after_label(contracts, "非最终轮聚合输出：")
    completed = json_after_label(contracts, "最终轮聚合输出：")

    assert "每轮" in flow
    assert "status: running" in flow
    assert "nextRound" in flow
    assert "status: completed" in flow
    assert "nextRound: null" in flow
    assert set(update_request) == {
        "participantDid",
        "sampleCount",
        "modelUpdateUri",
        "updateHash",
    }
    assert set(aggregate_request) == {
        "aggregateId",
        "aggregateResultUri",
        "aggregateHash",
    }
    assert running["status"] == "running"
    assert isinstance(running["nextRound"], int)
    assert running["updates"]
    assert completed["status"] == "completed"
    assert completed["nextRound"] is None
    assert completed["updates"] == []


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


def test_key_demo_and_agent_examples_are_parseable_json():
    openapi = read("docs/api/openapi.md")
    demo = endpoint_section(openapi, "POST /api/v1/demo/run")
    predict = endpoint_section(openapi, "POST /api/v1/agent/predict")
    strategy = endpoint_section(openapi, "POST /api/v1/agent/trading-strategy")
    question = endpoint_section(openapi, "POST /api/v1/agent/audit-question")
    report = endpoint_section(openapi, "POST /api/v1/agent/audit-report")

    examples = (
        json_after_label(demo, "请求："),
        json_after_label(demo, "成功 `data`："),
        json_after_label(predict, "请求："),
        json_after_label(predict, "成功 `data`："),
        json_after_label(strategy, "请求："),
        json_after_label(strategy, "成功 `data`："),
        json_after_label(question, "请求："),
        json_after_label(question, "成功 `data`："),
        json_after_label(report, "请求："),
        json_after_label(report, "成功 `data`："),
    )

    assert all(isinstance(example, dict) and example for example in examples)


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


def test_openapi_matrix_and_endpoint_h3_sections_match_bidirectionally():
    openapi = read("docs/api/openapi.md")
    matrix_rows = coverage_matrix_rows(openapi)
    matrix_endpoints = {(method, path) for _, method, path in matrix_rows}
    h3_endpoints = re.findall(
        r"^### `([A-Z]+) ([^`]+)`$",
        openapi,
        flags=re.MULTILINE,
    )

    assert len(h3_endpoints) == len(set(h3_endpoints))
    assert set(h3_endpoints) == matrix_endpoints


def test_every_openapi_endpoint_has_complete_implementation_contract():
    openapi = read("docs/api/openapi.md")
    for _, method, path in coverage_matrix_rows(openapi):
        endpoint = f"{method} {path}"
        section = endpoint_section(openapi, endpoint)
        for marker in ENDPOINT_REQUIREMENT_MARKERS:
            assert marker in section, f"{endpoint} missing {marker}"
        fields = re.search(
            r"^\*\*字段类型与必填性\*\*：(.*)$",
            section,
            flags=re.MULTILINE,
        )
        assert fields
        assert "必填" in fields.group(1) or "无请求字段" in fields.group(1)
        assert "请求体" in section
        assert re.search(r"^\*\*成功说明\*\*：.*`data`", section, re.MULTILINE)
        if method == "GET":
            assert "无请求体" in section, f"{endpoint} must declare no request body"
            assert "不适用" in section, f"{endpoint} must declare idempotency inapplicable"
        else:
            assert "Idempotency-Key" in section, f"{endpoint} missing write idempotency rule"
        assert "response-and-errors.md" in section, f"{endpoint} must reference common errors"


def test_openapi_coverage_matrix_matches_each_backend_external_interface():
    openapi = read("docs/api/openapi.md")
    contracts = read("docs/design/module-contracts.md")
    matrix = numbered_section(openapi, 3)
    matrix_rows = coverage_matrix_rows(openapi)
    matrix_modules = {module for module, _, _ in matrix_rows}
    expected_modules = BACKEND_MODULES | {"所有服务"}

    assert len(FROZEN_ENDPOINTS) == 31
    assert set(matrix_rows) == FROZEN_ENDPOINTS
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


def test_public_response_document_matches_actual_frozen_key_sets():
    response_doc = read("docs/api/response-and-errors.md")
    success_section = numbered_section(response_doc, 2)
    failure_section = numbered_section(response_doc, 3)
    success_example = json_after_label(success_section, "成功响应示例：")
    failure_example = json_after_label(failure_section, "失败响应示例：")

    assert "requestId" not in response_doc
    assert set(success_example) == {
        "code",
        "message",
        "data",
        "traceId",
        "timestamp",
    }
    assert set(failure_example) == {
        "code",
        "message",
        "data",
        "traceId",
        "timestamp",
        "details",
    }
    assert re.search(r"\| `timestamp` \| string \| 是 \|", success_section)
    assert "仅在存在字段级详情时返回 `details`" in failure_section


def test_failure_http_usage_boundary_is_frozen_in_public_docs():
    readme = read("packages/common/README.md")
    response_doc = read("docs/api/response-and-errors.md")

    for document in (readme, response_doc):
        assert "异常处理器/非 HTTP 场景的包络构造器" in document
        assert "禁止在 FastAPI 路由中直接 `return failure(...)`" in document
        assert "raise ServiceError(code, details=...)" in document


def test_documented_error_catalog_exactly_matches_public_package():
    response_doc = numbered_section(read("docs/api/response-and-errors.md"), 5)
    rows = re.findall(
        r"^\| `(\d{5})` \| `([^`]+)` \|",
        response_doc,
        flags=re.MULTILINE,
    )
    documented = {int(code): message for code, message in rows}
    expected = {int(code): message for code, message in ERROR_MESSAGES.items()}

    assert len(rows) == len(documented) == len(ErrorCode) == 34
    assert documented == expected


def test_openapi_change_rules_require_common_error_reference_not_failure_example():
    rules = numbered_section(read("docs/api/openapi.md"), 13)

    assert "每个接口必须有“可能错误”" in rules
    assert "引用公共错误目录" in rules
    assert "失败示例" not in rules


def test_common_package_contract_excludes_module_specific_and_security_helpers():
    common = numbered_section(read("docs/design/module-contracts.md"), 13)

    for responsibility in (
        "统一响应",
        "错误码",
        "traceId",
        "UTC 时间",
        "冻结 ID",
        "HealthData",
        "ErrorDetail",
    ):
        assert responsibility in common
    for excluded in ("模块专属 DTO", "哈希", "签名", "加密", "业务工具"):
        assert excluded in common
    assert "不属于公共包" in common
    assert "源端可信采集" in common
    assert "hashing.py" not in common
    assert "通用 DTO/Schema" not in common


def test_week_one_contract_ambiguities_are_recorded_as_completed_decisions():
    week_one = read("docs/design/week-one-mock-delivery.md")

    assert "### 3.1 已冻结决策与完成状态" in week_one
    assert "Day 1 必须消除的契约歧义" not in week_one
    assert "当前接口文档存在以下联调歧义" not in week_one
    assert "`traceId` 只存在于公共响应包络" in week_one


def test_formal_files_are_utf8_without_bom_and_repository_freezes_lf():
    attributes = ROOT / ".gitattributes"
    assert attributes.exists(), "missing .gitattributes"
    attributes_text = attributes.read_text(encoding="utf-8")
    assert "* text=auto eol=lf" in attributes_text

    for relative_path in FORMAL_UTF8_FILES + (".gitattributes",):
        raw = (ROOT / relative_path).read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), f"UTF-8 BOM: {relative_path}"
        raw.decode("utf-8", errors="strict")
        assert b"\r\n" not in raw, f"CRLF: {relative_path}"
