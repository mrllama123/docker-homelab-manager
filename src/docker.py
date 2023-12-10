import shutil
import tempfile
import docker
from functools import lru_cache
import os
import subprocess
from fastapi import HTTPException
from datetime import datetime


@lru_cache()
def get_docker_client():
    if is_docker_rootless():
        return docker.DockerClient(
            base_url=f'unix://{os.getenv("XDG_RUNTIME_DIR")}/docker.sock'
        )
    return docker.DockerClient(base_url="unix://var/run/docker.sock")


def is_docker_rootless():
    return not os.path.exists('/var/run/docker.sock')
    # try:
    #     output = subprocess.check_output(
    #         ["docker", "info", "--format", "{{.SecurityOptions}}"]
    #     )
    #     return "rootless" in output.decode("utf-8")
    # except subprocess.CalledProcessError:
    #     return False


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

def backup_volume(volume_name: str, backup_folder: str):
    client = get_docker_client()
    temp_dir = tempfile.mkdtemp()
    backup_file = f"{volume_name}-{datetime.now().isoformat()}.tar.gz"
    client.containers.run(
        "busybox",
        command=f"tar cvaf /dest/{backup_file} -C /source .",
        remove=True,
        volumes={
            volume_name: {"bind": "/source", "mode": "rw"},
            temp_dir: {"bind": "/dest", "mode": "rw"},
        },
    )
    # move file to /backup folder
    shutil.move(os.path.join(temp_dir, backup_file), backup_folder)

