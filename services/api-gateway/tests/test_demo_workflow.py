from fastapi.testclient import TestClient

from api_gateway.main import app


client = TestClient(app)



def test_demo_workflow():

    payload = {
        "scenario": "vpp_day_ahead_trading",
        "participants": [
            "aggregator-A",
            "energy-user-B",
        ],
        "meterCount": 3,
        "trainingRounds": 2,
    }


    response = client.post(
        "/api/v1/demo/run",
        json=payload,
    )


    assert response.status_code == 200


    body = response.json()


    assert body["code"] == 0


    data = body["data"]


    assert (
        data["status"]
        == "COMPLETED"
    )


    assert (
        data["assetId"]
        .startswith("asset_")
    )


    assert (
        data["globalModelVersion"]
        .startswith("model_")
    )