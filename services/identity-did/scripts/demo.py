import json
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import httpx


BASE_URL = os.getenv("IDENTITY_DID_BASE_URL", "http://127.0.0.1:8003").rstrip(
    "/"
)
HTTP_TIMEOUT = float(os.getenv("IDENTITY_DID_TIMEOUT", "10"))
REQUESTER_DID = "did:vpp:operator:001"
OWNER_DID = "did:vpp:load-aggregator:001"


class DemoError(RuntimeError):
    """A readable failure from the repeatable Mock demonstration."""


def _request_url(response: httpx.Response) -> str:
    try:
        return str(response.request.url)
    except RuntimeError:
        return "unknown request URL"


def response_data(response: httpx.Response) -> dict[str, Any]:
    request_url = _request_url(response)
    try:
        body = response.json()
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise DemoError(
            f"{request_url} returned HTTP {response.status_code} with invalid JSON"
        ) from exc

    if not isinstance(body, dict):
        raise DemoError(
            f"{request_url} returned HTTP {response.status_code} without "
            "a response envelope"
        )

    code = body.get("code")
    message = body.get("message")
    if response.is_error or code != 0:
        raise DemoError(
            f"{request_url} returned HTTP {response.status_code}: "
            f"code={code!r}, message={message!r}"
        )

    data = body.get("data")
    if not isinstance(data, dict):
        raise DemoError(f"{request_url} returned a success envelope without data")
    return data


def show_mock_data(title: str, response: httpx.Response) -> dict[str, Any]:
    data = response_data(response)
    print(f"\n=== {title} ===")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return data


def require_status(
    data: dict[str, Any],
    expected: str,
    request_url: str,
) -> None:
    actual = data.get("status")
    if actual != expected:
        raise DemoError(
            f"{request_url} returned unexpected status {actual!r}; "
            f"expected {expected!r}"
        )


def run_demo(
    client: httpx.Client,
    *,
    run_id: str | None = None,
    expire_at: str | None = None,
) -> dict[str, Any]:
    active_run_id = run_id or uuid4().hex
    active_expiry = expire_at or (
        datetime.now(timezone.utc) + timedelta(hours=1)
    ).isoformat()

    create_path = "/api/v1/auth/requests"
    create_response = client.post(
        create_path,
        json={
            "requesterDid": REQUESTER_DID,
            "ownerDid": OWNER_DID,
            "assetId": f"asset_demo_{active_run_id}",
            "purpose": "federated_training_demo",
            "expireAt": active_expiry,
        },
        headers={
            "Idempotency-Key": f"demo-create-{active_run_id}",
            "X-Caller-Did": REQUESTER_DID,
        },
    )
    authorization = show_mock_data("1. 创建 requested 授权", create_response)
    require_status(authorization, "requested", _request_url(create_response))

    auth_id = authorization.get("authId")
    if not isinstance(auth_id, str) or not auth_id:
        raise DemoError(
            f"{_request_url(create_response)} returned no usable authId"
        )

    approve_path = f"/api/v1/auth/requests/{auth_id}/approve"
    approve_response = client.post(
        approve_path,
        json={
            "approverDid": OWNER_DID,
            "decision": "approved",
            "reason": "week1 repeatable mock demo",
        },
        headers={
            "Idempotency-Key": f"demo-approve-{active_run_id}",
            "X-Caller-Did": OWNER_DID,
        },
    )
    approved = show_mock_data("2. 所有者批准授权", approve_response)
    require_status(approved, "approved", _request_url(approve_response))

    query_path = f"/api/v1/auth/requests/{auth_id}"
    query_response = client.get(query_path)
    queried = show_mock_data("3. 查询最终授权", query_response)
    require_status(queried, "approved", _request_url(query_response))
    if queried.get("authId") != auth_id:
        raise DemoError(
            f"{_request_url(query_response)} returned a different authId"
        )
    return queried


def main() -> int:
    try:
        with httpx.Client(
            base_url=BASE_URL,
            timeout=HTTP_TIMEOUT,
            trust_env=False,
        ) as client:
            run_demo(client)
    except httpx.RequestError as exc:
        request_url = str(exc.request.url) if exc.request is not None else BASE_URL
        print(
            f"演示失败：请求 {request_url} 连接或超时：{exc}",
            file=sys.stderr,
        )
        return 1
    except DemoError as exc:
        print(f"演示失败：{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
