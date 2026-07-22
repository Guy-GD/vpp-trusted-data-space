import hashlib
import json

from fastapi.testclient import TestClient

from app.main import app
from app.service import IdentityService


client = TestClient(app)
PUBLIC_KEY = "bW9jay1wdWJsaWMta2V5"


def show(title: str, response) -> dict:
    response.raise_for_status()
    body = response.json()
    print(f"\n=== {title} ===")
    print(json.dumps(body, ensure_ascii=False, indent=2))
    return body["data"]


def main() -> None:
    requester_payload = {
        "name": "VPP 运营方",
        "type": "operator",
        "publicKey": PUBLIC_KEY,
    }
    requester_headers = {
        "Idempotency-Key": "demo-create-requester",
        "X-Trace-Id": "trace-demo-requester",
    }
    requester_response = client.post(
        "/api/v1/identity/subjects",
        json=requester_payload,
        headers=requester_headers,
    )
    requester = show("1. 注册请求方 DID", requester_response)

    replay = client.post(
        "/api/v1/identity/subjects",
        json=requester_payload,
        headers=requester_headers,
    )
    show("2. 使用同一幂等键重放（DID 不变）", replay)

    owner = show(
        "3. 注册数据所有者 DID",
        client.post(
            "/api/v1/identity/subjects",
            json={
                "name": "负荷聚合商",
                "type": "load_aggregator",
                "publicKey": PUBLIC_KEY,
            },
        ),
    )

    show(
        "4. 注册设备 DID",
        client.post(
            "/api/v1/identity/devices",
            json={
                "deviceName": "园区智能电表 01",
                "deviceType": "smart_meter",
                "ownerDid": owner["subjectDid"],
                "publicKey": PUBLIC_KEY,
            },
        ),
    )

    payload_hash = "sha256:" + hashlib.sha256(b"demo-energy-data").hexdigest()
    signature = IdentityService.make_mock_signature(PUBLIC_KEY, payload_hash)
    show(
        "5. 验证请求方签名",
        client.post(
            "/api/v1/identity/verify",
            json={
                "subjectDid": requester["subjectDid"],
                "signature": signature,
                "payloadHash": payload_hash,
            },
        ),
    )

    authorization = show(
        "6. 创建授权申请",
        client.post(
            "/api/v1/auth/requests",
            json={
                "requesterDid": requester["subjectDid"],
                "ownerDid": owner["subjectDid"],
                "assetId": "asset_demo_load_curve",
                "purpose": "federated_training_for_day_ahead_trading",
                "expireAt": "2099-12-31T23:59:59+08:00",
            },
            headers={"X-Caller-Did": requester["subjectDid"]},
        ),
    )

    show(
        "7. 数据所有者批准授权",
        client.post(
            f"/api/v1/auth/requests/{authorization['authId']}/approve",
            json={"approverDid": owner["subjectDid"]},
            headers={"X-Caller-Did": owner["subjectDid"]},
        ),
    )

    show(
        "8. 查询最终授权状态",
        client.get(f"/api/v1/auth/requests/{authorization['authId']}"),
    )


if __name__ == "__main__":
    main()

