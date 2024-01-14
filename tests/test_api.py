from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from celery import states


class MockVolume:
    def __init__(
        self, name="test-volume", labels=None, mountpoint="/test-volume", options=None
    ) -> None:
        self.name = name
        self.labels = labels or {}
        self.mountpoint = mountpoint
        self.options = options
        self.status = {}
        self.created_at = datetime.fromisoformat("2021-01-01T00:00:00.000000+00:00")


class MockAsyncResult:
    def __init__(self, status=states.PENDING, result="", id="test-task-id") -> None:
        self.status = status
        self.result = result
        self.id = id


@pytest.fixture()
def client() -> TestClient:
    from src.api.main import app

    return TestClient(app)


def test_list_volumes(mocker, client):
    mock_get_volumes = mocker.patch(
        "src.api.main.get_volumes",
        return_value=[MockVolume()],
    )
    response = client.get("/volumes")
    assert response.status_code == 200
    assert response.json() == [
        {
            "name": "test-volume",
            "labels": {},
            "mountpoint": "/test-volume",
            "options": {},
            "status": {},
            "createdAt": "2021-01-01T00:00:00+00:00",
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
        return_value=MockVolume(),
    )
    mock_is_volume_attached = mocker.patch(
        "src.api.main.is_volume_attached",
        return_value=False,
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
    mock_is_volume_attached.assert_called_once_with("test-volume")
    mock_create_volume_backup.assert_called_once_with("test-volume")


def test_create_backup_volume_attached(mocker, client):
    mock_get_volume = mocker.patch(
        "src.api.main.get_volume",
        return_value=MockVolume(),
    )
    mock_is_volume_attached = mocker.patch(
        "src.api.main.is_volume_attached",
        return_value=True,
    )
    mock_create_volume_backup = mocker.patch(
        "src.api.main.create_volume_backup.delay",
        return_value=MockAsyncResult(),
    )
    response = client.post("/backup/test-volume")
    assert response.status_code == 409
    assert response.json() == {
        "detail": "Volume test-volume is attached to a container"
    }
    mock_get_volume.assert_called_once_with("test-volume")
    mock_is_volume_attached.assert_called_once_with("test-volume")
    mock_create_volume_backup.assert_not_called()


def test_restore_backup(mocker, client):
    mock_create_volume_backup = mocker.patch(
        "src.api.main.restore_volume_task.delay",
        return_value=MockAsyncResult(),
    )
    response = client.post(
        "/restore",
        json={
            "volume_name": "test-volume",
            "backup_filename": "test-backup-name.tar.gz",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "message": "restore of test-volume started",
        "task_id": "test-task-id",
    }
    mock_create_volume_backup.assert_called_once_with(
        "test-volume", "test-backup-name.tar.gz"
    )


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
