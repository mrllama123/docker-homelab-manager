from typing import Optional

from sqlmodel import Field, SQLModel, create_engine


class Backups(SQLModel, table=True):
    backup_name: Optional[str] = Field(default=None, primary_key=True)
    backup_path: Optional[str] = Field(default=None)
    backup_created: str
    backup_path: str
    volume_name: str


SQLITE_FILE_NAME = "database.db"
sqlite_url = f"sqlite:////db/{SQLITE_FILE_NAME}"

engine = create_engine(sqlite_url, echo=True, connect_args={"check_same_thread": False})


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
