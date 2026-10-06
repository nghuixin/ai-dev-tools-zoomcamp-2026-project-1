import pytest
from fastapi.testclient import TestClient

from app.deps import get_store
from app.main import app
from app.store import Store


@pytest.fixture
def store() -> Store:
    memory = Store()
    memory.seed()
    return memory


@pytest.fixture
def client(store: Store) -> TestClient:
    app.dependency_overrides[get_store] = lambda: store
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
