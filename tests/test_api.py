import pytest
from fastapi.testclient import TestClient

from src.db import Backups
from src.models import ScheduleCrontab

from tests.fixtures import MockAsyncResult, MockVolume


@pytest.fixture()
def client(session) -> TestClient:
    from src.api import app, get_session

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_list_volumes(mocker, client):
    mock_get_volumes = mocker.patch(
        "src.api.get_volumes",
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


def test_get_backups(client, session):
    for backup_name in ["test-backup-name-1.tar.gz", "test-backup-name-2.tar.gz"]:
        session.add(
            Backups(
                backup_name=backup_name,
                backup_created="2021-01-01T00:00:00+00:00",
                backup_path="/backup/test-backup-name.tar.gz",
                volume_name="test-volume",
            )
        )
    session.commit()
    response = client.get("/backups")
    assert response.status_code == 200
    assert response.json() == [
        {
            "backup_name": "test-backup-name-1.tar.gz",
            "backup_created": "2021-01-01T00:00:00+00:00",
            "backup_path": "/backup/test-backup-name.tar.gz",
            "volume_name": "test-volume",
            "restored": False,
            "restored_date": None,
        },
        {
            "backup_name": "test-backup-name-2.tar.gz",
            "backup_created": "2021-01-01T00:00:00+00:00",
            "backup_path": "/backup/test-backup-name.tar.gz",
            "volume_name": "test-volume",
            "restored": False,
            "restored_date": None,
        },
    ]


def test_get_no_backups(client):
    response = client.get("/backups")
    assert response.status_code == 200
    assert response.json() == []


def test_get_backup(client, session):
    session.add(
        Backups(
            backup_name="test-backup-name.tar.gz",
            backup_created="2021-01-01T00:00:00+00:00",
            backup_path="/backup/test-backup-name.tar.gz",
            volume_name="test-volume",
        )
    )
    session.commit()
    response = client.get("/backups/test-backup-name.tar.gz")
    assert response.status_code == 200
    assert response.json() == {
        "backup_name": "test-backup-name.tar.gz",
        "backup_created": "2021-01-01T00:00:00+00:00",
        "backup_path": "/backup/test-backup-name.tar.gz",
        "volume_name": "test-volume",
        "restored": False,
        "restored_date": None,
    }


def test_get_backup_not_found(client):
    response = client.get("/backups/test-backup-name.tar.gz")
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Backup test-backup-name.tar.gz does not exist",
    }


def test_create_backup_volume_not_found(mocker, client):
    mock_get_volume = mocker.patch(
        "src.api.get_volume",
        return_value=None,
    )
    mock_create_volume_backup = mocker.patch(
        "src.api.add_backup_job",
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
    mocker.patch("src.api.uuid", **{"uuid4.return_value": "test-uuid"})
    mock_get_volume = mocker.patch(
        "src.api.get_volume",
        return_value=MockVolume(),
    )
    mock_is_volume_attached = mocker.patch(
        "src.api.is_volume_attached",
        return_value=True,
    )
    mock_create_volume_backup = mocker.patch(
        "src.api.add_backup_job",
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
    mock_create_volume_backup.assert_called_once_with(
        None,
        "backup-test-volume-test-uuid",
        "test-volume",
    )


def test_create_backup_volume_attached(mocker, client):
    mock_get_volume = mocker.patch(
        "src.api.get_volume",
        return_value=MockVolume(),
    )
    mock_is_volume_attached = mocker.patch(
        "src.api.is_volume_attached",
        return_value=False,
    )
    mock_create_volume_backup = mocker.patch(
        "src.api.add_backup_job",
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
    mocker.patch("src.api.uuid", **{"uuid4.return_value": "test-uuid"})
    mock_create_volume_backup = mocker.patch(
        "src.api.add_restore_job",
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
        None, "restore-test-volume-test-uuid", "test-volume", "test-backup-name.tar.gz"
    )


def test_create_schedule(mocker, client):
    mocker.patch("src.api.uuid", **{"uuid4.return_value": "test-uuid"})
    mock_get_volume = mocker.patch(
        "src.api.get_volume",
    )
    mock_create_volume_backup = mocker.patch(
        "src.api.add_backup_job",
        return_value=MockAsyncResult(),
    )
    response = client.post(
        "/volumes/backup/schedule",
        json={
            "schedule_name": "test-schedule",
            "volume_name": "test-volume",
            "crontab": {
                "minute": "1",
                "hour": "2",
                "day": "*",
                "month": "*",
                "day_of_week": "*",
            },
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "schedule_name": "test-task-id",
        "volume_name": "test-volume",
        "crontab": {
            "minute": "1",
            "hour": "2",
            "day": "*",
            "month": "*",
            "day_of_week": "*",
        },
    }
    mock_get_volume.assert_called_once_with("test-volume")
    mock_create_volume_backup.assert_called_once_with(
        None,
        "test-schedule",
        "test-volume",
        ScheduleCrontab(minute="1", hour="2", day="*", month="*", day_of_week="*"),
    )
