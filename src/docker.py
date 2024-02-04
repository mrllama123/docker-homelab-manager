import logging
import os
from datetime import datetime, timezone
from functools import lru_cache

from python_on_whales import DockerClient, DockerException, Volume


BACKUP_DIR = os.getenv("BACKUP_DIR")

logging.basicConfig()
logger = logging.getLogger(__name__)


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


def is_volume_attached(volume_name: str) -> bool:
    client = get_docker_client()

    return len(client.volume.list(filters={"name": volume_name, "dangling": 0})) == 0


def backup_volume(volume_name: str) -> tuple[str, str]:
    client = get_docker_client()

    dt_now = datetime.now(tz=timezone.utc)
    backup_file = f"{volume_name}-{dt_now.isoformat()}.tar.gz"

    volume = get_volume(volume_name)

    if not volume:
        raise ValueError(f"Volume {volume_name} does not exist")

    logger.info("Backing up volume %s to %s", volume_name, backup_file)
    client.run(
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
    if not os.path.exists(os.path.join("/backup", backup_file)):
        raise RuntimeError("Backup failed")

    return volume_name, backup_file

    # with Session(engine) as session:
    #     backup = Backups(
    #         backup_name=backup_file,
    #         backup_created=dt_now.isoformat(),
    #         backup_path=os.path.join(BACKUP_DIR, backup_file),
    #         volume_name=volume_name,
    #     )
    #     session.add(backup)
    #     session.commit()


def restore_volume(volume_name: str, filename: str) -> tuple[str, str]:
    client = get_docker_client()
    client.run(
        image="busybox",
        command=[
            "tar",
            "xvf",
            f"/source/{filename}",
            "-C",
            "/dest",
        ],
        remove=True,
        volumes=[(volume_name, "/dest"), (BACKUP_DIR, "/source")],
    )
    if not os.path.exists(os.path.join("/backup", filename)):
        raise RuntimeError("Restore failed")

    return volume_name, filename
    # with Session(engine) as session:
    #     backup = session.exec(
    #         select(Backups).where(Backups.backup_name == filename)
    #     ).first()
    #     if not backup:
    #         raise ValueError(f"Backup {filename} does not exist")
    #     backup.restored = True
    #     backup.restored_date = datetime.now(tz=timezone.utc).isoformat()
    #     session.add(backup)
    #     session.commit()
