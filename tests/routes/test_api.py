from apscheduler.jobstores.base import JobLookupError

from src.db import Backups
from src.models import BackupSchedule, ScheduleCrontab
from tests.fixtures import MockAsyncResult, MockVolume


def test_list_volumes(mocker, client):
    mock_get_volumes = mocker.patch(
        "src.routes.impl.volumes.volumes.get_volumes",
        return_value=[MockVolume()],
    )
    response = client.get("/api/volumes")
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
    backups = [
        Backups(
            backup_id=backup_id,
            created_at="2021-01-01T00:00:00+00:00",
            backup_filename=f"{backup_id}.tar.gz",
            backup_name="test-backup-name",
            successful=True,
            backup_path="/volumes/backup/test-backup-name.tar.gz",
            volume_name="test-volume",
        )
        for backup_id in ["test-backup-id-1", "test-backup-id-2"]
    ]
    session.add_all(backups)
    session.commit()
    response = client.get("/api/volumes/backup")
    assert response.status_code == 200
    assert response.json() == [backup.model_dump(mode="json") for backup in backups]


def test_get_no_backups(client):
    response = client.get("/api/volumes/backup")
    assert response.status_code == 200
    assert response.json() == []


def test_get_backup(client, session):
    backup = Backups(
        backup_id="test-backup-id",
        backup_filename="test-backup-name.tar.gz",
        backup_name="test-backup-name",
        created_at="2021-01-01T00:00:00+00:00",
        successful=True,
        backup_path="/volumes/backup/test-backup-name.tar.gz",
        volume_name="test-volume",
    )
    session.add(backup)
    session.commit()
    response = client.get("/api/volumes/backup/test-backup-id")
    assert response.status_code == 200
    assert response.json() == backup.model_dump(mode="json")


def test_get_backup_not_found(client):
    response = client.get("/api/volumes/backup/test-backup-name.tar.gz")
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Backup test-backup-name.tar.gz does not exist",
    }


def test_create_backup_volume_not_found(mocker, client):
    mock_get_volume = mocker.patch(
        "src.routes.api.get_volume",
        return_value=None,
    )
    mock_create_volume_backup = mocker.patch(
        "src.routes.api.add_backup_job",
        return_value=MockAsyncResult(),
    )
    response = client.post("/api/volumes/backup/test-volume")
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Volume test-volume does not exist",
    }
    mock_get_volume.assert_called_once_with("test-volume")
    mock_create_volume_backup.assert_not_called()


def test_create_backup(mocker, client):
    mocker.patch("src.routes.api.uuid", **{"uuid4.return_value": "test-uuid"})
    mock_get_volume = mocker.patch(
        "src.routes.api.get_volume",
        return_value=MockVolume(),
    )
    mock_is_volume_attached = mocker.patch(
        "src.routes.api.is_volume_attached",
        return_value=True,
    )
    mock_create_volume_backup = mocker.patch(
        "src.routes.api.add_backup_job",
        return_value=MockAsyncResult(),
    )

    response = client.post("/api/volumes/backup/test-volume")
    assert response.status_code == 200
    assert response.json() == {
        "volume_name": "test-volume",
        "backup_id": "test-task-id",
    }
    mock_get_volume.assert_called_once_with("test-volume")
    mock_is_volume_attached.assert_called_once_with("test-volume")
    mock_create_volume_backup.assert_called_once_with(
        "backup-test-volume-test-uuid",
        "test-volume",
    )


def test_create_backup_volume_attached(mocker, client):
    mock_get_volume = mocker.patch(
        "src.routes.api.get_volume",
        return_value=MockVolume(),
    )
    mock_is_volume_attached = mocker.patch(
        "src.routes.api.is_volume_attached",
        return_value=False,
    )
    mock_create_volume_backup = mocker.patch(
        "src.routes.api.add_backup_job",
        return_value=MockAsyncResult(),
    )
    response = client.post("/api/volumes/backup/test-volume")
    assert response.status_code == 409
    assert response.json() == {
        "detail": "Volume test-volume is attached to a container"
    }
    mock_get_volume.assert_called_once_with("test-volume")
    mock_is_volume_attached.assert_called_once_with("test-volume")
    mock_create_volume_backup.assert_not_called()


def test_create_schedule(mocker, client):
    mocker.patch("src.routes.api.uuid", **{"uuid4.return_value": "test-uuid"})
    mock_get_volume = mocker.patch(
        "src.routes.api.get_volume",
    )
    mock_create_volume_backup = mocker.patch(
        "src.routes.api.add_backup_job",
        return_value=MockAsyncResult(),
    )
    response = client.post(
        "/api/volumes/schedule/backup",
        json={
            "schedule_name": "test-schedule",
            "volume_name": "test-volume",
            "crontab": {
                "minute": "1",
                "hour": "2",
                "day": "*",
                "month": "*",
                "seconds": "*",
                "day_of_week": "*",
            },
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "schedule_id": "test-task-id",
        "schedule_name": "test-schedule",
        "volume_name": "test-volume",
        "crontab": {
            "minute": "1",
            "hour": "2",
            "day": "*",
            "month": "*",
            "seconds": "*",
            "day_of_week": "*",
        },
    }
    mock_get_volume.assert_called_once_with("test-volume")
    mock_create_volume_backup.assert_called_once_with(
        "test-schedule",
        "test-volume",
        ScheduleCrontab(minute="1", hour="2", day="*", month="*", day_of_week="*"),
        is_schedule=True,
    )


def test_get_schedule(mocker, client):
    mock_get_schedule = mocker.patch(
        "src.routes.api.get_backup_schedule",
        return_value=BackupSchedule(
            volume_name="test-volume",
            schedule_id="test-schedule-id",
            schedule_name="test-schedule",
            crontab=ScheduleCrontab(
                minute="1", hour="2", day="*", month="*", day_of_week="*"
            ),
        ),
    )
    response = client.get("/api/volumes/schedule/backup/test-schedule")
    assert response.status_code == 200
    assert response.json() == {
        "schedule_id": "test-schedule-id",
        "schedule_name": "test-schedule",
        "volume_name": "test-volume",
        "crontab": {
            "minute": "1",
            "hour": "2",
            "day": "*",
            "month": "*",
            "seconds": "*",
            "day_of_week": "*",
        },
    }
    mock_get_schedule.assert_called_once_with("test-schedule")


def test_get_schedule_not_found(mocker, client):
    mock_get_schedule = mocker.patch(
        "src.routes.api.get_backup_schedule",
        return_value=None,
    )
    response = client.get("/api/volumes/schedule/backup/test-schedule")
    assert response.status_code == 404
    assert response.json() == {"detail": "Schedule job test-schedule does not exist"}
    mock_get_schedule.assert_called_once_with("test-schedule")


def test_list_schedule(mocker, client):
    mock_list_schedule = mocker.patch(
        "src.routes.api.list_backup_schedules",
        return_value=[
            BackupSchedule(
                volume_name="test-volume",
                schedule_id="test-schedule-id",
                schedule_name="test-schedule",
                crontab=ScheduleCrontab(
                    minute="1", hour="2", day="*", month="*", day_of_week="*"
                ),
            )
        ],
    )
    response = client.get("/api/volumes/schedule/backup")
    assert response.status_code == 200
    assert response.json() == [
        {
            "schedule_id": "test-schedule-id",
            "schedule_name": "test-schedule",
            "volume_name": "test-volume",
            "crontab": {
                "minute": "1",
                "hour": "2",
                "day": "*",
                "month": "*",
                "seconds": "*",
                "day_of_week": "*",
            },
        }
    ]
    mock_list_schedule.assert_called_once_with()


def test_remove_schedule(mocker, client):
    mock_remove_schedule = mocker.patch(
        "src.routes.api.delete_backup_schedule",
    )
    response = client.delete("/api/volumes/schedule/backup/test-schedule")
    assert response.status_code == 200
    assert response.json() == "Schedule test-schedule removed"
    mock_remove_schedule.assert_called_once_with("test-schedule")


def test_remove_schedule_not_found(mocker, client):
    mock_remove_schedule = mocker.patch(
        "src.routes.api.delete_backup_schedule",
        side_effect=JobLookupError("test-schedule"),
    )
    response = client.delete("/api/volumes/schedule/backup/test-schedule")
    assert response.status_code == 404
    assert response.json() == {"detail": "Schedule job test-schedule does not exist"}
    mock_remove_schedule.assert_called_once_with("test-schedule")
