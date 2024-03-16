from sqlmodel import Session, or_, select

from src.models import RestoredBackups


def db_list_restored_backups(
    session: Session,
    restore_ids: list[str] | None = None,
) -> list[RestoredBackups]:
    query = select(RestoredBackups)
    if restore_ids:
        query = query.where(
            or_(
                *[
                    RestoredBackups.restore_id == restore_id
                    for restore_id in restore_ids
                ]
            )
        )
    return session.exec(query).all()
