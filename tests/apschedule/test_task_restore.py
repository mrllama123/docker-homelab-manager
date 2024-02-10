from datetime import datetime, timezone

import pytest
from freezegun import freeze_time
from sqlmodel import select

from src.models import (
    Backups,
    ErrorRestoredBackups,
    RestoredBackups,
)


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
        backup_name="restore-test-volume-uuid-1",
        backup_created="2021-01-01T00:00:00.000000+00:00",
        backup_path="/backup/test-volume-2021-01-01T00:00:00.000000+00:00.tar.gz",
        volume_name="test-volume",
    )
    session.add(backup)

    from src.apschedule.tasks import task_restore_backup

    task_restore_backup(
        backup.volume_name,
        backup.backup_filename,
        "job_id_2",
        "restore-test-volume-uuid-2",
    )

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
    assert restore_db.restore_name == "restore-test-volume-uuid-2"


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
        backup_name="restore-test-volume-uuid-1",
        backup_created="2021-01-01T00:00:00.000000+00:00",
        backup_path="/backup/test-volume-2021-01-01T00:00:00.000000+00:00.tar.gz",
        volume_name="test-volume",
    )
    session.add(backup)

    from src.apschedule.tasks import task_restore_backup

    with pytest.raises(Exception, match="test error"):
        task_restore_backup(
            backup.volume_name,
            backup.backup_filename,
            "job_id_2",
            "restore-test-volume-uuid-2",
        )

    mock_restore_volume.assert_called_once_with(
        backup.volume_name, "/backup", backup.backup_filename
    )

    restore_db = session.exec(
        select(ErrorRestoredBackups).where(
            ErrorRestoredBackups.restore_id == "job_id_2"
        )
    ).first()

    assert restore_db
    assert restore_db.restore_id == "job_id_2"
    assert restore_db.error_message == "test error"
    assert restore_db.restore_name == "restore-test-volume-uuid-2"
