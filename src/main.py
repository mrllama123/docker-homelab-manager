import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.apschedule.schedule import setup_scheduler
from src.routes import api

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler = setup_scheduler()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(lifespan=lifespan)
app.include_router(api.router)
