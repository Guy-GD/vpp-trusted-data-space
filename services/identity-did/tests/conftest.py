import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from identity_did.main import create_app


@pytest.fixture
def app() -> FastAPI:
    return create_app()


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
