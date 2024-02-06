from freezegun import freeze_time
from datetime import datetime, timezone

from sqlmodel import select

from src.models import (
    Backups,
    ScheduledBackups,
    BackupVolumes,
    BackupFilenames,
    RestoreBackupVolumes,
    RestoredBackups,
    ErrorBackups,
    ErrorRestoredBackups,
)


@freeze_time(lambda: datetime.now(timezone.utc), tick=False)
def test_task_backup_volume(mocker, session):
    mocker.patch(
        "src.apschedule.tasks.Session",
        **{"return_value.__enter__.return_value": session},
    )
    mock_backup_volume = mocker.patch("src.apschedule.tasks.backup_volume")
    mocker.patch("src.apschedule.tasks.BACKUP_DIR", "/backup")
    from src.apschedule.tasks import task_create_backup

    task_create_backup("test-volume", "job_id_1")

    mock_backup_volume.assert_called_once_with("test-volume", "/backup")
    backup_db = session.exec(
        select(Backups).where(Backups.backup_id == "job_id_1")
    ).first()

    dt_now = datetime.now(timezone.utc)

    assert backup_db
    assert backup_db.backup_id == "job_id_1"
    assert backup_db.backup_filename == f"test-volume-{dt_now.isoformat()}.tar.gz"
    assert backup_db.backup_created == dt_now.isoformat()
    assert backup_db.backup_path == f"/backup/test-volume-{dt_now.isoformat()}.tar.gz"
    assert backup_db.volume_name == "test-volume"
    assert backup_db.success == True
    assert backup_db.errorMessage == None
    assert backup_db.schedule_id == None

    db_backup_volumes = session.exec(
        select(BackupVolumes).where(BackupVolumes.backup_id == "job_id_1")
    ).first()

    assert db_backup_volumes
    assert db_backup_volumes.volume_name == "test-volume"
    assert db_backup_volumes.backup_id == "job_id_1"

    db_backup_filenames = session.exec(
        select(BackupFilenames).where(BackupFilenames.backup_id == "job_id_1")
    ).first()

    assert db_backup_filenames
    assert (
        db_backup_filenames.backup_filename
        == f"test-volume-{dt_now.isoformat()}.tar.gz"
    )
    assert db_backup_filenames.backup_id == "job_id_1"

    db_scheduled_backups = session.exec(
        select(ScheduledBackups).where(ScheduledBackups.backup_id == "job_id_1")
    ).first()

    assert not db_scheduled_backups


@freeze_time(lambda: datetime.now(timezone.utc), tick=False)
def test_task_backup_volume_error(mocker, session):
    mocker.patch(
        "src.apschedule.tasks.Session",
        **{"return_value.__enter__.return_value": session},
    )
    mock_backup_volume = mocker.patch(
        "src.apschedule.tasks.backup_volume", side_effect=Exception("test error")
    )
    mocker.patch("src.apschedule.tasks.BACKUP_DIR", "/backup")
    from src.apschedule.tasks import task_create_backup

    task_create_backup("test-volume", "job_id_1")

    mock_backup_volume.assert_called_once_with("test-volume", "/backup")
    backup_db = session.exec(
        select(ErrorBackups).where(ErrorBackups.backup_id == "job_id_1")
    ).first()

    assert backup_db
    assert backup_db.backup_id == "job_id_1"
    assert backup_db.error_message == "test error"


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

    task_create_backup("test-volume", "job_id_1", "job_name_1", True)

    mock_backup_volume.assert_called_once_with("test-volume", "/backup")
    backup_db = session.exec(
        select(ErrorBackups).where(ErrorBackups.backup_id == "test-uuid")
    ).first()

    assert backup_db
    assert backup_db.backup_id == "test-uuid"
    assert backup_db.error_message == "test error"


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

    mock_backup_volume.assert_called_once_with("test-volume", "/backup")
    backup_db = session.exec(
        select(Backups).where(Backups.backup_id == "test-uuid")
    ).first()

    dt_now = datetime.now(timezone.utc)

    assert backup_db
    assert backup_db.backup_id == "test-uuid"
    assert backup_db.backup_filename == f"test-volume-{dt_now.isoformat()}.tar.gz"
    assert backup_db.backup_created == dt_now.isoformat()
    assert backup_db.backup_path == f"/backup/test-volume-{dt_now.isoformat()}.tar.gz"
    assert backup_db.volume_name == "test-volume"
    assert backup_db.success == True
    assert backup_db.errorMessage == None
    assert backup_db.schedule_id == "job_id_1"

    db_backup_volumes = session.exec(
        select(BackupVolumes).where(BackupVolumes.backup_id == "test-uuid")
    ).first()

    assert db_backup_volumes
    assert db_backup_volumes.volume_name == "test-volume"
    assert db_backup_volumes.backup_id == "test-uuid"

    db_backup_filenames = session.exec(
        select(BackupFilenames).where(BackupFilenames.backup_id == "test-uuid")
    ).first()

    assert db_backup_filenames
    assert (
        db_backup_filenames.backup_filename
        == f"test-volume-{dt_now.isoformat()}.tar.gz"
    )
    assert db_backup_filenames.backup_id == "test-uuid"

    db_scheduled_backups = session.exec(
        select(ScheduledBackups).where(ScheduledBackups.backup_id == "test-uuid")
    ).first()

    assert db_scheduled_backups
    assert db_scheduled_backups.schedule_id == "job_id_1"
    assert db_scheduled_backups.backup_id == "test-uuid"
    assert db_scheduled_backups.schedule_name == "job_name_1"


@freeze_time(lambda: datetime.now(timezone.utc), tick=False)
def test_task_restore_backup(mocker, session):
    mocker.patch(
        "src.apschedule.tasks.Session",
        **{"return_value.__enter__.return_value": session},
    )
    mock_restore_volume = mocker.patch("src.apschedule.tasks.restore_volume")
    mocker.patch("src.apschedule.tasks.BACKUP_DIR", "/backup")
    backup = Backups(
        backup_id="job_id_1",
        backup_filename="test-volume-2021-01-01T00:00:00.000000+00:00.tar.gz",
        backup_created="2021-01-01T00:00:00.000000+00:00",
        backup_path="/backup/test-volume-2021-01-01T00:00:00.000000+00:00.tar.gz",
        volume_name="test-volume",
        success=True,
    )
    session.add(backup)

    from src.apschedule.tasks import task_restore_backup

    task_restore_backup(backup.volume_name, backup.backup_filename, "job_id_2")

    mock_restore_volume.assert_called_once_with(
        backup.volume_name, "/backup", backup.backup_filename
    )
    restore_db = session.exec(
        select(RestoredBackups).where(RestoredBackups.restore_id == "job_id_2")
    ).first()

    dt_now = datetime.now(timezone.utc)

    assert restore_db
    assert restore_db.restore_id == "job_id_2"
    assert restore_db.backup_filename == backup.backup_filename
    assert restore_db.restored_date == dt_now.isoformat()
    assert restore_db.volume_name == "test-volume"
    assert restore_db.success == True
    assert restore_db.errorMessage == None

    db_restore_volumes = session.exec(
        select(RestoreBackupVolumes).where(
            RestoreBackupVolumes.restore_id == "job_id_2"
        )
    ).first()

    assert db_restore_volumes
    assert db_restore_volumes.volume_name == "test-volume"
    assert db_restore_volumes.restore_id == "job_id_2"


@freeze_time(lambda: datetime.now(timezone.utc), tick=False)
def test_task_restore_backup_error(mocker, session):
    mocker.patch(
        "src.apschedule.tasks.Session",
        **{"return_value.__enter__.return_value": session},
    )
    mock_restore_volume = mocker.patch(
        "src.apschedule.tasks.restore_volume", side_effect=Exception("test error")
    )
    mocker.patch("src.apschedule.tasks.BACKUP_DIR", "/backup")
    backup = Backups(
        backup_id="job_id_1",
        backup_filename="test-volume-2021-01-01T00:00:00.000000+00:00.tar.gz",
        backup_created="2021-01-01T00:00:00.000000+00:00",
        backup_path="/backup/test-volume-2021-01-01T00:00:00.000000+00:00.tar.gz",
        volume_name="test-volume",
        success=True,
    )
    session.add(backup)

    from src.apschedule.tasks import task_restore_backup

    task_restore_backup(backup.volume_name, backup.backup_filename, "job_id_2")

    mock_restore_volume.assert_called_once_with(
        backup.volume_name, "/backup", backup.backup_filename
    )

    restore_db = session.exec(
        select(ErrorRestoredBackups).where(ErrorRestoredBackups.restore_id == "job_id_2")
    ).first()

    assert restore_db
    assert restore_db.restore_id == "job_id_2"
    assert restore_db.error_message == "test error"
