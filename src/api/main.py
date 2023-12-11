import os
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.docker import get_volume, get_volumes


from src.celery.worker import create_volume_backup

app = FastAPI()


class VolumeItem(BaseModel):
    id: str
    shortId: str
    name: str
    attrs: dict[str, Any]


class BackupVolumeResponse(BaseModel):
    message: str
    task_id: str


class BackupStatusResponse(BaseModel):
    status: str
    result: Any


@app.get("/volumes", description="Get a list of all Docker volumes")
async def api_volumes() -> list[VolumeItem]:
    volumes = get_volumes()
    return [
        {
            "id": volume.id,
            "shortId": volume.short_id,
            "name": volume.name,
            "attrs": volume.attrs,
        }
        for volume in volumes
    ]


@app.post("/backup/{volume_name}", description="Backup a Docker volume")
def api_backup_volume(volume_name: str) -> BackupVolumeResponse:
    if not get_volume(volume_name):
        raise HTTPException(
            status_code=404,
            detail=f"Volume {volume_name} does not exist",
        )

    task = create_volume_backup.delay(volume_name)
    return {"message": f"Backup of {volume_name} started", "task_id": task.id}


@app.get("/backup/status/{task_id}", description="Get the status of a backup task")
def api_backup_status(task_id: str) -> BackupStatusResponse:
    task = create_volume_backup.AsyncResult(task_id)
    return {"status": task.status, "result": task.result}
