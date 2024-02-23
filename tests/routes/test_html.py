from src.models import Backups

from tests.fixtures import MockAsyncResult, MockVolume


def test_root(client, snapshot):
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"

    snapshot.assert_match(response.text.strip(), "index.html")


def test_volumes(client, snapshot, mocker):
    mocker.patch(
        "src.routes.impl.volumes.get_volumes",
        return_value=[MockVolume()],
    )
    response = client.get("/volumes")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    snapshot.assert_match(response.text.strip(), "volume_rows.html")


def test_backup_volume_tab(client, snapshot):
    response = client.get("/tabs/backup-volume")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    snapshot.assert_match(response.text.strip(), "backup_volume_tab.html")


def test_backup_volume(client, snapshot, mocker):
    mocker.patch("src.routes.impl.volumes.uuid", **{"uuid4.return_value": "test-uuid"})
    mock_get_volume = mocker.patch(
        "src.routes.impl.volumes.get_volume",
        return_value=MockVolume(),
    )
    mock_is_volume_attached = mocker.patch(
        "src.routes.impl.volumes.is_volume_attached",
        return_value=True,
    )
    mock_create_volume_backup = mocker.patch(
        "src.routes.impl.volumes.add_backup_job",
        return_value=MockAsyncResult(),
    )
    response = client.post("/volumes/backup/test_volume")

    mock_get_volume.assert_called_once_with("test_volume")
    mock_is_volume_attached.assert_called_once_with("test_volume")
    mock_create_volume_backup.assert_called_once_with(
        "backup-test_volume-test-uuid", "test_volume"
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    snapshot.assert_match(response.text.strip(), "notification.html")


def test_backup_volume_error_attached(client, snapshot, mocker):
    mocker.patch("src.routes.impl.volumes.uuid", **{"uuid4.return_value": "test-uuid"})
    mock_get_volume = mocker.patch(
        "src.routes.impl.volumes.get_volume",
        return_value=MockVolume(),
    )
    mock_is_volume_attached = mocker.patch(
        "src.routes.impl.volumes.is_volume_attached",
        return_value=False,
    )
    response = client.post("/volumes/backup/test_volume")

    mock_get_volume.assert_called_once_with("test_volume")
    mock_is_volume_attached.assert_called_once_with("test_volume")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    snapshot.assert_match(response.text.strip(), "notification.html")


def test_backups(client, snapshot, session):
    for backup_id in ["test-backup-id-1", "test-backup-id-2"]:
        session.add(
            Backups(
                backup_id=backup_id,
                created_at="2021-01-01T00:00:00+00:00",
                backup_filename=f"{backup_id}.tar.gz",
                backup_name="test-backup-name",
                successful=True,
                backup_path="/volumes/backup/test-backup-name.tar.gz",
                volume_name="test-volume",
            )
        )
    session.commit()
    response = client.get("/volumes/backups")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    snapshot.assert_match(response.text.strip(), "backup_rows.html")
