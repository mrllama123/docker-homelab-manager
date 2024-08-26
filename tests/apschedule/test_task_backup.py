from datetime import datetime, timezone

import pytest
from freezegun import freeze_time
from sqlmodel import select

from src.models import BackupFilenames, Backups


@freeze_time(lambda: datetime.now(timezone.utc), tick=False)
def test_task_backup_volume(mocker, session):
    mocker.patch(
        "src.apschedule.tasks.Session",
        **{"return_value.__enter__.return_value": session},
    )
    mock_backup_volume = mocker.patch("src.apschedule.tasks.backup_volume")
    mocker.patch("src.apschedule.tasks.BACKUP_DIR", "/backup")
    from src.apschedule.tasks import task_create_backup

    task_create_backup("test-volume", "job_id_1", "job_name_1")

    mock_backup_volume.assert_called_once_with(
        "test-volume",
        "/backup",
        f"test-volume-{datetime.now(timezone.utc).isoformat()}.tar.gz",
    )
    backup_db = session.exec(
        select(Backups).where(Backups.backup_id == "job_id_1"),
    ).first()

    dt_now = datetime.now(timezone.utc)

    assert backup_db
    assert backup_db.backup_id == "job_id_1"
    assert backup_db.backup_filename == f"test-volume-{dt_now.isoformat()}.tar.gz"
    assert backup_db.backup_name == "job_name_1"
    assert backup_db.created_at == dt_now.isoformat()
    assert backup_db.backup_path == f"/backup/test-volume-{dt_now.isoformat()}.tar.gz"
    assert backup_db.volume_name == "test-volume"
    assert backup_db.schedule_id is None

    db_backup_filenames = session.exec(
        select(BackupFilenames).where(BackupFilenames.backup_id == "job_id_1"),
    ).first()

    assert db_backup_filenames
    assert (
        db_backup_filenames.backup_filename
        == f"test-volume-{dt_now.isoformat()}.tar.gz"
    )
    assert db_backup_filenames.backup_id == "job_id_1"


@freeze_time(lambda: datetime.now(timezone.utc), tick=False)
def test_task_backup_volume_error(mocker, session):
    mocker.patch(
        "src.apschedule.tasks.Session",
        **{"return_value.__enter__.return_value": session},
    )
    mock_backup_volume = mocker.patch(
        "src.apschedule.tasks.backup_volume",
        side_effect=Exception("test error"),
    )
    mocker.patch("src.apschedule.tasks.BACKUP_DIR", "/backup")
    from src.apschedule.tasks import task_create_backup

    with pytest.raises(Exception, match="test error"):
        task_create_backup("test-volume", "job_id_1", "job_name_1")

    mock_backup_volume.assert_called_once_with(
        "test-volume",
        "/backup",
        f"test-volume-{datetime.now(timezone.utc).isoformat()}.tar.gz",
    )
    backup_db = session.exec(
        select(Backups).where(Backups.backup_id == "job_id_1")
    ).first()

    assert backup_db
    assert backup_db.backup_id == "job_id_1"
    assert backup_db.error_message == "test error"
    assert backup_db.backup_name == "job_name_1"


@freeze_time(lambda: datetime.now(timezone.utc), tick=False)
def test_task_backup_volume_error_schedule(mocker, session):
    mocker.patch(
        "src.apschedule.tasks.Session",
        **{"return_value.__enter__.return_value": session},
    )
    mock_backup_volume = mocker.patch(
        "src.apschedule.tasks.backup_volume", side_effect=Exception("test error")
    )
    mocker.patch("src.apschedule.tasks.BACKUP_DIR", "/backup")
    mocker.patch("src.apschedule.tasks.uuid", **{"uuid4.return_value": "test-uuid"})
    from src.apschedule.tasks import task_create_backup

    with pytest.raises(Exception, match="test error"):
        task_create_backup(
            "test-volume",
            "job_id_1",
            "job_name_1",
            is_schedule=True,
        )

    mock_backup_volume.assert_called_once_with(
        "test-volume",
        "/backup",
        f"test-volume-{datetime.now(timezone.utc).isoformat()}.tar.gz",
    )
    backup_db = session.exec(
        select(Backups).where(Backups.backup_id == "test-uuid")
    ).first()

    assert backup_db
    assert backup_db.backup_id == "test-uuid"
    assert backup_db.error_message == "test error"
    assert backup_db.backup_name == "job_name_1"


@freeze_time(lambda: datetime.now(timezone.utc), tick=False)
def test_task_backup_volume_schedule(mocker, session):
    mocker.patch(
        "src.apschedule.tasks.Session",
        **{"return_value.__enter__.return_value": session},
    )
    mock_backup_volume = mocker.patch("src.apschedule.tasks.backup_volume")
    mocker.patch("src.apschedule.tasks.BACKUP_DIR", "/backup")
    mocker.patch("src.apschedule.tasks.uuid", **{"uuid4.return_value": "test-uuid"})
    from src.apschedule.tasks import task_create_backup

    task_create_backup("test-volume", "job_id_1", "job_name_1", True)

    mock_backup_volume.assert_called_once_with(
        "test-volume",
        "/backup",
        f"test-volume-{datetime.now(timezone.utc).isoformat()}.tar.gz",
    )
    backup_db = session.exec(
        select(Backups).where(Backups.backup_id == "test-uuid")
    ).first()

    dt_now = datetime.now(timezone.utc)

    assert backup_db
    assert backup_db.backup_id == "test-uuid"
    assert backup_db.backup_filename == f"test-volume-{dt_now.isoformat()}.tar.gz"
    assert backup_db.created_at == dt_now.isoformat()
    assert backup_db.backup_path == f"/backup/test-volume-{dt_now.isoformat()}.tar.gz"
    assert backup_db.volume_name == "test-volume"
    assert backup_db.schedule_id == "job_id_1"
    assert backup_db.backup_name == "job_name_1"

    db_backup_filenames = session.exec(
        select(BackupFilenames).where(BackupFilenames.backup_id == "test-uuid")
    ).first()

    assert db_backup_filenames
    assert (
        db_backup_filenames.backup_filename
        == f"test-volume-{dt_now.isoformat()}.tar.gz"
    )
    assert db_backup_filenames.backup_id == "test-uuid"
