import logging
from functools import lru_cache
from pathlib import Path

from python_on_whales import DockerClient, DockerException, Volume

logging.basicConfig()
logger = logging.getLogger(__name__)


@lru_cache
def get_docker_client() -> DockerClient:
    return DockerClient()


def get_volumes() -> list[Volume]:
    client = get_docker_client()
    return client.volume.list()


def get_volume(volume_name: str) -> Volume | None:
    client = get_docker_client()
    try:
        return client.volume.inspect(volume_name)
    except DockerException:
        return None
    except Exception as e:
        raise e


def is_volume_attached(volume_name: str) -> bool:
    client = get_docker_client()

    return len(client.volume.list(filters={"name": volume_name, "dangling": 0})) == 0


def backup_volume(volume_name: str, backup_dir: str, filename: str) -> None:
    client = get_docker_client()

    volume = get_volume(volume_name)

    if not volume:
        raise ValueError("Volume %s does not exist", volume_name)

    logger.info(
        "Backing up volume %s to %s",
        volume_name,
        Path(backup_dir) / filename,
    )
    client.run(
        image="busybox",
        command=[
            "tar",
            "cvaf",
            f"/dest/{filename}",
            "-C",
            "/source",
            ".",
        ],  # f"tar cvaf /dest/{backup_file} -C /source .",
        remove=True,
        volumes=[(volume, "/source"), (backup_dir, "/dest")],
    )
    if not Path.exists(Path(backup_dir) / filename):
        raise RuntimeError("Backup failed")


def restore_volume(volume_name: str, backup_dir: str, filename: str) -> None:
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
        volumes=[(volume_name, "/dest"), (backup_dir, "/source")],
    )
    if not Path.exists(Path("/backup") / filename):
        raise RuntimeError("Restore failed")
