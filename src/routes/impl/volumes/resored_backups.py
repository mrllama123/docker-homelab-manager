from sqlmodel import Session, or_, select

from src.models import RestoredBackups


def db_list_restored_backups(
    session: Session,
    restore_ids: list[str] | None = None,
    created_at: str | None = None,
    successful: bool | None = None,
    backup_filename: str | None = None,
) -> list[RestoredBackups]:
    query = select(RestoredBackups)
    where_clauses = []
    if restore_ids:
        where_clauses.append(
            or_(
                *[
                    RestoredBackups.restore_id == restore_id
                    for restore_id in restore_ids
                ],
            ),
        )

    if created_at:
        where_clauses.append(RestoredBackups.created_at == created_at)

    if successful is not None:
        where_clauses.append(RestoredBackups.successful == successful)

    if backup_filename:
        where_clauses.append(RestoredBackups.backup_filename == backup_filename)

    if where_clauses:
        query = query.where(*where_clauses)
    return session.exec(query).all()
