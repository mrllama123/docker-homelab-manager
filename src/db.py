import os

from sqlmodel import Session, SQLModel, create_engine

from src.models import *  # pylint: disable=wildcard-import, unused-wildcard-import

sqlite_url = os.environ.get("DATABASE_URL", "sqlite://")

engine = create_engine(sqlite_url, echo=True, connect_args={"check_same_thread": False})


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
