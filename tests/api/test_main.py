from fastapi.testclient import TestClient
import pytest
from docker.models.volumes import Volume


@pytest.fixture
def client():
    from src.api.main import app

    return TestClient(app)


def test_list_volumes(mocker, client):
    mock_get_volumes = mocker.patch(
        "src.api.main.get_volumes",
        return_value=[Volume(attrs={"Name": "test-volume"})],
    )
    response = client.get("/volumes")
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "test-volume",
            "shortId": "test-volume",
            "name": "test-volume",
            "attrs": {"Name": "test-volume"},
        }
    ]
    mock_get_volumes.assert_called_once()
