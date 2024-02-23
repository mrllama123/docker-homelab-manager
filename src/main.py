import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.apschedule.schedule import setup_scheduler
from src.routes import api, html

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler = setup_scheduler()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="src/static"), name="static")
app.include_router(api.router)
app.include_router(html.router)
