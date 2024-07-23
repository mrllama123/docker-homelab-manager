from sqlmodel import Session, or_, select, func

from src.models import Backups


def db_list_backups(
    session: Session,
    offset: int = 0,
    limit: int = 100,
    backup_ids: list[str] | None = None,
    successful: bool | None = None,
) -> list[Backups]:
    query = select(Backups)
    if backup_ids:
        query = query.where(
            or_(*[Backups.backup_id == backup_id for backup_id in backup_ids])
        )
    if successful is not None:
        query = query.where(Backups.successful == successful)

    return session.exec(query.offset(offset).limit(limit)).all()


def db_get_backup(session: Session, backup_id: str) -> Backups | None:
    return session.exec(select(Backups).where(Backups.backup_id == backup_id)).first()


def db_get_backup_table_count(session: Session) -> int:
    return session.exec(select(func.count()).select_from(Backups)).one()
