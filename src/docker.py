import os
from datetime import datetime
from functools import lru_cache

from python_on_whales import DockerClient, DockerException, Volume
from sqlmodel import Session

from src.db import Backups, engine

BACKUP_DIR = os.getenv("BACKUP_DIR")


@lru_cache
def get_docker_client() -> DockerClient:
    if is_docker_rootless():
        return DockerClient(
            host=f'unix://{os.getenv("XDG_RUNTIME_DIR")}/docker.sock',
        )
    return DockerClient()


def is_docker_rootless() -> bool:
    return not os.path.exists("/var/run/docker.sock")


def get_volumes() -> list[Volume]:
    client = get_docker_client()
    volumes = client.volume.list()
    return volumes


def get_volume(volume_name: str) -> Volume | None:
    client = get_docker_client()
    try:
        volume = client.volume.inspect(volume_name)
        return volume
    except DockerException:
        return None
    except Exception as e:
        raise e


def backup_volume(volume_name: str) -> None:
    client = get_docker_client()

    dt_now = datetime.now(tz=datetime.utcnow().astimezone().tzinfo)
    backup_file = f"{volume_name}-{dt_now.isoformat()}.tar.gz"

    volume = get_volume(volume_name)

    if not volume:
        raise ValueError(f"Volume {volume_name} does not exist")

    output = client.run(
        image="busybox",
        command=[
            "tar",
            "cvaf",
            f"/dest/{backup_file}",
            "-C",
            "/source",
            ".",
        ],  # f"tar cvaf /dest/{backup_file} -C /source .",
        remove=True,
        volumes=[(volume, "/source"), (BACKUP_DIR, "/dest")],
    )
    print(output)
    if not os.path.exists(os.path.join("/backup", backup_file)):
        raise RuntimeError("Backup failed")

    with Session(engine) as session:
        backup = Backups(
            backup_name=backup_file,
            backup_created=dt_now.isoformat(),
            backup_path=os.path.join(BACKUP_DIR, volume_name, backup_file),
            volume_name=volume_name,
        )
        session.add(backup)
        session.commit()
