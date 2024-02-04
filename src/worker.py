from datetime import datetime, timezone
from src.docker import backup_volume
def backup_volume_task(volume_name):
    dt_now = datetime.now(tz=timezone.utc)
    backup_file = f"{volume_name}-{dt_now.isoformat()}.tar.gz"
    backup_volume(volume_name)

