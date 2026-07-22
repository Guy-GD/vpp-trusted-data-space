import json
import os
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


def show_mock_data(title: str, response: httpx.Response) -> dict[str, Any]:
    response.raise_for_status()
    data = response.json()["data"]
    print(f"\n=== {title} ===")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return data


def main() -> None:
    run_id = uuid4().hex
    expire_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()

    with httpx.Client(
        base_url=BASE_URL,
        timeout=HTTP_TIMEOUT,
        trust_env=False,
    ) as client:
        authorization = show_mock_data(
            "1. 创建 requested 授权",
            client.post(
                "/api/v1/auth/requests",
                json={
                    "requesterDid": REQUESTER_DID,
                    "ownerDid": OWNER_DID,
                    "assetId": f"asset_demo_{run_id}",
                    "purpose": "federated_training_demo",
                    "expireAt": expire_at,
                },
                headers={
                    "Idempotency-Key": f"demo-create-{run_id}",
                    "X-Caller-Did": REQUESTER_DID,
                },
            ),
        )
        assert authorization["status"] == "requested"

        approved = show_mock_data(
            "2. 所有者批准授权",
            client.post(
                f"/api/v1/auth/requests/{authorization['authId']}/approve",
                json={
                    "approverDid": OWNER_DID,
                    "decision": "approved",
                    "reason": "week1 repeatable mock demo",
                },
                headers={
                    "Idempotency-Key": f"demo-approve-{run_id}",
                    "X-Caller-Did": OWNER_DID,
                },
            ),
        )
        assert approved["status"] == "approved"

        queried = show_mock_data(
            "3. 查询最终授权",
            client.get(f"/api/v1/auth/requests/{authorization['authId']}"),
        )
        assert queried["authId"] == authorization["authId"]
        assert queried["status"] == "approved"


if __name__ == "__main__":
    main()
