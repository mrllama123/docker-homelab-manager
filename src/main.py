import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.apschedule.schedule import setup_scheduler
from src.routes import api, html
from fastapi.middleware.cors import CORSMiddleware
import os

logger = logging.getLogger(__name__)
CORS_ORIGINS = (
    os.getenv("CORS_ORIGINS").split(",") if os.getenv("CORS_ORIGINS") else ["*"]
)

logger.info("CORS allow_origins: %s", CORS_ORIGINS)


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler = setup_scheduler()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="src/static"), name="static")
app.include_router(api.router)
app.include_router(html.router)
