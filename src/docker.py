import logging
import os
from functools import lru_cache

from python_on_whales import DockerClient, DockerException, Volume

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


def backup_volume(volume_name: str, backup_dir: str, filename: str) -> None:
    client = get_docker_client()

    volume = get_volume(volume_name)

    if not volume:
        raise ValueError(f"Volume {volume_name} does not exist")

    logger.info(
        "Backing up volume %s to %s", volume_name, os.path.join(backup_dir, filename)
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
    if not os.path.exists(os.path.join("/backup", filename)):
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
    if not os.path.exists(os.path.join("/backup", filename)):
        raise RuntimeError("Restore failed")
