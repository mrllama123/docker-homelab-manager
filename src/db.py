from typing import Optional
import os
from sqlmodel import Field, SQLModel, create_engine
from src.models import *


sqlite_url = os.environ.get("DATABASE_URL", f"sqlite://")

engine = create_engine(sqlite_url, echo=True, connect_args={"check_same_thread": False})


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
