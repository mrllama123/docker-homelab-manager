import os

from sqlmodel import SQLModel, create_engine

sqlite_url = os.environ.get("DATABASE_URL", f"sqlite://")

engine = create_engine(sqlite_url, echo=True, connect_args={"check_same_thread": False})


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
