from src.models import RestoredBackups
from tests.fixtures import MockAsyncResult


def test_get_restored_volume(client, session):
    for restore_id in ["test-restore-id-1", "test-restore-id-2"]:
        session.add(
            RestoredBackups(
                restore_id=restore_id,
                restore_name="test-restore-name",
                created_at="2021-01-01T00:00:00+00:00",
                backup_filename=f"{restore_id}.tar.gz",
                volume_name="test-volume",
            )
        )
    session.commit()

    response = client.get("/api/volumes/restores")

    assert response.status_code == 200
    assert response.json() == [
        {
            "restore_id": "test-restore-id-1",
            "restore_name": "test-restore-name",
            "volume_name": "test-volume",
            "successful": True,
            'error_message': None,
            "backup_filename": "test-restore-id-1.tar.gz",
            "created_at": "2021-01-01T00:00:00+00:00",
        },
        {
            "restore_id": "test-restore-id-2",
            "restore_name": "test-restore-name",
            "volume_name": "test-volume",
            "successful": True,
            'error_message': None,
            "backup_filename": "test-restore-id-2.tar.gz",
            "created_at": "2021-01-01T00:00:00+00:00",
        },
    ]

def test_restore_backup(mocker, client):
    mocker.patch("src.routes.api.uuid", **{"uuid4.return_value": "test-uuid"})
    mock_create_volume_backup = mocker.patch(
        "src.routes.api.add_restore_job",
        return_value=MockAsyncResult(),
    )
    response = client.post(
        "/api/volumes/restore",
        json={
            "volume_name": "test-volume",
            "backup_filename": "test-backup-name.tar.gz",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "volume_name": "test-volume",
        "restore_id": "test-task-id",
    }
    mock_create_volume_backup.assert_called_once_with(
        "restore-test-volume-test-uuid", "test-volume", "test-backup-name.tar.gz"
    )

