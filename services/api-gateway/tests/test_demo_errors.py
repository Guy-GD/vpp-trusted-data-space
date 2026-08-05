from fastapi.testclient import TestClient

from api_gateway.main import app


client = TestClient(app)



def test_business_not_found():

    response = client.get(
        "/api/v1/demo/status/not_exists"
    )


    assert response.status_code == 404