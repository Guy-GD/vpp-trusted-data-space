# Week One Full-Chain Mock Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a Docker Compose environment in which the Vue frontend triggers a real HTTP-orchestrated Mock flow across eight FastAPI services and displays the complete VPP trust-data-space result.

**Architecture:** Eight independently packaged FastAPI services communicate through HTTP/JSON and share only the installable `vpp_common` Python package. `api-gateway` is the sole cross-module orchestrator and the frontend's only backend dependency; all business persistence is in-memory for week one, while IDs, state transitions, error handling, tracing, idempotency, tests, containers, and service calls are real.

**Tech Stack:** Python 3.11, FastAPI, Pydantic v2, Uvicorn, httpx, pytest, Vue 3, Vite, JavaScript, Element Plus, Axios, Node.js 24 LTS, Docker Compose, GitHub Actions.

## Global Constraints

- Source design: `docs/design/week-one-mock-delivery.md`.
- API source of truth: `docs/api/openapi.md`.
- Unified response and errors: `docs/api/response-and-errors.md`.
- Module boundaries: `docs/design/module-contracts.md`.
- Cross-module flow: `docs/design/main-flow.md`.
- All backends use Python 3.11, FastAPI, Pydantic v2, and Uvicorn.
- The frontend uses Node.js 24 LTS, Vue 3, Vite, JavaScript, Element Plus, and Axios.
- Service communication is HTTP/1.1 with JSON; frontend calls only `api-gateway`.
- Business capabilities may be Mock; HTTP calls, validation, state, IDs, tracing, idempotency, containers, tests, and UI integration must be real.
- No database, production blockchain, MQTT, real cryptography, real federated training, production MPC, or external model API in week one.
- All text files use UTF-8. PowerShell 5 readers must pass `-Encoding UTF8`.
- Do not commit `.env`, credentials, keys, real meter plaintext, unprotected model parameters, or production data.
- Every backend write endpoint consumes `Idempotency-Key` when defined by the contract and every response includes `traceId`.
- A module is not `Done` until its PR is merged and the module has passed integration.

---

## Work Allocation and Issue Map

| Task | GitHub Issue title | Owner | Target day |
|---:|---|---|---:|
| 1 | `[P0][架构] 冻结第一周技术基线与主流程契约` | Technical lead | Day 1 noon |
| 2 | `[P0][公共] 实现 vpp_common 公共包` | Technical lead | Day 1 noon |
| 3 | `[P0][源端采集] 实现 meter-simulator Mock 服务` | meter-simulator owner | Day 3 |
| 4 | `[P0][数据接入] 实现 data-ingestion Mock 服务` | data-ingestion owner | Day 3 |
| 5 | `[P0][DID] 实现 identity-did 与授权 Mock 服务` | identity-did owner | Day 3 |
| 6 | `[P0][联邦学习] 实现训练状态、更新和模型版本 Mock` | federated-learning owner | Day 3 |
| 7 | `[P0][隐私计算] 实现参数保护与安全聚合 Mock` | privacy-compute owner | Day 3 |
| 8 | `[P0][存证] 实现内存哈希链与业务证据链` | ledger-service owner | Day 3 |
| 9 | `[P0][Agent] 实现预测、策略、问答和报告 Mock` | ai-agent owner | Day 3 |
| 10 | `[P0][网关] 实现一键演示编排、状态与集成测试` | api-gateway owner | Day 4 |
| 11 | `[P0][前端] 实现 Vue 一键演示控制台` | web-dashboard owner | Day 5 |
| 12 | `[P0][部署] 实现九服务 Docker Compose` | privacy-compute owner | Day 4 |
| 13 | `[P0][CI] 增加后端测试、前端构建与契约校验` | api-gateway owner | Day 6 |
| 14 | `[P0][测试] 实现全链路 E2E 与失败恢复验证` | api-gateway owner | Day 6 |
| 15 | `[P0][验收] 全新环境彩排并冻结 week1-mock-v0.1.0` | Technical lead | Day 7 |

Detailed copy-ready owner packets are in:

`docs/superpowers/plans/2026-07-16-week-one-owner-issue-packets.md`

## Repository File Map

```text
.editorconfig
.env.example
.nvmrc
.python-version
pyproject.toml                         # optional root pytest configuration only
packages/common/
  pyproject.toml
  README.md
  src/vpp_common/
    __init__.py
    response.py
    errors.py
    fastapi_support.py
    schemas.py
    id_generator.py
    time_utils.py
    tracing.py
  tests/
services/<service>/
  pyproject.toml
  README.md
  Dockerfile
  src/<python_package>/
    __init__.py
    main.py
    api.py
    schemas.py
    repository.py
    service.py
  tests/
apps/web-dashboard/
  package.json
  vite.config.js
  src/
  Dockerfile
  nginx.conf
infra/docker-compose/docker-compose.yml
tests/integration/
tests/e2e/
```

Unique Python package names:

| Service directory | Python package |
|---|---|
| `services/api-gateway` | `api_gateway` |
| `services/meter-simulator` | `meter_simulator` |
| `services/data-ingestion` | `data_ingestion` |
| `services/identity-did` | `identity_did` |
| `services/federated-learning` | `federated_learning` |
| `services/privacy-compute` | `privacy_compute` |
| `services/ledger-service` | `ledger_service` |
| `services/ai-agent` | `ai_agent` |

Do not use a shared top-level Python package named `app`; running all tests from the monorepo root would otherwise import the wrong service.

---

### Task 1: Freeze technical baseline and remove contract ambiguities

**Files:**
- Modify: `docs/api/openapi.md`
- Modify: `docs/design/main-flow.md`
- Modify: `docs/design/module-contracts.md`
- Modify: `docs/design/week-one-mock-delivery.md` only if the approved design needs a consistency correction
- Modify: `README.md`
- Modify: `.gitignore`
- Create: `.python-version`
- Create: `.nvmrc`
- Create: `.editorconfig`
- Test: `tests/integration/test_contract_docs.py`

**Interfaces:**
- Consumes: Approved week-one design and all existing API/module documents.
- Produces: One unambiguous gateway-orchestrated flow and exact FL/privacy handoff fields for all implementers.

- [ ] **Step 1: Write the failing contract-document test**

```python
from pathlib import Path

ROOT = Path(__file__).parents[2]


def test_week_one_contract_contains_required_handoffs():
    openapi = (ROOT / "docs/api/openapi.md").read_text(encoding="utf-8")
    flow = (ROOT / "docs/design/main-flow.md").read_text(encoding="utf-8")
    assert "updates" in openapi
    assert "aggregateResultUri" in openapi
    assert "aggregateHash" in openapi
    assert "evidenceEventIds" in openapi
    assert "业务服务不直接写账本" in flow
```

- [ ] **Step 2: Run the focused test and confirm failure**

Run:

```powershell
python -m pytest tests/integration/test_contract_docs.py -v
```

Expected: FAIL because at least one handoff field or orchestration sentence is absent.

- [ ] **Step 3: Define exact FL start response**

Update `POST /api/v1/fl/tasks/{taskId}/start` success `data` to:

```json
{
  "trainingTaskId": "fl_task_001",
  "status": "running",
  "currentRound": 1,
  "updates": [
    {
      "participantDid": "did:vpp:load-aggregator:001",
      "sampleCount": 500,
      "modelUpdateUri": "memory://updates/fl_task_001/round_1/load.json",
      "updateHash": "sha256:update001"
    }
  ]
}
```

- [ ] **Step 4: Define exact FL aggregate request**

Update `POST /api/v1/fl/tasks/{taskId}/rounds/{roundId}/aggregate` request to:

```json
{
  "aggregateId": "aggregate_001",
  "aggregateResultUri": "memory://aggregates/fl_task_001/round_1/result.json",
  "aggregateHash": "sha256:agg001"
}
```

- [ ] **Step 5: Define exact per-round aggregate response**

For rounds before the final round:

```json
{
  "trainingTaskId": "fl_task_001",
  "roundId": 1,
  "status": "running",
  "currentRound": 2,
  "updates": [
    {
      "participantDid": "did:vpp:load-aggregator:001",
      "sampleCount": 500,
      "modelUpdateUri": "memory://updates/fl_task_001/round_2/load.json",
      "updateHash": "sha256:update-round-2-load"
    }
  ],
  "globalModelVersion": null,
  "modelHash": null,
  "metrics": null
}
```

For the final round:

```json
{
  "trainingTaskId": "fl_task_001",
  "roundId": 3,
  "status": "completed",
  "currentRound": 3,
  "updates": [],
  "globalModelVersion": "global_model_v1",
  "modelHash": "sha256:model123",
  "participantCount": 3,
  "metrics": {
    "mae": 2.31,
    "rmse": 3.72,
    "mape": 0.081
  }
}
```

The gateway loops over `updates -> privacy aggregate -> FL aggregate` until `status` is `completed`.

- [ ] **Step 6: Define Agent evidence context**

Update `POST /api/v1/agent/audit-question` and `POST /api/v1/agent/audit-report` requests so the gateway can pass ledger evidence without the Agent calling the ledger directly:

```json
{
  "businessId": "demo_001",
  "modelVersion": "global_model_v1",
  "evidenceEventIds": ["evt_001", "evt_002"],
  "question": "本次交易是否具备完整审计证据？"
}
```

For audit reports, replace `question` with:

```json
{"reportType": "transaction_audit"}
```

- [ ] **Step 7: Freeze gateway-only orchestration**

State in `main-flow.md` and `module-contracts.md`:

```text
第一周由 api-gateway 调用 privacy-compute 和 ledger-service。
federated-learning、privacy-compute 和 ai-agent 不直接写账本。
```

- [ ] **Step 8: Add version and encoding files**

`.python-version`:

```text
3.11
```

`.nvmrc`:

```text
24
```

`.editorconfig`:

```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.md]
trim_trailing_whitespace = false

[*.py]
indent_style = space
indent_size = 4

[{*.js,*.vue,*.json,*.yml,*.yaml}]
indent_style = space
indent_size = 2
```

- [ ] **Step 9: Document the baseline and ignore generated/sensitive files**

Add to `README.md`:

```text
Backend: Python 3.11 + FastAPI + Pydantic v2 + Uvicorn
Frontend: Node.js 24 LTS + Vue 3 + Vite + JavaScript + Element Plus
Communication: HTTP/JSON
Week-one storage: in-memory Mock
```

Append to `.gitignore`:

```gitignore
.env
.venv/
**/__pycache__/
**/.pytest_cache/
**/*.egg-info/
apps/web-dashboard/node_modules/
apps/web-dashboard/dist/
```

- [ ] **Step 10: Re-run contract test**

Run:

```powershell
python -m pytest tests/integration/test_contract_docs.py -v
```

Expected: PASS.

- [ ] **Step 11: Commit**

```powershell
git add docs/api/openapi.md docs/design/main-flow.md docs/design/module-contracts.md README.md .gitignore .python-version .nvmrc .editorconfig tests/integration/test_contract_docs.py
git commit -m "docs: freeze week-one service contracts"
```

---

### Task 2: Build and freeze the shared `vpp_common` package

**Files:**
- Create: `packages/common/pyproject.toml`
- Create: `packages/common/README.md`
- Create: `packages/common/src/vpp_common/__init__.py`
- Create: `packages/common/src/vpp_common/response.py`
- Create: `packages/common/src/vpp_common/errors.py`
- Create: `packages/common/src/vpp_common/fastapi_support.py`
- Create: `packages/common/src/vpp_common/schemas.py`
- Create: `packages/common/src/vpp_common/id_generator.py`
- Create: `packages/common/src/vpp_common/time_utils.py`
- Create: `packages/common/src/vpp_common/tracing.py`
- Create: `packages/common/tests/test_response.py`
- Create: `packages/common/tests/test_ids.py`
- Create: `packages/common/tests/test_tracing.py`
- Create: `packages/common/tests/test_fastapi_support.py`

**Interfaces:**
- Consumes: `docs/api/response-and-errors.md`.
- Produces: `ApiResponse[T]`, `success()`, `failure()`, `ErrorCode`, `new_id()`, `utc_now_iso()`, and `resolve_trace_id()` for all backends.
- Produces: `ServiceError` and `install_exception_handlers()` so validation and business errors also use the unified envelope.

- [ ] **Step 1: Write failing response tests**

```python
from vpp_common.errors import ErrorCode
from vpp_common.response import failure, success


def test_success_envelope():
    body = success({"service": "meter-simulator"}, trace_id="trace_test")
    assert body.model_dump() == {
        "code": 0,
        "message": "ok",
        "data": {"service": "meter-simulator"},
        "traceId": "trace_test",
    }


def test_failure_envelope():
    body = failure(ErrorCode.INVALID_REQUEST, "trace_test")
    assert body.code == 40001
    assert body.message == "invalid request"
    assert body.data is None
```

- [ ] **Step 2: Run tests and confirm import failure**

```powershell
python -m pip install -e packages/common
python -m pytest packages/common/tests -v
```

Expected: FAIL because package modules are not implemented.

- [ ] **Step 3: Implement stable error codes**

```python
from enum import Enum


class ErrorCode(Enum):
    INVALID_REQUEST = (40001, "invalid request")
    MISSING_REQUIRED_FIELD = (40002, "missing required field")
    INVALID_TIMESTAMP = (40003, "invalid timestamp")
    INVALID_ENUM_VALUE = (40004, "invalid enum value")
    PAYLOAD_TOO_LARGE = (40005, "payload too large")
    MISSING_IDENTITY = (40101, "missing identity")
    INVALID_DID = (40102, "invalid did")
    INVALID_SIGNATURE = (40103, "invalid signature")
    INVALID_HASH = (40104, "invalid hash")
    ACCESS_DENIED = (40301, "access denied")
    AUTHORIZATION_REQUIRED = (40302, "authorization required")
    AUTHORIZATION_EXPIRED = (40303, "authorization expired")
    RESOURCE_NOT_FOUND = (40401, "resource not found")
    BUSINESS_NOT_FOUND = (40402, "business not found")
    TRAINING_TASK_NOT_FOUND = (40403, "training task not found")
    MODEL_VERSION_NOT_FOUND = (40404, "model version not found")
    IDEMPOTENCY_CONFLICT = (40901, "idempotency conflict")
    INVALID_RESOURCE_STATE = (40902, "invalid resource state")
    DUPLICATE_EVENT = (40903, "duplicate event")
    PARTICIPANTS_NOT_READY = (42201, "participants not ready")
    INSUFFICIENT_UPDATES = (42202, "insufficient updates")
    UNSUPPORTED_PRIVACY_MODE = (42203, "unsupported privacy mode")
    INVALID_TRAINING_CONFIGURATION = (42204, "invalid training configuration")
    RATE_LIMIT_EXCEEDED = (42901, "rate limit exceeded")
    INTERNAL_ERROR = (50001, "internal error")
    STORAGE_ERROR = (50002, "storage error")
    SERIALIZATION_ERROR = (50003, "serialization error")
    DOWNSTREAM_REJECTED = (50201, "downstream rejected")
    DOWNSTREAM_INVALID_RESPONSE = (50202, "downstream invalid response")
    DOWNSTREAM_UNAVAILABLE = (50203, "downstream unavailable")
    SERVICE_UNAVAILABLE = (50301, "service unavailable")
    DEPENDENCY_UNAVAILABLE = (50302, "dependency unavailable")
    MAINTENANCE_MODE = (50303, "maintenance mode")
    DOWNSTREAM_TIMEOUT = (50401, "downstream timeout")

    @property
    def code(self) -> int:
        return self.value[0]

    @property
    def message(self) -> str:
        return self.value[1]
```

- [ ] **Step 4: Implement response models**

```python
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

from .errors import ErrorCode

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(populate_by_name=True)
    code: int
    message: str
    data: T | None
    traceId: str


def success(data: T, trace_id: str, message: str = "ok") -> ApiResponse[T]:
    return ApiResponse(code=0, message=message, data=data, traceId=trace_id)


def failure(error: ErrorCode, trace_id: str) -> ApiResponse[Any]:
    return ApiResponse(
        code=error.code,
        message=error.message,
        data=None,
        traceId=trace_id,
    )
```

- [ ] **Step 5: Implement HTTP status mapping and FastAPI exception handlers**

```python
HTTP_STATUS_BY_PREFIX = {
    400: 400,
    401: 401,
    403: 403,
    404: 404,
    409: 409,
    422: 422,
    429: 429,
    500: 500,
    502: 502,
    503: 503,
    504: 504,
}


def http_status_for(error: ErrorCode) -> int:
    return HTTP_STATUS_BY_PREFIX[error.code // 100]
```

```python
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .errors import ErrorCode, http_status_for
from .response import failure
from .tracing import resolve_trace_id


class ServiceError(Exception):
    def __init__(self, error: ErrorCode):
        self.error = error
        super().__init__(error.message)


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, _: RequestValidationError) -> JSONResponse:
        trace_id = resolve_trace_id(request.headers.get("X-Trace-Id"))
        body = failure(ErrorCode.INVALID_REQUEST, trace_id)
        return JSONResponse(status_code=400, content=body.model_dump())

    @app.exception_handler(ServiceError)
    async def service_error(request: Request, exc: ServiceError) -> JSONResponse:
        trace_id = resolve_trace_id(request.headers.get("X-Trace-Id"))
        body = failure(exc.error, trace_id)
        return JSONResponse(
            status_code=http_status_for(exc.error),
            content=body.model_dump(),
        )
```

- [ ] **Step 6: Implement ID, time, and trace helpers**

```python
from uuid import uuid4

ALLOWED_PREFIXES = {
    "demo_",
    "batch_",
    "reading_",
    "asset_",
    "auth_",
    "fl_task_",
    "aggregate_",
    "prediction_",
    "strategy_",
    "report_",
    "evt_",
    "tx_",
    "trace_",
}

def new_id(prefix: str) -> str:
    if prefix not in ALLOWED_PREFIXES:
        raise ValueError(f"unsupported id prefix: {prefix}")
    return f"{prefix}{uuid4().hex[:12]}"
```

```python
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
```

```python
from .id_generator import new_id


def resolve_trace_id(incoming: str | None) -> str:
    return incoming or new_id("trace_")
```

- [ ] **Step 7: Run package tests**

```powershell
python -m pytest packages/common/tests -v
```

Expected: all tests PASS.

- [ ] **Step 8: Commit and announce API freeze**

```powershell
git add packages/common
git commit -m "feat: add shared response and tracing package"
```

After merge, announce:

```text
vpp_common week-one API is frozen. Business modules may consume it but may not add module-specific schemas to the package.
```

---

### Task 3: Deliver all eight standalone backend services

**Files:**
- Create/modify: all files listed in owner packets for `meter-simulator`, `data-ingestion`, `identity-did`, `federated-learning`, `privacy-compute`, `ledger-service`, `ai-agent`, and `api-gateway`.

**Interfaces:**
- Consumes: Tasks 1-2 and `docs/api/openapi.md`.
- Produces: Eight independently testable FastAPI services.

- [ ] **Step 1: Each owner creates a feature branch**

```powershell
git switch develop
git pull --ff-only
git switch -c feature/<module>-week1-mock
```

- [ ] **Step 2: Each owner follows their packet**

Use the exact packet in:

```text
docs/superpowers/plans/2026-07-16-week-one-owner-issue-packets.md
```

- [ ] **Step 3: Each owner proves independent installation and tests**

Example for meter-simulator:

```powershell
python -m pip install -e packages/common -e services/meter-simulator
python -m pytest services/meter-simulator/tests -v
```

Expected: all module tests PASS.

- [ ] **Step 4: Each owner opens a PR before Day 4**

Every PR includes:

```text
Closes #<issue>
Module test command and output
GET /health evidence
Normal request evidence
Failure request evidence
Idempotency evidence
Docker build evidence
Gateway integration state
```

---

### Task 4: Build the Vue one-page demo console

**Files:**
- Create/modify: files listed in the web-dashboard owner packet.

**Interfaces:**
- Consumes: `POST /api/v1/demo/run`, `GET /api/v1/demo/status/{businessId}`.
- Produces: A browser UI that starts and displays the full flow and renders errors with `traceId`.

- [ ] **Step 1: Build against fixture JSON**

Run:

```powershell
cd apps/web-dashboard
npm install
npm run dev
```

Expected: the static one-page console renders all seven stages and result cards.

- [ ] **Step 2: Replace fixture provider with Axios gateway client**

The only production API base URL is:

```javascript
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
})
```

- [ ] **Step 3: Build**

```powershell
npm run build
```

Expected: exit code `0` and `dist/` created.

- [ ] **Step 4: Commit**

```powershell
git add apps/web-dashboard
git commit -m "feat: add one-click mock demo dashboard"
```

---

### Task 5: Compose all nine services

**Files:**
- Create: `.env.example`
- Create: `infra/docker-compose/docker-compose.yml`
- Create: `services/api-gateway/Dockerfile`
- Create: `services/meter-simulator/Dockerfile`
- Create: `services/data-ingestion/Dockerfile`
- Create: `services/identity-did/Dockerfile`
- Create: `services/federated-learning/Dockerfile`
- Create: `services/privacy-compute/Dockerfile`
- Create: `services/ledger-service/Dockerfile`
- Create: `services/ai-agent/Dockerfile`
- Create: `apps/web-dashboard/Dockerfile`
- Create: `apps/web-dashboard/nginx.conf`

**Interfaces:**
- Consumes: Eight backend images and one frontend image.
- Produces: `docker compose up --build` environment with service-name discovery.

- [ ] **Step 1: Validate Compose before services are complete**

```powershell
docker compose -f infra/docker-compose/docker-compose.yml config
```

Expected on Day 1: configuration parses even if some image builds are not ready.

- [ ] **Step 2: Use fixed internal URLs**

```text
METER_SERVICE_URL=http://meter-simulator:8000
INGESTION_SERVICE_URL=http://data-ingestion:8000
IDENTITY_SERVICE_URL=http://identity-did:8000
FL_SERVICE_URL=http://federated-learning:8000
PRIVACY_SERVICE_URL=http://privacy-compute:8000
LEDGER_SERVICE_URL=http://ledger-service:8000
AGENT_SERVICE_URL=http://ai-agent:8000
```

- [ ] **Step 3: Add health checks**

Every backend health check calls:

```text
http://localhost:8000/health
```

For Python slim images, use Python rather than assuming `curl` is installed:

```yaml
healthcheck:
  test:
    - CMD
    - python
    - -c
    - "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
  interval: 5s
  timeout: 3s
  retries: 10
```

The frontend health check calls:

```text
http://localhost/
```

- [ ] **Step 4: Build and start**

```powershell
docker compose -f infra/docker-compose/docker-compose.yml up --build -d
docker compose -f infra/docker-compose/docker-compose.yml ps
```

Expected by Day 4: nine services are running; backend services become healthy.

- [ ] **Step 5: Commit**

```powershell
git add .env.example infra/docker-compose apps/web-dashboard/Dockerfile apps/web-dashboard/nginx.conf services/*/Dockerfile
git commit -m "build: add week-one compose environment"
```

---

### Task 6: Upgrade CI from directory smoke checks

**Files:**
- Modify: `.github/workflows/ci.yml`
- Create: `tests/integration/test_openapi_coverage.py`

**Interfaces:**
- Consumes: all module tests, frontend build, Compose file, and API docs.
- Produces: PR checks that reject broken modules and contract drift.

- [ ] **Step 1: Add backend matrix**

The matrix must contain:

```yaml
service:
  - packages/common
  - services/api-gateway
  - services/meter-simulator
  - services/data-ingestion
  - services/identity-did
  - services/federated-learning
  - services/privacy-compute
  - services/ledger-service
  - services/ai-agent
```

- [ ] **Step 2: Add frontend build job**

Run:

```text
npm ci
npm run build
```

in `apps/web-dashboard`.

- [ ] **Step 3: Add Compose validation**

Run:

```text
docker compose -f infra/docker-compose/docker-compose.yml config
```

- [ ] **Step 4: Add contract coverage test**

The test extracts `(method, path)` pairs from `module-contracts.md` and checks they appear in `openapi.md`, then queries each FastAPI application's generated OpenAPI schema in its module test suite.

- [ ] **Step 5: Run local equivalents**

```powershell
python -m pytest packages/common/tests services tests/integration -v
cd apps/web-dashboard
npm ci
npm run build
cd ../..
docker compose -f infra/docker-compose/docker-compose.yml config
```

Expected: all commands exit `0`.

- [ ] **Step 6: Commit**

```powershell
git add .github/workflows/ci.yml tests/integration/test_openapi_coverage.py
git commit -m "ci: validate services frontend and contracts"
```

---

### Task 7: Add full-chain E2E tests

**Files:**
- Create: `tests/e2e/test_demo_flow.py`
- Create: `tests/e2e/test_demo_failures.py`
- Create: `tests/e2e/README.md`

**Interfaces:**
- Consumes: running Compose environment at `http://localhost:8000`.
- Produces: repeatable acceptance evidence for success, idempotency, state query, trace propagation, and downstream failure.

- [ ] **Step 1: Write the success E2E**

```python
import httpx


def test_full_demo_flow():
    payload = {
        "scenario": "vpp_day_ahead_trading",
        "participants": [
            "did:vpp:load-aggregator:001",
            "did:vpp:renewable-plant:001",
            "did:vpp:storage:001",
        ],
        "meterCount": 3,
        "trainingRounds": 3,
    }
    headers = {"Idempotency-Key": "e2e-demo-success"}
    response = httpx.post(
        "http://localhost:8000/api/v1/demo/run",
        json=payload,
        headers=headers,
        timeout=30,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["traceId"]
    assert body["data"]["businessId"].startswith("demo_")
    assert body["data"]["globalModelVersion"].startswith("global_model_v")
    assert body["data"]["auditReportId"].startswith("report_")
    assert len(body["data"]["ledgerTxIds"]) >= 7
```

- [ ] **Step 2: Add status and idempotency assertions**

Repeat the request with the same key and assert the same `businessId`; call status endpoint and assert `COMPLETED`.

- [ ] **Step 3: Run success E2E**

```powershell
python -m pytest tests/e2e/test_demo_flow.py -v
```

Expected: PASS against running Compose.

- [ ] **Step 4: Add stopped-downstream test**

Stop `privacy-compute`, execute the flow with a new key, and assert `code` is `50203` or `50302` and `traceId` is present.

- [ ] **Step 5: Restore environment and run full E2E**

```powershell
docker compose -f infra/docker-compose/docker-compose.yml up -d privacy-compute
python -m pytest tests/e2e -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```powershell
git add tests/e2e
git commit -m "test: cover full mock demo flow"
```

---

### Task 8: Execute Day 7 clean-environment acceptance

**Files:**
- Create: `docs/deploy/week-one-runbook.md`
- Create: `docs/report/week-one-acceptance.md`
- Modify: `demo/video-storyboard.md`

**Interfaces:**
- Consumes: merged `develop` branch and all week-one deliverables.
- Produces: acceptance evidence and release readiness decision.

- [ ] **Step 1: Start from a clean clone or clean machine**

```powershell
git clone <repository-url>
cd vpp-trusted-data-space
git switch develop
Copy-Item .env.example .env
docker compose -f infra/docker-compose/docker-compose.yml up --build -d
```

- [ ] **Step 2: Verify nine services**

```powershell
docker compose -f infra/docker-compose/docker-compose.yml ps
```

Expected: frontend and eight backends are running; backends are healthy.

- [ ] **Step 3: Run automated acceptance**

```powershell
python -m pytest tests/e2e -v
```

Expected: all E2E tests PASS.

- [ ] **Step 4: Run browser acceptance**

Open `http://localhost:3000`, click “开始演示”, and record:

```text
businessId
readingBatchId
assetId
authId
trainingTaskId
globalModelVersion
MAE/RMSE/MAPE
ledgerTxIds
auditReportId
traceId
```

- [ ] **Step 5: Record failure recovery**

Stop one downstream service, confirm the UI displays failure stage, code, message, and `traceId`, then restore it and rerun with a new idempotency key.

- [ ] **Step 6: Write acceptance report**

`docs/report/week-one-acceptance.md` must contain:

```text
Commit SHA
Environment
Compose result
Backend test count
Frontend build result
E2E result
Successful demo IDs
Failure drill result
Known limitations
Week-two replacement order
Go/No-Go decision
```

- [ ] **Step 7: Commit acceptance artifacts**

```powershell
git add docs/deploy/week-one-runbook.md docs/report/week-one-acceptance.md demo/video-storyboard.md
git commit -m "docs: record week-one mock acceptance"
```

- [ ] **Step 8: Merge and tag**

After all checks are green:

```powershell
git tag -a week1-mock-v0.1.0 -m "Week one full-chain mock demo"
git push origin week1-mock-v0.1.0
```

Expected: the tag points to the accepted integration commit.

---

## Coordination Cadence

Board states:

```text
Backlog -> Ready -> In Progress -> In Review -> Integration -> Done
                                              \-> Blocked
```

Rules:

```text
09:30: 15-minute stand-up; report yesterday's evidence, today's verifiable deliverable, and blockers.
20:30: 20-30 minute integration session; merge approved PRs and run health/Compose/main-flow checks.
Blocked for more than 2 hours: move Issue to Blocked and notify the technical lead.
Code complete but not integrated: keep the Issue in Integration, not Done.
Day 4 onward: prioritize small integration PRs over large module rewrites.
```

Interface change gate:

```text
owner states reason and affected callers
-> technical lead approves
-> openapi.md changes first
-> module-contracts.md changes
-> main-flow.md changes if sequence/state changes
-> response-and-errors.md changes if public protocol changes
-> implementation changes
-> affected modules repeat integration tests
```

## Daily Integration Gates

### Day 1

```text
Contracts frozen
vpp_common merged
8 x /health tests green
Vue project starts
Compose config parses
```

### Day 2

```text
All module normal endpoints implemented
Frontend fixture UI complete
Each module has an open PR
```

### Day 3

```text
Failure paths, state, IDs, and idempotency complete
Module test suites green
Gateway clients complete
```

### Day 4

```text
Real HTTP backend chain complete
Nine-service Compose starts
No module waits on undocumented fields
```

### Day 5

```text
Frontend calls real gateway
First successful browser flow
Evidence chain and Agent report visible
```

### Day 6

```text
CI green
E2E green
Stopped-service failure drill passes
README and runbook complete
```

### Day 7

```text
Clean-environment acceptance passes
Demo rehearsal passes
No P0 blocker remains
week1-mock-v0.1.0 frozen
```

## Definition of Done

### Backend module

A backend issue is `Done` only when:

```text
service installs and starts independently
GET /health returns the unified envelope
all owned OpenAPI paths are implemented
normal-path tests pass for every endpoint
at least two failure-path tests pass
at least one write-endpoint idempotency test passes
traceId is returned and preserved
created resources are queryable with dynamic IDs
Docker image builds and becomes healthy
README contains install, run, test, and curl commands
PR includes verification evidence
gateway integration is complete or explicitly not yet applicable
```

### Frontend

The frontend issue is `Done` only when:

```text
it calls only api-gateway
one-click success displays every required result
loading prevents duplicate clicks
failure displays stage, code, message, and traceId
businessId status query works
npm run build passes
Compose browser access passes
```

### Full chain

Week one is `Done` only when:

```text
nine Compose services run
eight backend health checks pass
browser starts a real HTTP-orchestrated flow
linked business IDs and metrics are visible
ledger trace contains all key stages
same-key retry reuses businessId
stopped-downstream drill returns a traceable error
CI passes
E2E passes
clean-environment acceptance report records Go
```

## Execution Order

```text
Task 1 contract freeze
  -> Task 2 common package
      -> Tasks 3 backend modules in parallel
      -> Task 4 frontend fixtures in parallel
      -> Task 5 Compose from Day 1
          -> Task 6 CI
          -> Task 7 E2E
              -> Task 8 acceptance and tag
```
