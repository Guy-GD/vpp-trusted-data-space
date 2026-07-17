# Week One Owner Issue Packets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide ten copy-ready, owner-scoped task packets that implement the approved week-one full-chain Mock delivery without overlapping module ownership.

**Architecture:** Each owner changes only their primary module plus explicitly assigned cross-cutting files. Backend modules are unique installable Python packages that consume `vpp_common`; the gateway orchestrates HTTP calls, privacy-compute owns Compose, and the frontend calls only the gateway.

**Tech Stack:** Python 3.11, FastAPI, Pydantic v2, Uvicorn, httpx, pytest, Vue 3, Vite, JavaScript, Element Plus, Axios, Node.js 24 LTS, Docker Compose, GitHub Actions.

## Global Constraints

- Read `docs/design/week-one-mock-delivery.md` before implementation.
- Follow `docs/api/openapi.md`, `docs/api/response-and-errors.md`, `docs/design/module-contracts.md`, and `docs/design/main-flow.md`.
- The technical lead approves every path, field, enum, state, and error-code change.
- All backends provide `GET /health`, unified response envelopes, dynamic IDs, in-memory repositories, tracing, and idempotency.
- Do not import another service's Python package; use HTTP.
- Do not add a database, blockchain SDK, MQTT broker, real cryptography, real federated framework, production MPC, or external LLM API.
- Each owner provides tests, Dockerfile, README, curl examples, and PR evidence.
- Use UTF-8 and do not commit secrets or `.env`.

## Exact Interface Ownership

| Owner | Method | Path |
|---|---|---|
| api-gateway | POST | `/api/v1/demo/run` |
| api-gateway | GET | `/api/v1/demo/status/{businessId}` |
| meter-simulator | POST | `/api/v1/meter/readings/generate` |
| data-ingestion | POST | `/api/v1/data/ingest` |
| data-ingestion | POST | `/api/v1/data/assets` |
| data-ingestion | GET | `/api/v1/data/assets/{assetId}` |
| identity-did | POST | `/api/v1/identity/subjects` |
| identity-did | POST | `/api/v1/identity/devices` |
| identity-did | POST | `/api/v1/identity/verify` |
| identity-did | POST | `/api/v1/auth/requests` |
| identity-did | POST | `/api/v1/auth/requests/{authId}/approve` |
| identity-did | GET | `/api/v1/auth/requests/{authId}` |
| federated-learning | POST | `/api/v1/fl/tasks` |
| federated-learning | POST | `/api/v1/fl/tasks/{taskId}/start` |
| federated-learning | POST | `/api/v1/fl/tasks/{taskId}/rounds/{roundId}/updates` |
| federated-learning | POST | `/api/v1/fl/tasks/{taskId}/rounds/{roundId}/aggregate` |
| federated-learning | GET | `/api/v1/fl/tasks/{taskId}` |
| federated-learning | GET | `/api/v1/fl/tasks/{taskId}/metrics` |
| federated-learning | GET | `/api/v1/fl/models/{modelVersion}` |
| privacy-compute | POST | `/api/v1/privacy/model-updates/encrypt` |
| privacy-compute | POST | `/api/v1/privacy/model-updates/mask` |
| privacy-compute | POST | `/api/v1/privacy/secure-aggregate` |
| privacy-compute | GET | `/api/v1/privacy/aggregates/{aggregateId}` |
| ledger-service | POST | `/api/v1/ledger/events` |
| ledger-service | GET | `/api/v1/ledger/events/{eventId}` |
| ledger-service | GET | `/api/v1/ledger/traces/{businessId}` |
| ai-agent | POST | `/api/v1/agent/predict` |
| ai-agent | POST | `/api/v1/agent/trading-strategy` |
| ai-agent | POST | `/api/v1/agent/audit-question` |
| ai-agent | POST | `/api/v1/agent/audit-report` |
| all backend owners | GET | `/health` |

## Shared Backend Packaging Contract

Every backend owner uses:

```toml
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"

[project]
name = "<distribution-name>"
version = "0.1.0"
requires-python = ">=3.11,<3.12"
dependencies = [
  "fastapi>=0.115,<1",
  "pydantic>=2,<3",
  "uvicorn[standard]>=0.34,<1",
]

[project.optional-dependencies]
test = [
  "httpx>=0.28,<1",
  "pytest>=8,<9",
]

[tool.setuptools.packages.find]
where = ["src"]
```

`api-gateway` additionally depends on:

```toml
"httpx>=0.28,<1",
"pydantic-settings>=2,<3",
"pytest-asyncio>=0.24,<1",
```

Every service `main.py` exposes:

```python
from fastapi import FastAPI, Header
from vpp_common.fastapi_support import install_exception_handlers
from vpp_common.response import ApiResponse, success
from vpp_common.tracing import resolve_trace_id

app = FastAPI(title="<service-name>", version="0.1.0")
install_exception_handlers(app)


@app.get("/health", response_model=ApiResponse[dict[str, str]])
def health(x_trace_id: str | None = Header(default=None)) -> ApiResponse[dict[str, str]]:
    trace_id = resolve_trace_id(x_trace_id)
    return success(
        {"service": "<service-name>", "status": "healthy"},
        trace_id=trace_id,
    )
```

Every service treats `/health` as readiness for week one and configures logs without request bodies:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s service=<service-name> %(message)s",
)
logger = logging.getLogger("<service-name>")
```

Route/service logs include `traceId`, business ID, stage, and outcome, but never meter plaintext, keys, signatures, ciphertext contents, or raw model updates.

Every backend Dockerfile uses the repository root as build context:

```dockerfile
FROM python:3.11-slim
WORKDIR /workspace
COPY packages/common packages/common
COPY services/<service> services/<service>
RUN python -m pip install --no-cache-dir ./packages/common ./services/<service>
EXPOSE 8000
CMD ["uvicorn", "<python_package>.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### Task 1: Technical lead — contracts, common package, integration governance

**GitHub Issue title:** `[P0][公共] 冻结契约并实现 vpp_common 公共包`

**Owner:** Technical lead

**Dependencies:** None.

**Files:**
- Modify: `docs/api/openapi.md`
- Modify: `docs/design/main-flow.md`
- Modify: `docs/design/module-contracts.md`
- Modify: `README.md`
- Modify: `.gitignore`
- Create: `.python-version`
- Create: `.nvmrc`
- Create: `.editorconfig`
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
- Create: `tests/integration/test_contract_docs.py`

**Interfaces:**
- Produces: frozen FL/privacy handoff fields and `vpp_common` public API.
- Consumers: all eight backend owners.

- [ ] **Step 1: Freeze orchestration and handoff fields**

Write the exact contracts described in Task 1 of `2026-07-16-week-one-mock-master.md`.

Acceptance:

```text
FL start response has updates[]
FL aggregate request has aggregateId, aggregateResultUri, aggregateHash
Agent audit requests have modelVersion and evidenceEventIds
api-gateway is the week-one orchestrator
business services do not write ledger events directly
```

- [ ] **Step 2: Write common-package tests before implementation**

Create:

```python
def test_new_ids_use_prefix():
    from vpp_common.id_generator import new_id
    assert new_id("asset_").startswith("asset_")


def test_unknown_id_prefix_is_rejected():
    import pytest
    from vpp_common.id_generator import new_id
    with pytest.raises(ValueError):
        new_id("unknown_")


def test_resolve_trace_id_preserves_incoming():
    from vpp_common.tracing import resolve_trace_id
    assert resolve_trace_id("trace_existing") == "trace_existing"
```

- [ ] **Step 3: Define the common package metadata**

`packages/common/pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"

[project]
name = "vpp-common"
version = "0.1.0"
requires-python = ">=3.11,<3.12"
dependencies = [
  "fastapi>=0.115,<1",
  "pydantic>=2,<3",
]

[project.optional-dependencies]
test = [
  "httpx>=0.28,<1",
  "pytest>=8,<9",
]

[tool.setuptools.packages.find]
where = ["src"]
```

- [ ] **Step 4: Run tests and observe failure**

```powershell
python -m pip install -e packages/common
python -m pytest packages/common/tests tests/integration/test_contract_docs.py -v
```

Expected before implementation: import or assertion failures.

- [ ] **Step 5: Implement public API**

Exports in `packages/common/src/vpp_common/__init__.py`:

```python
from .errors import ErrorCode
from .fastapi_support import ServiceError, install_exception_handlers
from .id_generator import new_id
from .response import ApiResponse, failure, success
from .time_utils import utc_now_iso
from .tracing import resolve_trace_id

__all__ = [
    "ApiResponse",
    "ErrorCode",
    "ServiceError",
    "failure",
    "install_exception_handlers",
    "new_id",
    "resolve_trace_id",
    "success",
    "utc_now_iso",
]
```

- [ ] **Step 6: Define cross-module base schemas**

`packages/common/src/vpp_common/schemas.py`:

```python
from pydantic import BaseModel


class HealthData(BaseModel):
    service: str
    status: str


class ErrorDetail(BaseModel):
    field: str
    reason: str
```

- [ ] **Step 7: Run tests**

```powershell
python -m pytest packages/common/tests tests/integration/test_contract_docs.py -v
```

Expected: all PASS.

- [ ] **Step 8: Publish integration rules**

Post to the team:

```text
vpp_common API frozen at 0.1.0.
Do not copy response/error helpers into services.
Do not add module DTOs to common.
Interface changes require technical-lead approval and docs-first update.
```

- [ ] **Step 9: Publish repository baseline**

Add the approved backend/frontend stack and HTTP/JSON rule to `README.md`. Add `.env`, Python caches, editable-install metadata, `node_modules`, and frontend `dist` to `.gitignore`.

```gitignore
.env
.venv/
**/__pycache__/
**/.pytest_cache/
**/*.egg-info/
apps/web-dashboard/node_modules/
apps/web-dashboard/dist/
```

- [ ] **Step 10: Commit**

```powershell
git add .python-version .nvmrc .editorconfig README.md .gitignore packages/common docs/api/openapi.md docs/design/main-flow.md docs/design/module-contracts.md tests/integration/test_contract_docs.py
git commit -m "feat: freeze contracts and add common package"
```

**Issue acceptance:**

- [ ] Common tests pass.
- [ ] Contract test passes.
- [ ] All backend owners can install `packages/common`.
- [ ] No module-specific DTO exists in common.
- [ ] Day 1 noon API freeze announced.

---

### Task 2: meter-simulator owner — trusted collection Mock

**GitHub Issue title:** `[P0][源端采集] 实现 meter-simulator 动态 Mock 批次`

**Owner:** meter-simulator owner

**Dependencies:** Task 1 common package.

**Files:**
- Create: `services/meter-simulator/pyproject.toml`
- Create: `services/meter-simulator/src/meter_simulator/__init__.py`
- Create: `services/meter-simulator/src/meter_simulator/main.py`
- Create: `services/meter-simulator/src/meter_simulator/api.py`
- Create: `services/meter-simulator/src/meter_simulator/schemas.py`
- Create: `services/meter-simulator/src/meter_simulator/repository.py`
- Create: `services/meter-simulator/src/meter_simulator/service.py`
- Create: `services/meter-simulator/tests/test_health.py`
- Create: `services/meter-simulator/tests/test_readings.py`
- Create: `services/meter-simulator/Dockerfile`
- Create: `services/meter-simulator/README.md`

**Interfaces:**
- Consumes: `POST /api/v1/meter/readings/generate` request and `Idempotency-Key`.
- Produces: `readingBatchId` and `readings[]` for api-gateway/data-ingestion.

- [ ] **Step 1: Write failing request/response tests**

```python
from fastapi.testclient import TestClient
from meter_simulator.main import app

client = TestClient(app)


def test_generate_readings():
    response = client.post(
        "/api/v1/meter/readings/generate",
        headers={"Idempotency-Key": "meter-case-1", "X-Trace-Id": "trace_meter"},
        json={
            "meterId": "meter_001",
            "ownerDid": "did:vpp:load-aggregator:001",
            "count": 3,
            "intervalSeconds": 5,
        },
    )
    body = response.json()
    assert response.status_code == 200
    assert body["code"] == 0
    assert body["traceId"] == "trace_meter"
    assert body["data"]["readingBatchId"].startswith("batch_")
    assert len(body["data"]["readings"]) == 3


def test_same_key_returns_same_batch():
    request = {
        "meterId": "meter_001",
        "ownerDid": "did:vpp:load-aggregator:001",
        "count": 1,
        "intervalSeconds": 5,
    }
    first = client.post("/api/v1/meter/readings/generate", headers={"Idempotency-Key": "same"}, json=request)
    second = client.post("/api/v1/meter/readings/generate", headers={"Idempotency-Key": "same"}, json=request)
    assert first.json()["data"]["readingBatchId"] == second.json()["data"]["readingBatchId"]
```

- [ ] **Step 2: Run and confirm failure**

```powershell
python -m pip install -e packages/common -e "services/meter-simulator[test]"
python -m pytest services/meter-simulator/tests -v
```

Expected: FAIL before routes exist.

- [ ] **Step 3: Implement schemas**

```python
from pydantic import BaseModel, Field


class GenerateReadingsRequest(BaseModel):
    meterId: str
    ownerDid: str
    count: int = Field(ge=1, le=100)
    intervalSeconds: int = Field(ge=1, le=3600)


class Reading(BaseModel):
    readingId: str
    meterId: str
    ownerDid: str
    ciphertext: str
    signature: str
    hash: str
    timestamp: str


class ReadingBatch(BaseModel):
    readingBatchId: str
    readings: list[Reading]
```

- [ ] **Step 4: Implement deterministic service and repository**

Use `random.Random(f"{meterId}:{count}:{intervalSeconds}")` so the numeric Mock payload is reproducible, but generate dynamic business IDs. Store:

```python
idempotency_key -> {"request_hash": str, "result": ReadingBatch}
```

For each reading:

```python
digest = hashlib.sha256(f"{ciphertext}|{timestamp}".encode("utf-8")).hexdigest()
reading_hash = f"sha256:{digest}"
signature = f"sig:{reading_hash}"
```

Return `40901` when the same key is reused with a different request body.

- [ ] **Step 5: Add failure tests**

Test:

```text
count = 0 -> HTTP 400 and code 40001
ownerDid not starting with did:vpp: -> HTTP 401 and code 40102
same key with changed count -> HTTP 409 and code 40901
```

- [ ] **Step 6: Run tests**

```powershell
python -m pytest services/meter-simulator/tests -v
```

Expected: all PASS.

- [ ] **Step 7: Build Docker image**

```powershell
docker build -f services/meter-simulator/Dockerfile -t vpp/meter-simulator:week1 .
docker run --rm -p 8001:8000 vpp/meter-simulator:week1
```

In another terminal:

```powershell
Invoke-RestMethod http://localhost:8001/health
```

- [ ] **Step 8: Commit**

```powershell
git add services/meter-simulator
git commit -m "feat: add meter simulator mock service"
```

**Issue acceptance:**

- [ ] All two endpoints pass tests.
- [ ] Dynamic IDs and deterministic payloads are demonstrated.
- [ ] Three failure/idempotency cases pass.
- [ ] Docker health check works.
- [ ] README includes install, run, test, and curl examples.

---

### Task 3: data-ingestion owner — encrypted batch and asset Mock

**GitHub Issue title:** `[P0][数据接入] 实现 data-ingestion 验签验哈希与资产登记 Mock`

**Owner:** data-ingestion owner

**Dependencies:** Task 1; consumes meter batch schema.

**Files:**
- Create: `services/data-ingestion/pyproject.toml`
- Create: `services/data-ingestion/src/data_ingestion/__init__.py`
- Create: `services/data-ingestion/src/data_ingestion/main.py`
- Create: `services/data-ingestion/src/data_ingestion/api.py`
- Create: `services/data-ingestion/src/data_ingestion/schemas.py`
- Create: `services/data-ingestion/src/data_ingestion/repository.py`
- Create: `services/data-ingestion/src/data_ingestion/service.py`
- Create: `services/data-ingestion/tests/test_health.py`
- Create: `services/data-ingestion/tests/test_ingestion.py`
- Create: `services/data-ingestion/tests/test_assets.py`
- Create: `services/data-ingestion/Dockerfile`
- Create: `services/data-ingestion/README.md`

**Interfaces:**
- Consumes: encrypted `readings[]`.
- Produces: queryable `assetId`, asset metadata, `40103`, and `40104`.

- [ ] **Step 1: Write failing ingest test**

```python
def test_ingest_registers_queryable_asset(client):
    response = client.post(
        "/api/v1/data/ingest",
        headers={"Idempotency-Key": "ingest-1", "X-Trace-Id": "trace_ingest"},
        json={
            "readingBatchId": "batch_001",
            "ownerDid": "did:vpp:load-aggregator:001",
            "readings": [{
                "readingId": "reading_001",
                "meterId": "meter_001",
                "ciphertext": "base64-ciphertext",
                "signature": "sig:sha256:abc123",
                "hash": "sha256:abc123",
                "timestamp": "2026-07-16T08:00:00+08:00",
            }],
        },
    )
    asset_id = response.json()["data"]["assetId"]
    queried = client.get(f"/api/v1/data/assets/{asset_id}")
    assert queried.json()["data"]["assetId"] == asset_id
```

- [ ] **Step 2: Implement exact request and asset models**

Use:

```python
class IngestRequest(BaseModel):
    readingBatchId: str
    ownerDid: str
    readings: list[EncryptedReading]


class AssetRecord(BaseModel):
    assetId: str
    readingBatchId: str
    ownerDid: str
    assetType: str = "meter_readings"
    sensitivityLevel: str = "private"
    status: str = "registered"
    createdAt: str
```

- [ ] **Step 3: Implement week-one verification rules**

```text
recomputed sha256(ciphertext + "|" + timestamp) must equal hash
signature must equal "sig:" + hash
readings must not be empty
ownerDid must start with did:vpp:
```

These are explicit Mock verification rules, not production cryptography.

- [ ] **Step 4: Implement independent asset registration**

`POST /api/v1/data/assets` accepts:

```json
{
  "readingBatchId": "batch_001",
  "ownerDid": "did:vpp:load-aggregator:001",
  "assetType": "meter_readings",
  "sensitivityLevel": "private",
  "purpose": "federated_training"
}
```

It creates a queryable asset record without ingesting readings.

- [ ] **Step 5: Add failure and idempotency tests**

```text
signature != "sig:" + hash -> 40103
hash without sha256: prefix -> 40104
unknown asset query -> 40401
same key/different request -> 40901
```

- [ ] **Step 6: Run tests**

```powershell
python -m pip install -e packages/common -e "services/data-ingestion[test]"
python -m pytest services/data-ingestion/tests -v
```

Expected: all PASS.

- [ ] **Step 7: Build and commit**

```powershell
docker build -f services/data-ingestion/Dockerfile -t vpp/data-ingestion:week1 .
git add services/data-ingestion
git commit -m "feat: add data ingestion mock service"
```

**Issue acceptance:**

- [ ] All four endpoints pass.
- [ ] Ingested and independently registered assets are queryable.
- [ ] Signature/hash tampering produces exact errors.
- [ ] No plaintext appears in response or logs.
- [ ] Contract-consistency review of another backend PR is recorded.

---

### Task 4: identity-did owner — DID and authorization Mock

**GitHub Issue title:** `[P0][DID] 实现主体设备 DID 与授权状态流转 Mock`

**Owner:** identity-did owner

**Dependencies:** Task 1.

**Files:**
- Create: `services/identity-did/pyproject.toml`
- Create: `services/identity-did/src/identity_did/__init__.py`
- Create: `services/identity-did/src/identity_did/main.py`
- Create: `services/identity-did/src/identity_did/api.py`
- Create: `services/identity-did/src/identity_did/schemas.py`
- Create: `services/identity-did/src/identity_did/repository.py`
- Create: `services/identity-did/src/identity_did/service.py`
- Create: `services/identity-did/tests/test_health.py`
- Create: `services/identity-did/tests/test_identity.py`
- Create: `services/identity-did/tests/test_authorization.py`
- Create: `services/identity-did/Dockerfile`
- Create: `services/identity-did/README.md`

**Interfaces:**
- Produces: subject/device DID records and `requested -> approved` authorization state.

- [ ] **Step 1: Write failing authorization-flow test**

```python
def test_authorization_flow(client):
    request = client.post(
        "/api/v1/auth/requests",
        headers={"Idempotency-Key": "auth-1"},
        json={
            "requesterDid": "did:vpp:operator:001",
            "ownerDid": "did:vpp:load-aggregator:001",
            "assetId": "asset_001",
            "purpose": "federated_training_for_day_ahead_trading",
            "expireAt": "2026-08-01T00:00:00+08:00",
        },
    )
    auth_id = request.json()["data"]["authId"]
    approved = client.post(
        f"/api/v1/auth/requests/{auth_id}/approve",
        headers={"Idempotency-Key": "approve-1"},
        json={"approverDid": "did:vpp:load-aggregator:001", "decision": "approved"},
    )
    assert approved.json()["data"]["status"] == "approved"
```

- [ ] **Step 2: Implement exact repositories**

Store:

```python
subjects: dict[str, SubjectRecord]
devices: dict[str, DeviceRecord]
authorizations: dict[str, AuthorizationRecord]
idempotency: dict[str, StoredResult]
```

Seed the three demo participant DIDs plus `did:vpp:operator:001` so gateway integration does not require setup calls.

- [ ] **Step 3: Implement routes and states**

Routes:

```text
POST /api/v1/identity/subjects
POST /api/v1/identity/devices
POST /api/v1/identity/verify
POST /api/v1/auth/requests
POST /api/v1/auth/requests/{authId}/approve
GET  /api/v1/auth/requests/{authId}
GET  /health
```

Authorization states:

```text
requested -> approved
requested -> rejected
approved -> expired when expireAt is in the past
```

- [ ] **Step 4: Add exact error tests**

```text
unknown DID -> 40102
expired authorization -> 40303
approve already approved -> 40902
unknown authId -> 40401
same idempotency key/different request -> 40901
```

- [ ] **Step 5: Run tests**

```powershell
python -m pip install -e packages/common -e "services/identity-did[test]"
python -m pytest services/identity-did/tests -v
```

Expected: all PASS.

- [ ] **Step 6: Build and commit**

```powershell
docker build -f services/identity-did/Dockerfile -t vpp/identity-did:week1 .
git add services/identity-did
git commit -m "feat: add did and authorization mock service"
```

**Issue acceptance:**

- [ ] Seven endpoints pass.
- [ ] Demo DIDs are available after startup.
- [ ] Authorization transitions and expiry are tested.
- [ ] Failure-path review checklist is shared with team.

---

### Task 5: federated-learning owner — task, rounds, updates, model registry Mock

**GitHub Issue title:** `[P0][联邦学习] 实现三轮训练状态与模型版本 Mock`

**Owner:** federated-learning owner

**Dependencies:** Task 1 exact handoff contract.

**Files:**
- Create: `services/federated-learning/pyproject.toml`
- Create: `services/federated-learning/src/federated_learning/__init__.py`
- Create: `services/federated-learning/src/federated_learning/main.py`
- Create: `services/federated-learning/src/federated_learning/api.py`
- Create: `services/federated-learning/src/federated_learning/schemas.py`
- Create: `services/federated-learning/src/federated_learning/repository.py`
- Create: `services/federated-learning/src/federated_learning/service.py`
- Create: `services/federated-learning/tests/test_health.py`
- Create: `services/federated-learning/tests/test_tasks.py`
- Create: `services/federated-learning/tests/test_rounds.py`
- Create: `services/federated-learning/tests/test_models.py`
- Create: `services/federated-learning/Dockerfile`
- Create: `services/federated-learning/README.md`

**Interfaces:**
- Produces: training task state, current-round updates, metrics, and `global_model_vN`.
- Consumes: privacy aggregate reference in aggregate endpoint.

- [ ] **Step 1: Write failing three-round happy-path test**

```python
def test_task_start_and_aggregate(client):
    created = client.post(
        "/api/v1/fl/tasks",
        headers={"Idempotency-Key": "fl-create-1"},
        json={
            "taskName": "虚拟电厂日前负荷预测联邦训练",
            "modelType": "load_forecast",
            "algorithm": "fedavg",
            "rounds": 3,
            "participants": [
                "did:vpp:load-aggregator:001",
                "did:vpp:renewable-plant:001",
                "did:vpp:storage:001",
            ],
            "assetIds": ["asset_001", "asset_002", "asset_003"],
            "target": "adjustable_capacity_kw",
        },
    )
    task_id = created.json()["data"]["trainingTaskId"]
    started = client.post(f"/api/v1/fl/tasks/{task_id}/start")
    assert len(started.json()["data"]["updates"]) == 3
```

- [ ] **Step 2: Implement task and model records**

```python
class TrainingTaskRecord(BaseModel):
    trainingTaskId: str
    status: Literal["created", "running", "completed", "failed"]
    rounds: int
    currentRound: int
    participants: list[str]
    assetIds: list[str]
    updatesByRound: dict[int, list[ModelUpdate]]
    aggregateByRound: dict[int, AggregateReference]
    globalModelVersion: str | None = None


class ModelRecord(BaseModel):
    modelVersion: str
    trainingTaskId: str
    modelHash: str
    metrics: Metrics
    modelUri: str
```

- [ ] **Step 3: Implement stable updates and metrics**

For each round and participant, produce:

```text
sampleCount: 500, 400, 300
modelUpdateUri: memory://updates/<task>/<round>/<participant>.json
updateHash: sha256:<deterministic digest>
```

Final metrics:

```json
{"mae": 2.31, "rmse": 3.72, "mape": 0.081}
```

- [ ] **Step 4: Enforce aggregate preconditions**

Aggregate request:

```json
{
  "aggregateId": "aggregate_001",
  "aggregateResultUri": "memory://aggregates/fl_task_001/round_1/result.json",
  "aggregateHash": "sha256:agg001"
}
```

Rules:

```text
task must be running
roundId must equal currentRound
three updates must exist
aggregateHash must start with sha256:
final round creates global_model_vN and status completed
```

For a non-final round, the aggregate response increments `currentRound` and returns the next round's three `updates`. For the final round, it returns `status: completed`, an empty `updates` list, `globalModelVersion`, `modelHash`, `participantCount`, and metrics. This exact response shape is frozen in the master plan Task 1.

- [ ] **Step 5: Add error tests**

```text
unknown task -> 40403
invalid rounds/model configuration -> 42204
fewer than three updates -> 42202
aggregate before start -> 40902
unknown model -> 40404
```

- [ ] **Step 6: Run tests**

```powershell
python -m pip install -e packages/common -e "services/federated-learning[test]"
python -m pytest services/federated-learning/tests -v
```

Expected: all PASS.

- [ ] **Step 7: Build and commit**

```powershell
docker build -f services/federated-learning/Dockerfile -t vpp/federated-learning:week1 .
git add services/federated-learning
git commit -m "feat: add federated training mock state machine"
```

**Issue acceptance:**

- [ ] Eight endpoints pass.
- [ ] Three participants and three rounds are demonstrated.
- [ ] Model query and metrics query work after completion.
- [ ] Another backend package structure is reviewed for consistency.

---

### Task 6: privacy-compute owner — privacy Mock plus Compose

**GitHub Issue title:** `[P0][隐私计算][部署] 实现安全聚合 Mock 与九服务 Compose`

**Owner:** privacy-compute owner

**Dependencies:** Task 1; service Dockerfiles delivered by owners.

**Files:**
- Create: `services/privacy-compute/pyproject.toml`
- Create: `services/privacy-compute/src/privacy_compute/__init__.py`
- Create: `services/privacy-compute/src/privacy_compute/main.py`
- Create: `services/privacy-compute/src/privacy_compute/api.py`
- Create: `services/privacy-compute/src/privacy_compute/schemas.py`
- Create: `services/privacy-compute/src/privacy_compute/repository.py`
- Create: `services/privacy-compute/src/privacy_compute/service.py`
- Create: `services/privacy-compute/tests/test_health.py`
- Create: `services/privacy-compute/tests/test_privacy.py`
- Create: `services/privacy-compute/Dockerfile`
- Create: `services/privacy-compute/README.md`
- Create: `.env.example`
- Create: `infra/docker-compose/docker-compose.yml`

**Interfaces:**
- Consumes: model update references.
- Produces: aggregate reference consumed by federated-learning/gateway.
- Produces: full Compose environment.

- [ ] **Step 1: Write failing secure-aggregate test**

```python
def test_secure_aggregate(client):
    response = client.post(
        "/api/v1/privacy/secure-aggregate",
        headers={"Idempotency-Key": "privacy-1"},
        json={
            "trainingTaskId": "fl_task_001",
            "roundId": 1,
            "updates": [
                {
                    "participantDid": f"did:vpp:participant:{i}",
                    "modelUpdateUri": f"memory://updates/{i}.json",
                    "updateHash": f"sha256:update{i}",
                }
                for i in range(3)
            ],
            "privacyMode": "secure_masking",
        },
    )
    data = response.json()["data"]
    assert data["aggregateId"].startswith("aggregate_")
    assert data["participantCount"] == 3
    assert data["privacyMode"] == "secure_masking"
```

- [ ] **Step 2: Implement all privacy modes**

Supported:

```text
homomorphic_demo
secure_masking
mpc_demo
```

All modes produce:

```json
{
  "aggregateId": "aggregate_...",
  "trainingTaskId": "fl_task_001",
  "roundId": 1,
  "aggregateResultUri": "memory://aggregates/fl_task_001/round_1/result.json",
  "aggregateHash": "sha256:...",
  "participantCount": 3,
  "privacyMode": "secure_masking"
}
```

- [ ] **Step 3: Implement encrypt and mask endpoints**

Both endpoints store queryable aggregate/update-protection records and never return a participant's raw update payload.

- [ ] **Step 4: Add errors**

```text
unsupported privacyMode -> 42203
updates count < 2 -> 42202
unknown aggregateId -> 40401
same key/different body -> 40901
```

- [ ] **Step 5: Run privacy tests**

```powershell
python -m pip install -e packages/common -e "services/privacy-compute[test]"
python -m pytest services/privacy-compute/tests -v
```

- [ ] **Step 6: Create `.env.example`**

```dotenv
VITE_API_BASE_URL=/api
GATEWAY_PORT=8000
METER_SERVICE_URL=http://meter-simulator:8000
INGESTION_SERVICE_URL=http://data-ingestion:8000
IDENTITY_SERVICE_URL=http://identity-did:8000
FL_SERVICE_URL=http://federated-learning:8000
PRIVACY_SERVICE_URL=http://privacy-compute:8000
LEDGER_SERVICE_URL=http://ledger-service:8000
AGENT_SERVICE_URL=http://ai-agent:8000
HTTP_TIMEOUT_SECONDS=5
```

- [ ] **Step 7: Create Compose with fixed ports**

Use host ports `3000`, `8000` through `8007` exactly as defined in the design. All backends use internal port `8000`.

- [ ] **Step 8: Validate and start**

```powershell
docker compose -f infra/docker-compose/docker-compose.yml config
docker compose -f infra/docker-compose/docker-compose.yml up --build -d
docker compose -f infra/docker-compose/docker-compose.yml ps
```

Expected by Day 4: nine services running.

- [ ] **Step 9: Commit**

```powershell
git add services/privacy-compute .env.example infra/docker-compose/docker-compose.yml
git commit -m "feat: add privacy mock and compose environment"
```

**Issue acceptance:**

- [ ] Five endpoints pass.
- [ ] Three privacy modes are independently testable.
- [ ] Compose config validates from Day 1.
- [ ] Nine services run by Day 4.
- [ ] No real secrets appear in `.env.example`.

---

### Task 7: ledger-service owner — in-memory hash chain

**GitHub Issue title:** `[P0][存证] 实现事件存证与 businessId 证据链 Mock`

**Owner:** ledger-service owner

**Dependencies:** Task 1 event types and common package.

**Files:**
- Create: `services/ledger-service/pyproject.toml`
- Create: `services/ledger-service/src/ledger_service/__init__.py`
- Create: `services/ledger-service/src/ledger_service/main.py`
- Create: `services/ledger-service/src/ledger_service/api.py`
- Create: `services/ledger-service/src/ledger_service/schemas.py`
- Create: `services/ledger-service/src/ledger_service/repository.py`
- Create: `services/ledger-service/src/ledger_service/service.py`
- Create: `services/ledger-service/tests/test_health.py`
- Create: `services/ledger-service/tests/test_events.py`
- Create: `services/ledger-service/tests/test_traces.py`
- Create: `services/ledger-service/Dockerfile`
- Create: `services/ledger-service/README.md`

**Interfaces:**
- Consumes: ledger event request.
- Produces: event record, transaction ID, block height, current/previous hash, and business trace.

- [ ] **Step 1: Write failing hash-chain test**

```python
def test_events_form_hash_chain(client):
    first = client.post(
        "/api/v1/ledger/events",
        headers={"Idempotency-Key": "ledger-1"},
        json={
            "eventType": "meter_data_collected",
            "businessId": "demo_001",
            "subjectDid": "did:vpp:operator:001",
            "payloadHash": "sha256:data001",
            "payloadUri": "memory://batch_001",
            "description": "meter batch collected",
            "metadata": {"readingBatchId": "batch_001"},
        },
    ).json()["data"]
    second = client.post(
        "/api/v1/ledger/events",
        headers={"Idempotency-Key": "ledger-2"},
        json={
            "eventType": "data_asset_registered",
            "businessId": "demo_001",
            "subjectDid": "did:vpp:operator:001",
            "payloadHash": "sha256:asset001",
            "payloadUri": "memory://asset_001",
            "description": "asset registered",
            "metadata": {"assetId": "asset_001"},
        },
    ).json()["data"]
    event = client.get(f"/api/v1/ledger/events/{second['eventId']}").json()["data"]
    assert event["previousHash"] == first["currentHash"]
```

- [ ] **Step 2: Implement allowed event catalog**

Accept the fixed event types from `module-contracts.md`, including:

```text
meter_data_collected
data_asset_registered
auth_requested
auth_approved
training_started
model_update_submitted
secure_aggregation_finished
global_model_created
agent_prediction_called
agent_report_generated
```

- [ ] **Step 3: Implement deterministic event hashing**

Hash canonical JSON containing:

```text
eventId
eventType
businessId
subjectDid
payloadHash
payloadUri
timestamp
previousHash
metadata
```

Store events by ID and by `businessId`; increment an in-memory `blockHeight`.

- [ ] **Step 4: Implement idempotency and duplicate rules**

```text
same Idempotency-Key + same body -> return same event
same Idempotency-Key + different body -> 40901
same eventType + businessId + payloadHash without same key -> 40903
```

- [ ] **Step 5: Run tests**

```powershell
python -m pip install -e packages/common -e "services/ledger-service[test]"
python -m pytest services/ledger-service/tests -v
```

Expected: all PASS.

- [ ] **Step 6: Build and commit**

```powershell
docker build -f services/ledger-service/Dockerfile -t vpp/ledger-service:week1 .
git add services/ledger-service
git commit -m "feat: add in-memory audit hash chain"
```

**Issue acceptance:**

- [ ] Four endpoints pass.
- [ ] At least seven ordered event types form a valid business chain.
- [ ] Duplicate and unknown-resource errors pass.
- [ ] Event data contains no raw meter plaintext or raw model parameters.

---

### Task 8: ai-agent owner — prediction, strategy, audit Mock

**GitHub Issue title:** `[P0][Agent] 实现预测、交易策略与审计报告 Mock`

**Owner:** ai-agent owner

**Dependencies:** Task 1; consumes model and evidence identifiers from gateway.

**Files:**
- Create: `services/ai-agent/pyproject.toml`
- Create: `services/ai-agent/src/ai_agent/__init__.py`
- Create: `services/ai-agent/src/ai_agent/main.py`
- Create: `services/ai-agent/src/ai_agent/api.py`
- Create: `services/ai-agent/src/ai_agent/schemas.py`
- Create: `services/ai-agent/src/ai_agent/repository.py`
- Create: `services/ai-agent/src/ai_agent/service.py`
- Create: `services/ai-agent/tests/test_health.py`
- Create: `services/ai-agent/tests/test_prediction.py`
- Create: `services/ai-agent/tests/test_audit.py`
- Create: `services/ai-agent/Dockerfile`
- Create: `services/ai-agent/README.md`
- Modify: `demo/video-storyboard.md`

**Interfaces:**
- Consumes: model version, scenario inputs, business ID, and evidence event IDs.
- Produces: prediction, strategy, audit answer, and report.

- [ ] **Step 1: Write failing prediction/report tests**

```python
def test_predict_and_report(client):
    predicted = client.post(
        "/api/v1/agent/predict",
        headers={"Idempotency-Key": "prediction-1"},
        json={
            "modelVersion": "global_model_v1",
            "scenario": "day_ahead_trading",
            "input": {
                "date": "2026-07-17",
                "temperature": 34,
                "marketPrice": 0.68,
            },
        },
    ).json()["data"]
    assert predicted["predictionId"].startswith("prediction_")
    assert predicted["predictedCapacityKw"] > 0

    report = client.post(
        "/api/v1/agent/audit-report",
        headers={"Idempotency-Key": "report-1"},
        json={
            "businessId": "demo_001",
            "modelVersion": "global_model_v1",
            "evidenceEventIds": ["evt_001", "evt_002"],
            "reportType": "transaction_audit",
        },
    ).json()["data"]
    assert report["auditReportId"].startswith("report_")
    assert report["riskLevel"] in {"low", "medium", "high"}
```

- [ ] **Step 2: Implement stable formulas/templates**

Seed the week-one known model registry with:

```python
known_models = {"global_model_v1"}
```

Requests for any other model version return `40404`.

Prediction formula:

```text
predictedCapacityKw = round(100000 + temperature * 500 - marketPrice * 1000, 2)
confidence = 0.92
```

Strategy references `predictionId` and returns:

```text
declaredCapacityKw = predictedCapacityKw * 0.90
safetyMargin = 0.10
priceRecommendation = marketPrice
```

- [ ] **Step 3: Implement audit outputs**

Audit question response:

```json
{
  "answer": "关键采集、授权、训练、聚合、模型和 Agent 事件均已存证。",
  "evidenceEventIds": ["evt_001", "evt_002"],
  "confidence": 0.95
}
```

Audit-question request contains `businessId`, `modelVersion`, `evidenceEventIds`, and `question`. Audit-report request contains `businessId`, `modelVersion`, `evidenceEventIds`, and `reportType`.

Audit report includes:

```text
auditReportId
title
summary
riskLevel
recommendations[]
```

- [ ] **Step 4: Add error and idempotency tests**

```text
modelVersion not starting global_model_v -> 40404
missing businessId -> 40002
same key/different request -> 40901
```

- [ ] **Step 5: Run tests**

```powershell
python -m pip install -e packages/common -e "services/ai-agent[test]"
python -m pytest services/ai-agent/tests -v
```

- [ ] **Step 6: Update demo storyboard**

Add the exact result fields the presenter points to:

```text
predictionId
predictedCapacityKw
strategyId
safetyMargin
auditReportId
riskLevel
recommendations
```

- [ ] **Step 7: Build and commit**

```powershell
docker build -f services/ai-agent/Dockerfile -t vpp/ai-agent:week1 .
git add services/ai-agent demo/video-storyboard.md
git commit -m "feat: add agent business mock outputs"
```

**Issue acceptance:**

- [ ] Five endpoints pass.
- [ ] Outputs are deterministic enough for demonstration.
- [ ] Report references model/evidence context.
- [ ] Storyboard matches actual fields.

---

### Task 9: api-gateway owner — orchestration, CI, integration, E2E

**GitHub Issue title:** `[P0][网关][测试] 实现全链路编排、状态、CI 与 E2E`

**Owner:** api-gateway owner

**Dependencies:** Tasks 1-8; can begin clients from frozen fixtures on Day 1.

**Files:**
- Create: `services/api-gateway/pyproject.toml`
- Create: `services/api-gateway/src/api_gateway/__init__.py`
- Create: `services/api-gateway/src/api_gateway/main.py`
- Create: `services/api-gateway/src/api_gateway/api.py`
- Create: `services/api-gateway/src/api_gateway/schemas.py`
- Create: `services/api-gateway/src/api_gateway/repository.py`
- Create: `services/api-gateway/src/api_gateway/settings.py`
- Create: `services/api-gateway/src/api_gateway/clients/__init__.py`
- Create: `services/api-gateway/src/api_gateway/clients/base.py`
- Create: `services/api-gateway/src/api_gateway/clients/meter.py`
- Create: `services/api-gateway/src/api_gateway/clients/ingestion.py`
- Create: `services/api-gateway/src/api_gateway/clients/identity.py`
- Create: `services/api-gateway/src/api_gateway/clients/fl.py`
- Create: `services/api-gateway/src/api_gateway/clients/privacy.py`
- Create: `services/api-gateway/src/api_gateway/clients/ledger.py`
- Create: `services/api-gateway/src/api_gateway/clients/agent.py`
- Create: `services/api-gateway/src/api_gateway/workflows/__init__.py`
- Create: `services/api-gateway/src/api_gateway/workflows/demo.py`
- Create: `services/api-gateway/tests/test_health.py`
- Create: `services/api-gateway/tests/test_demo_workflow.py`
- Create: `services/api-gateway/tests/test_demo_errors.py`
- Create: `services/api-gateway/Dockerfile`
- Create: `services/api-gateway/README.md`
- Modify: `.github/workflows/ci.yml`
- Create: `tests/integration/test_openapi_coverage.py`
- Create: `tests/e2e/test_demo_flow.py`
- Create: `tests/e2e/test_demo_failures.py`
- Create: `tests/e2e/README.md`

**Interfaces:**
- Consumes: every backend HTTP API.
- Produces: `POST /api/v1/demo/run`, status query, integration/CI/E2E evidence.

- [ ] **Step 1: Write workflow test with `httpx.MockTransport`**

```python
import httpx
import pytest

from api_gateway.workflows.demo import DemoWorkflow


@pytest.mark.asyncio
async def test_demo_workflow_returns_linked_ids(mock_transport):
    async with httpx.AsyncClient(transport=mock_transport) as client:
        result = await DemoWorkflow(client=client).run(
            business_id="demo_test",
            trace_id="trace_test",
            request={
                "scenario": "vpp_day_ahead_trading",
                "participants": [
                    "did:vpp:load-aggregator:001",
                    "did:vpp:renewable-plant:001",
                    "did:vpp:storage:001",
                ],
                "meterCount": 3,
                "trainingRounds": 3,
            },
        )
    assert result.businessId == "demo_test"
    assert result.assetId.startswith("asset_")
    assert result.globalModelVersion.startswith("global_model_v")
```

- [ ] **Step 2: Implement settings**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    meter_service_url: str = "http://localhost:8001"
    ingestion_service_url: str = "http://localhost:8002"
    identity_service_url: str = "http://localhost:8003"
    fl_service_url: str = "http://localhost:8004"
    privacy_service_url: str = "http://localhost:8005"
    ledger_service_url: str = "http://localhost:8006"
    agent_service_url: str = "http://localhost:8007"
    http_timeout_seconds: float = 5.0
```

- [ ] **Step 3: Configure gateway CORS**

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Idempotency-Key", "X-Trace-Id"],
)
```

Production Compose traffic uses the frontend Nginx `/api` proxy, so business services do not enable browser CORS.

- [ ] **Step 4: Implement base client behavior**

Every downstream request passes:

```text
X-Trace-Id: current trace ID
X-Caller-Did: did:vpp:operator:001
Idempotency-Key: <businessId>:<stage>
```

Map:

```text
httpx.TimeoutException -> 50401
httpx.ConnectError -> 50203
non-unified response -> 50202
downstream nonzero code -> preserve recognized code or map to 50201
```

- [ ] **Step 5: Implement exact workflow states**

```text
CREATED
COLLECTING
DATA_REGISTERED
AUTHORIZED
TRAINING
MODEL_READY
AGENT_COMPLETED
COMPLETED
FAILED
```

Store:

```python
businessId -> {
    request_hash,
    status,
    currentStage,
    lastEventType,
    result,
    error,
    traceId,
}
```

- [ ] **Step 6: Implement orchestration**

The workflow follows the 15-step sequence in `week-one-mock-delivery.md`. Record at least:

```text
meter_data_collected
data_asset_registered
auth_requested
auth_approved
training_started
secure_aggregation_finished
global_model_created
agent_prediction_called
agent_report_generated
```

Before calling audit question/report, query `GET /api/v1/ledger/traces/{businessId}` and pass its `eventId` values as `evidenceEventIds`. Use the generated `globalModelVersion` as `modelVersion`. The Agent must not call ledger-service directly.

- [ ] **Step 7: Add route tests**

Verify:

```text
success returns all IDs and metrics
same key/same request returns same businessId
same key/different request returns 40901
status query returns COMPLETED
downstream timeout returns 50401
downstream connect failure returns 50203
traceId is preserved through response
```

- [ ] **Step 8: Run gateway tests**

```powershell
python -m pip install -e packages/common -e "services/api-gateway[test]"
python -m pytest services/api-gateway/tests -v
```

Expected: all PASS.

- [ ] **Step 9: Upgrade CI**

Add backend matrix, frontend build, contract test, and Compose config jobs from the master plan.

- [ ] **Step 10: Add E2E**

Implement success, status, idempotency, evidence-chain, and stopped-privacy-service tests exactly as specified in the master plan.

- [ ] **Step 11: Run full verification**

```powershell
python -m pytest packages/common/tests services tests/integration -v
docker compose -f infra/docker-compose/docker-compose.yml up --build -d
python -m pytest tests/e2e -v
```

Expected: all PASS.

- [ ] **Step 12: Commit in reviewable units**

```powershell
git add services/api-gateway
git commit -m "feat: add gateway mock orchestration"

git add .github/workflows/ci.yml tests/integration
git commit -m "ci: validate services and contracts"

git add tests/e2e
git commit -m "test: add full mock flow e2e"
```

**Issue acceptance:**

- [ ] Three gateway endpoints pass.
- [ ] Seven downstream clients use HTTP.
- [ ] Status, errors, tracing, and idempotency pass.
- [ ] CI validates all modules and frontend build.
- [ ] Compose E2E success and failure drills pass.

---

### Task 10: web-dashboard owner — beginner-friendly one-page console

**GitHub Issue title:** `[P0][前端] 实现 Vue 一键全链路 Mock 演示页`

**Owner:** web-dashboard owner

**Dependencies:** Frozen gateway examples; real gateway by Day 5.

**Files:**
- Create: `apps/web-dashboard/package.json`
- Create: `apps/web-dashboard/package-lock.json`
- Create: `apps/web-dashboard/index.html`
- Create: `apps/web-dashboard/vite.config.js`
- Create: `apps/web-dashboard/src/main.js`
- Create: `apps/web-dashboard/src/App.vue`
- Create: `apps/web-dashboard/src/api/gateway.js`
- Create: `apps/web-dashboard/src/components/DemoForm.vue`
- Create: `apps/web-dashboard/src/components/FlowSteps.vue`
- Create: `apps/web-dashboard/src/components/ResultSummary.vue`
- Create: `apps/web-dashboard/src/components/ErrorPanel.vue`
- Create: `apps/web-dashboard/src/styles.css`
- Create: `apps/web-dashboard/Dockerfile`
- Create: `apps/web-dashboard/nginx.conf`
- Create: `apps/web-dashboard/README.md`

**Interfaces:**
- Consumes: only `POST /api/v1/demo/run` and `GET /api/v1/demo/status/{businessId}`.
- Produces: browser interaction and evidence screenshots.

- [ ] **Step 1: Scaffold**

```powershell
cd apps/web-dashboard
npm create vite@latest . -- --template vue
npm install
npm install element-plus axios
```

Remove the generated demo components and assets.

- [ ] **Step 2: Implement gateway client**

```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
})

export async function runDemo(payload, idempotencyKey) {
  const response = await api.post('/v1/demo/run', payload, {
    headers: { 'Idempotency-Key': idempotencyKey },
  })
  return response.data
}

export async function getDemoStatus(businessId) {
  const response = await api.get(`/v1/demo/status/${businessId}`)
  return response.data
}
```

- [ ] **Step 3: Implement initial form state**

```javascript
const form = reactive({
  scenario: 'vpp_day_ahead_trading',
  participants: [
    'did:vpp:load-aggregator:001',
    'did:vpp:renewable-plant:001',
    'did:vpp:storage:001',
  ],
  meterCount: 3,
  trainingRounds: 3,
})
```

- [ ] **Step 4: Implement seven-stage display**

Stages:

```text
源端采集
数据接入
身份授权
联邦训练
隐私聚合
模型生成
Agent 输出
```

Use Element Plus `el-steps`, `el-card`, `el-descriptions`, `el-table`, `el-alert`, and `el-tag`.

- [ ] **Step 5: Implement loading and failure behavior**

```javascript
loading.value = true
error.value = null
try {
  response.value = await runDemo(form, crypto.randomUUID())
  businessId.value = response.value.data.businessId
} catch (err) {
  error.value = err.response?.data || {
    code: 50001,
    message: err.message,
    traceId: 'unavailable',
  }
} finally {
  loading.value = false
}
```

Disable the start button while `loading` is true.

- [ ] **Step 6: Render exact result fields**

Display:

```text
businessId
readingBatchId
assetId
authId
trainingTaskId
globalModelVersion
metrics.mae
metrics.rmse
metrics.mape
predictionId
auditReportId
ledgerTxIds
traceId
```

- [ ] **Step 7: Add status query**

Allow the user to enter or reuse `businessId` and call `getDemoStatus()`. Do not trigger a second run.

- [ ] **Step 8: Configure Vite development proxy**

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 9: Build**

```powershell
npm run build
```

Expected: exit code `0`.

- [ ] **Step 10: Add production Docker and Nginx proxy**

`apps/web-dashboard/Dockerfile`:

```dockerfile
FROM node:24-alpine AS build
WORKDIR /app
COPY apps/web-dashboard/package*.json ./
RUN npm ci
COPY apps/web-dashboard/ ./
RUN npm run build

FROM nginx:1.28-alpine
COPY apps/web-dashboard/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
```

`apps/web-dashboard/nginx.conf`:

```nginx
server {
  listen 80;
  root /usr/share/nginx/html;
  index index.html;

  location / {
    try_files $uri $uri/ /index.html;
  }

  location /api/ {
    proxy_pass http://api-gateway:8000/api/;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Host $host;
  }
}
```

- [ ] **Step 11: Verify Compose integration**

Open:

```text
http://localhost:3000
```

Verify a full run, a status query, and a downstream-failure display.

- [ ] **Step 12: Capture evidence and commit**

Add README screenshots or linked evidence for:

```text
initial page
successful full flow
failed flow with error code and traceId
```

```powershell
git add apps/web-dashboard
git commit -m "feat: add one-click mock demo dashboard"
```

**Issue acceptance:**

- [ ] Frontend calls only gateway.
- [ ] One-click success flow displays all required results.
- [ ] Loading prevents duplicate clicks.
- [ ] Failure shows stage/code/message/traceId.
- [ ] Status query works after page refresh.
- [ ] `npm run build` and Compose access pass.

---

## Owner PR Evidence Template

Every owner copies this into the PR:

```markdown
## Verification

- Module tests:
  - Command:
  - Result:
- Health:
  - Request:
  - Response:
- Normal path:
  - Request:
  - Response:
- Failure path:
  - Request:
  - Response code and business code:
- Idempotency:
  - Same-key same-body result:
  - Same-key different-body result:
- Docker:
  - Build command:
  - Startup/health result:
- Gateway integration:
  - Status:
- Contract documents:
  - No change / updated files:
```

## Merge Order

```text
Technical lead contracts/common
-> all service health baselines
-> module normal paths
-> module errors/state/idempotency
-> gateway HTTP workflow
-> Compose
-> frontend real integration
-> CI and E2E
-> clean-environment acceptance
```
