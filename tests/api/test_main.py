import pytest
from fastapi.testclient import TestClient

from celery import states
from docker.models.volumes import Volume


class MockAsyncResult:
    def __init__(self, status=states.PENDING, result="", id="test-task-id"):
        self.status = status
        self.result = result
        self.id = id


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


def test_create_backup_volume_not_found(mocker, client):
    mock_get_volume = mocker.patch(
        "src.api.main.get_volume",
        return_value=None,
    )
    mock_create_volume_backup = mocker.patch(
        "src.api.main.create_volume_backup.delay",
        return_value=MockAsyncResult(),
    )
    response = client.post("/backup/test-volume")
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Volume test-volume does not exist",
    }
    mock_get_volume.assert_called_once_with("test-volume")
    mock_create_volume_backup.assert_not_called()


def test_create_backup(mocker, client):
    mock_get_volume = mocker.patch(
        "src.api.main.get_volume",
        return_value=Volume(attrs={"Name": "test-volume"}),
    )
    mock_create_volume_backup = mocker.patch(
        "src.api.main.create_volume_backup.delay",
        return_value=MockAsyncResult(),
    )
    response = client.post("/backup/test-volume")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Backup of test-volume started",
        "task_id": "test-task-id",
    }
    mock_get_volume.assert_called_once_with("test-volume")
    mock_create_volume_backup.assert_called_once_with("test-volume")


def test_get_backup_status(mocker, client):
    mock_get_backup_status = mocker.patch(
        "src.api.main.create_volume_backup.AsyncResult",
        return_value=MockAsyncResult(status=states.SUCCESS),
    )
    response = client.get("/backup/status/test-task-id")
    assert response.status_code == 200
    assert response.json() == {
        "status": "SUCCESS",
        "result": "",
        "task_id": "test-task-id",
    }
    mock_get_backup_status.assert_called_once_with("test-task-id")
