from datetime import datetime, timezone

from freezegun import freeze_time
import pytest
from sqlmodel import select

from src.db import Backups

from tests.fixtures import MockVolume


@freeze_time(lambda: datetime.now(timezone.utc), tick=False)
def test_backup_volume(mocker, session):
    mocker.patch(
        "src.docker.Session", **{"return_value.__enter__.return_value": session}
    )
    mock_docker_client = mocker.MagicMock()
    mock_get_docker_client = mocker.patch(
        "src.docker.get_docker_client", return_value=mock_docker_client
    )
    mock_volume = mocker.MagicMock()
    mock_get_volume = mocker.patch("src.docker.get_volume", return_value=mock_volume)
    mock_exists = mocker.patch("src.docker.os.path.exists", return_value=True)
    mocker.patch("src.docker.BACKUP_DIR", "/backup")
    from src.docker import backup_volume

    # Set up test data
    volume_name = "test-volume"
    dt_now = datetime.now(timezone.utc)
    backup_file = f"{volume_name}-{dt_now.isoformat()}.tar.gz"

    # Run the function
    backup_volume(volume_name)

    # Assert the function calls and behavior
    mock_get_docker_client.assert_called_once()
    mock_get_volume.assert_called_once_with(volume_name)

    mock_exists.assert_called_once_with(f"/backup/{backup_file}")
    mock_docker_client.run.assert_called_once_with(
        image="busybox",
        command=[
            "tar",
            "cvaf",
            f"/dest/{backup_file}",
            "-C",
            "/source",
            ".",
        ],
        remove=True,
        volumes=[(mock_volume, "/source"), ("/backup", "/dest")],
    )
    backup_db = session.exec(
        select(Backups).where(Backups.backup_name == backup_file)
    ).first()

    assert backup_db
    assert backup_db.backup_name == backup_file
    assert backup_db.backup_created == dt_now.isoformat()
    assert backup_db.backup_path == f"/backup/{backup_file}"
    assert backup_db.volume_name == volume_name


@freeze_time(lambda: datetime.now(timezone.utc), tick=False)
def test_backup_volume_failure_backup_not_found(mocker, session):
    mocker.patch(
        "src.docker.Session", **{"return_value.__enter__.return_value": session}
    )
    mock_docker_client = mocker.MagicMock()
    mock_get_docker_client = mocker.patch(
        "src.docker.get_docker_client", return_value=mock_docker_client
    )
    mock_volume = mocker.MagicMock()
    mock_get_volume = mocker.patch("src.docker.get_volume", return_value=mock_volume)
    mock_exists = mocker.patch("src.docker.os.path.exists", return_value=False)
    mocker.patch("src.docker.BACKUP_DIR", "/backup")
    from src.docker import backup_volume

    # Set up test data
    volume_name = "test-volume"
    dt_now = datetime.now(timezone.utc)
    backup_file = f"{volume_name}-{dt_now.isoformat()}.tar.gz"

    # Run the function
    with pytest.raises(RuntimeError, match="Backup failed"):
        backup_volume(volume_name)

    # # Assert the function calls and behavior
    mock_get_docker_client.assert_called_once()
    mock_get_volume.assert_called_once_with(volume_name)

    mock_exists.assert_called_once_with(f"/backup/{backup_file}")
    mock_docker_client.run.assert_called_once_with(
        image="busybox",
        command=[
            "tar",
            "cvaf",
            f"/dest/{backup_file}",
            "-C",
            "/source",
            ".",
        ],
        remove=True,
        volumes=[(mock_volume, "/source"), ("/backup", "/dest")],
    )
    backup_db = session.exec(
        select(Backups).where(Backups.backup_name == backup_file)
    ).first()

    assert not backup_db


def test_backup_volume_failure_volume_not_found(mocker, session):
    mocker.patch(
        "src.docker.Session", **{"return_value.__enter__.return_value": session}
    )
    mock_docker_client = mocker.MagicMock()
    mock_get_docker_client = mocker.patch(
        "src.docker.get_docker_client", return_value=mock_docker_client
    )
    mock_get_volume = mocker.patch("src.docker.get_volume", return_value=None)
    mock_exists = mocker.patch("src.docker.os.path.exists", return_value=True)
    mocker.patch("src.docker.BACKUP_DIR", "/backup")
    from src.docker import backup_volume

    # Set up test data
    volume_name = "test-volume"
    dt_now = datetime.now(timezone.utc)
    backup_file = f"{volume_name}-{dt_now.isoformat()}.tar.gz"

    # Run the function
    with pytest.raises(ValueError, match=f"Volume {volume_name} does not exist"):
        backup_volume(volume_name)

    # # Assert the function calls and behavior
    mock_get_docker_client.assert_called_once()
    mock_get_volume.assert_called_once_with(volume_name)

    mock_exists.assert_not_called()
    mock_docker_client.run.assert_not_called()
    backup_db = session.exec(
        select(Backups).where(Backups.backup_name == backup_file)
    ).first()

    assert not backup_db


@freeze_time(lambda: datetime.now(timezone.utc), tick=False)
def test_restore_volume(mocker, session):
    mocker.patch(
        "src.docker.Session", **{"return_value.__enter__.return_value": session}
    )
    mock_docker_client = mocker.MagicMock()
    mock_get_docker_client = mocker.patch(
        "src.docker.get_docker_client", return_value=mock_docker_client
    )
    mock_exists = mocker.patch("src.docker.os.path.exists", return_value=True)
    mocker.patch("src.docker.BACKUP_DIR", "/backup")

    session.add(
        Backups(
            backup_name="test-volume-2021-01-01T00:00:00.000000+00:00.tar.gz",
            backup_created="2021-01-01T00:00:00.000000+00:00",
            backup_path="/backup/test-volume-2021-01-01T00:00:00.000000+00:00.tar.gz",
            volume_name="test-volume",
        )
    )
    from src.docker import restore_volume

    # Set up test data
    volume_name = "test-volume"
    filename = "test-volume-2021-01-01T00:00:00.000000+00:00.tar.gz"

    # Run the function
    restore_volume(volume_name, filename)

    # # Assert the function calls and behavior
    mock_get_docker_client.assert_called_once()
    mock_exists.assert_called_once_with(f"/backup/{filename}")
    mock_docker_client.run.assert_called_once_with(
        image="busybox",
        command=[
            "tar",
            "xvf",
            f"/source/{filename}",
            "-C",
            "/dest",
        ],
        remove=True,
        volumes=[("test-volume", "/dest"), ("/backup", "/source")],
    )
    backup_db = session.exec(
        select(Backups).where(Backups.backup_name == filename)
    ).first()

    assert backup_db
    assert backup_db.restored
    assert backup_db.restored_date == datetime.now(timezone.utc).isoformat()


@freeze_time(lambda: datetime.now(timezone.utc), tick=False)
def test_restore_volume_not_found(mocker, session):
    mocker.patch(
        "src.docker.Session", **{"return_value.__enter__.return_value": session}
    )
    mock_docker_client = mocker.MagicMock()
    mock_get_docker_client = mocker.patch(
        "src.docker.get_docker_client", return_value=mock_docker_client
    )
    mock_exists = mocker.patch("src.docker.os.path.exists", return_value=False)
    mocker.patch("src.docker.BACKUP_DIR", "/backup")

    session.add(
        Backups(
            backup_name="test-volume-2021-01-01T00:00:00.000000+00:00.tar.gz",
            backup_created="2021-01-01T00:00:00.000000+00:00",
            backup_path="/backup/test-volume-2021-01-01T00:00:00.000000+00:00.tar.gz",
            volume_name="test-volume",
        )
    )
    from src.docker import restore_volume

    # Set up test data
    volume_name = "test-volume"
    filename = "test-volume-2021-01-01T00:00:00.000000+00:00.tar.gz"

    # Run the function
    with pytest.raises(RuntimeError, match="Restore failed"):
        restore_volume(volume_name, filename)

    # # Assert the function calls and behavior
    mock_get_docker_client.assert_called_once()
    mock_exists.assert_called_once_with(f"/backup/{filename}")
    mock_docker_client.run.assert_called_once_with(
        image="busybox",
        command=[
            "tar",
            "xvf",
            f"/source/{filename}",
            "-C",
            "/dest",
        ],
        remove=True,
        volumes=[("test-volume", "/dest"), ("/backup", "/source")],
    )
    backup_db = session.exec(
        select(Backups).where(Backups.backup_name == filename)
    ).first()

    assert backup_db
    assert not backup_db.restored
    assert not backup_db.restored_date




def test_get_volumes(mocker):
    vol_names = ["test-volume-1", "test-volume-2"]
    mock_client = mocker.MagicMock(
        **{
            "volume.list.return_value": [
                MockVolume(vol_name, mountpoint=f"/{vol_name}")
                for vol_name in vol_names
            ]
        }
    )
    mocker.patch("src.docker.get_docker_client", return_value=mock_client)
    from src.docker import get_volumes

    # Run the function
    volumes = get_volumes()
    assert len(volumes) == 2

    for vol_name in vol_names:
        assert any(vol_name == vol.name for vol in volumes)
        assert any(f"/{vol_name}" == vol.mountpoint for vol in volumes)

    assert all(vol.labels == {} for vol in volumes)
    assert all(not vol.options for vol in volumes)
    assert all(vol.status == {} for vol in volumes)
