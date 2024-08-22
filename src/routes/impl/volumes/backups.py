from sqlmodel import Session, or_, select

from src.models import Backups, BackUpStatus


def db_list_backups(
    session: Session,
    backup_ids: list[str] | None = None,
    status: BackUpStatus | None = None,
) -> list[Backups]:
    query = select(Backups)
    if backup_ids:
        query = query.where(
            or_(*[Backups.backup_id == backup_id for backup_id in backup_ids]),
        )

    if status:
        query = query.where(Backups.status == status)

    return list(session.exec(query).all())


def db_get_backup(session: Session, backup_id: str) -> Backups | None:
    return session.exec(select(Backups).where(Backups.backup_id == backup_id)).first()
