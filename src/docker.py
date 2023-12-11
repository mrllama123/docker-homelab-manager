import os
from datetime import datetime
from functools import lru_cache

import docker

BACKUP_DIR = os.getenv("BACKUP_DIR")


@lru_cache
def get_docker_client():
    if is_docker_rootless():
        return docker.DockerClient(
            base_url=f'unix://{os.getenv("XDG_RUNTIME_DIR")}/docker.sock',
        )
    return docker.DockerClient(base_url="unix://var/run/docker.sock")


def is_docker_rootless():
    return not os.path.exists("/var/run/docker.sock")


def get_volumes():
    client = get_docker_client()
    volumes = client.volumes.list()
    return volumes


def get_volume(volume_name: str) -> docker.models.volumes.Volume | None:
    client = get_docker_client()
    try:
        volume = client.volumes.get(volume_name)
        return volume
    except docker.errors.NotFound:
        return None
    except Exception as e:
        raise e


def backup_volume(volume_name: str, backup_vol_name: str):
    client = get_docker_client()
    dt_now = datetime.now(tz=datetime.utcnow().astimezone().tzinfo)
    backup_file = f"{volume_name}-{dt_now.isoformat()}.tar.gz"
    output = client.containers.run(
        "busybox",
        command=f"tar cvaf /dest/{backup_file} -C /source .",
        remove=True,
        volumes={
            volume_name: {"bind": "/source", "mode": "rw"},
            BACKUP_DIR: {"bind": "/dest", "mode": "rw"},
        },
        stdout=True,
    )
    print(output.decode("utf-8"))
