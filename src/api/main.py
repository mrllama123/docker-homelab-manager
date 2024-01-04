from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from src.celery.worker import create_volume_backup
from src.db import Backups, create_db_and_tables, engine
from src.docker import get_volume, get_volumes


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


class VolumeItem(BaseModel):
    name: str
    labels: dict[str, str]
    mountpoint: str
    options: dict[str, str]


class BackupVolumeResponse(BaseModel):
    message: str
    task_id: str


class BackupStatusResponse(BaseModel):
    status: str
    task_id: str
    result: Any


@app.get("/volumes", description="Get a list of all Docker volumes")
async def api_volumes() -> list[VolumeItem]:
    volumes = get_volumes()
    return [
        {
            "name": volume.name,
            "labels": volume.labels or {},
            "mountpoint": str(volume.mountpoint),
            "options": volume.options or {},
        }
        for volume in volumes
    ]


@app.get(
    "/backups", description="Get a list of all backups", response_model=list[Backups]
)
async def api_backups() -> list[Backups]:
    with Session(engine) as session:
        return session.exec(select(Backups)).all()


@app.get(
    "/backups/{backup_name}", description="Get a backup by name", response_model=Backups
)
async def api_backup(backup_name: str) -> Backups:
    with Session(engine) as session:
        backup = session.exec(
            select(Backups).where(Backups.backup_name == backup_name)
        ).first()
        if not backup:
            raise HTTPException(
                status_code=404,
                detail=f"Backup {backup_name} does not exist",
            )
        return backup


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
    return {"status": task.status, "result": task.result, "task_id": task.id}
