from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from identity_did.main import create_app
from identity_did.repository import InMemoryRepository


class MutableClock:
    def __init__(self) -> None:
        self.current = datetime(2030, 1, 1, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self.current

    def now_iso(self) -> str:
        return self.current.isoformat(timespec="milliseconds").replace(
            "+00:00", "Z"
        )

    def advance(self, delta: timedelta) -> None:
        self.current += delta


@pytest.fixture
def repository() -> InMemoryRepository:
    return InMemoryRepository()


@pytest.fixture
def clock() -> MutableClock:
    return MutableClock()


@pytest.fixture
def future_expiry(clock: MutableClock) -> str:
    return (clock.now() + timedelta(days=10)).isoformat()


@pytest.fixture
def app(repository: InMemoryRepository, clock: MutableClock) -> FastAPI:
    return create_app(repository, clock)


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
