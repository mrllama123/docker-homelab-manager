import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(session) -> TestClient:
    from src.db import get_session
    from src.main import app

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    yield TestClient(app)
    app.dependency_overrides.clear()
