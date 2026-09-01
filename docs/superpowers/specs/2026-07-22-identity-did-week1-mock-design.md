# Identity DID Week 1 Mock Design

## Goal

Bring `services/identity-did` into exact alignment with the frozen Week 1 task, public API contracts, and the identity/DID Issue. The service remains an in-memory Mock for repeatable demos and cross-module integration; it does not introduce a database, a real DID chain, JWT, or production cryptography.

## Scope

The service exposes exactly these seven endpoints:

```text
POST /api/v1/identity/subjects
POST /api/v1/identity/devices
POST /api/v1/identity/verify
POST /api/v1/auth/requests
POST /api/v1/auth/requests/{authId}/approve
GET  /api/v1/auth/requests/{authId}
GET  /health
```

The existing `app` package is replaced completely. Useful behavior and tests are migrated, while obsolete files are removed so that there is only one application entry point and one implementation of each contract.

## Package and File Layout

```text
services/identity-did/
├── pyproject.toml
├── Dockerfile
├── README.md
├── scripts/
│   └── demo.py
├── src/identity_did/
│   ├── __init__.py
│   ├── main.py
│   ├── api.py
│   ├── schemas.py
│   ├── repository.py
│   └── service.py
└── tests/
    ├── conftest.py
    ├── test_health.py
    ├── test_identity.py
    └── test_authorization.py
```

`pyproject.toml` requires Python `>=3.11,<3.12`, declares the frozen FastAPI/Pydantic/Uvicorn ranges, and depends on `vpp-common==0.1.0`. The `test` optional dependencies declare httpx and pytest in the frozen ranges. The official editable install remains:

```powershell
python -m pip install -e packages/common -e "services/identity-did[test]"
```

## Component Responsibilities

### `main.py`

Creates the FastAPI application, installs `vpp_common.install_exception_handlers`, and includes the API router. It contains no business logic. A small application factory permits isolated test repositories and clocks.

### `api.py`

Defines the seven public routes, extracts `Idempotency-Key` and `X-Caller-Did`, calls services, and wraps successful data with `vpp_common.success`. Business failures are raised as `vpp_common.ServiceError`.

### `schemas.py`

Defines Pydantic v2 request DTOs and typed subject, device, authorization, and idempotency records. Public fields use the frozen camelCase names. Authorization responses always carry the contract fields, including nullable `decision`, `reason`, and `approvedAt` before a decision is made.

### `repository.py`

Owns the exact in-memory dictionaries:

```text
subjects: dict[str, SubjectRecord]
devices: dict[str, DeviceRecord]
authorizations: dict[str, AuthorizationRecord]
idempotency: dict[str, StoredResult]
```

Every new repository is seeded with these active demo subjects so gateway integration needs no setup calls:

```text
did:vpp:operator:001
did:vpp:load-aggregator:001
did:vpp:renewable-plant:001
did:vpp:storage:001
```

New subject and device DIDs are generated dynamically without colliding with seeds. Authorization IDs use `vpp_common.new_id("auth_")`.

### `service.py`

Contains identity registration and Mock verification, authorization state transitions, expiry refresh, caller checks, and idempotency replay/conflict handling. The current time is injected so expiry tests are deterministic.

## Authorization State and Expiry

The only allowed transitions are:

```text
requested -> approved
requested -> rejected
approved  -> expired when expireAt is in the past
```

Creating an authorization whose `expireAt` is already in the past returns `40003`. Before an authorization is read or approved, the service refreshes its state. If an approved authorization has expired, its stored state becomes `expired` and the request raises `40303 authorization expired`. This makes the state transition persistent while satisfying the Issue requirement that an expired authorization return `40303`. Re-approving or re-rejecting a non-expired decided authorization returns `40902`.

Approval responses use `decision`, `reason`, and `approvedAt`; `status` matches the decision (`approved` or `rejected`).

## Identity and Mock Verification

Registration returns the frozen public fields and never exposes stored public keys. Device registration requires an active owner DID. Verification accepts exactly one of `subjectDid` or `deviceDid`, checks the frozen SHA-256 text format, and compares a deterministic Mock signature derived from the stored public key and payload hash. This remains explicitly non-production behavior.

The verification POST participates in the same idempotency mechanism as the other POST routes, as required by the public OpenAPI contract.

## Common Contract Integration

The service does not duplicate response, error, trace, ID, or common time helpers. It uses:

- `success` for successful envelopes, including the required UTC `timestamp`;
- `ServiceError` and `ErrorCode` for stable failures and HTTP status mapping;
- `install_exception_handlers` for validation, unhandled errors, trace propagation, and the `X-Trace-Id` response header;
- `new_id` for authorization IDs;
- `utc_now_iso` for stored timestamps.

Unknown or malformed incoming trace IDs are replaced according to the common package. Module-specific request and record schemas remain inside `identity_did`.

## Required Errors

Automated tests cover at least:

```text
unknown DID                              -> 40102
expired authorization                    -> 40303
approve already approved                 -> 40902
unknown authId                            -> 40401
same idempotency key, different request  -> 40901
invalid signature                        -> 40103
invalid payload hash                     -> 40104
non-owner approval                       -> 40301
past expireAt at creation                -> 40003
```

## Test Strategy

Tests are written first against the new import path and frozen behavior. Fixtures construct a fresh repository and application per test, preventing shared state and order dependence. A controllable clock verifies `requested -> approved -> expired` without sleeping.

The acceptance sequence is:

```powershell
python -m pip install -e packages/common -e "services/identity-did[test]"
python -m pytest services/identity-did/tests -v
python -m pytest packages/common/tests tests/integration/test_contract_docs.py -v
docker build -f services/identity-did/Dockerfile -t vpp/identity-did:week1 .
```

The seven routes are also enumerated from the application during tests so an accidental extra or missing public business route is visible. FastAPI's documentation routes are not counted as service endpoints.

## Docker and Documentation

The Docker image uses Python 3.11, copies and installs both `packages/common` and `services/identity-did` from the repository build context, exposes port 8000, and starts `identity_did.main:app` with Uvicorn.

The README documents the official editable install, local start, tests, seeded DIDs, repeatable demo, Docker build/run, all seven endpoints, and the failure-path review checklist. It does not instruct developers to create a second module-local virtual environment.

## Migration and Compatibility

The obsolete `app` package, `requirements.txt`, and superseded split test files are removed after their useful coverage is represented in the new test suite. The demo script is retained and updated to use seeded DIDs and the new `requested` state. No compatibility wrapper for `app.main` is kept because the task mandates a single installable `identity_did` package.

## Completion Criteria

The implementation is complete only when:

1. all seven endpoints satisfy the frozen request and response contracts;
2. all four seeded DIDs are usable immediately after startup;
3. authorization approval, rejection, automatic expiry, and all five exact task errors are tested;
4. the service uses `vpp_common` instead of local common-protocol copies;
5. the official editable install and test commands pass on Python 3.11;
6. the Docker image builds and its documented health check works;
7. the README contains repeatable normal- and failure-path evidence instructions;
8. no real credentials, production infrastructure, or unapproved endpoints are added.
