# Identity DID Review Follow-ups Design

**Date:** 2026-07-26
**Base:** `develop` after PR #16
**Scope:** `services/identity-did`

## Goal

Address the non-blocking review findings from PR #16 without changing the
seven public routes, request/response schemas, successful behavior, or Mock
service boundaries.

## Changes

### 1. Explicit DID guard

`IdentityService.verify_identity` will not use `assert` for a production-path
precondition. If neither `subjectDid` nor `deviceDid` is present when the
service is called directly, it will raise
`ServiceError(ErrorCode.INVALID_REQUEST)`.

Normal HTTP requests remain protected first by the existing Pydantic
`model_validator`, so the public API behavior remains `40001 invalid request`.

### 2. Bounded authorization ID retries

Authorization creation will replace the unbounded `while True` loop with at
most three attempts:

1. Generate an `auth_` ID through `vpp_common.new_id`.
2. Ask the repository to create the record atomically.
3. Return immediately when creation succeeds.
4. After three consecutive collisions, raise
   `ServiceError(ErrorCode.INTERNAL_ERROR)`.

The existing collision-recovery behavior remains: one or two collisions do
not fail the request and never overwrite an existing authorization. The new
bound prevents a broken ID generator from keeping a request alive forever.

### 3. Shared Mock public-key contract

The module README will state that all four seeded subjects use the literal
public-key string:

```text
bW9jay1wdWJsaWMta2V5
```

It will also state that Mock verification hashes that literal string directly
with `":" + payloadHash`; callers must not Base64-decode it before applying
the documented Mock formula. This is an integration convention only, not a
real credential or production cryptographic design.

## Tests

Add focused regression coverage before implementation:

- Construct an invalid verification request through the service boundary and
  verify it raises `40001`, proving behavior does not depend on `assert`.
- Force two authorization ID collisions followed by a unique ID and verify
  creation succeeds without overwriting existing records.
- Force three consecutive collisions and verify the service terminates with
  `50001` after exactly three attempts.
- Extend delivery-document checks to require the shared Mock public-key value
  and literal-string signing convention.

Run the complete identity-did module suite and the shared contract suite after
the focused tests pass.

## Non-goals

- No new endpoint or schema field.
- No change to the successful authorization response.
- No real DID resolver, asymmetric cryptography, or per-subject key store.
- No database, Redis, or distributed retry mechanism.
