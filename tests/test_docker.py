import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool
from datetime import datetime, timezone
from freezegun import freeze_time
from src.db import Backups


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@freeze_time(lambda: datetime.now(timezone.utc), tick=False)
def test_backup_volume(monkeypatch, mocker, session):
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
