import os
from datetime import datetime
from functools import lru_cache
from python_on_whales import DockerClient, DockerException, Volume

BACKUP_DIR = os.getenv("BACKUP_DIR")


@lru_cache
def get_docker_client():
    if is_docker_rootless():
        return DockerClient(
            host=f'unix://{os.getenv("XDG_RUNTIME_DIR")}/docker.sock',
        )
    return DockerClient()


def is_docker_rootless():
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


def backup_volume(volume_name: str):
    client = get_docker_client()

    dt_now = datetime.now(tz=datetime.utcnow().astimezone().tzinfo)
    backup_file = f"{volume_name}-{dt_now.isoformat()}.tar.gz"

    volume = get_volume(volume_name)

    if not volume:
        raise Exception(f"Volume {volume_name} does not exist")

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
        raise Exception("Backup failed")
