import uuid
import logging

logger = logging.getLogger(__name__)

JOBS = {}


def create_loading_job() -> str:
    job_id = str(uuid.uuid4())
    JOBS[job_id] = 0
    return job_id


def get_loading_job(job_id: str) -> int | None:
    logger.info(f"Getting job {job_id}")
    logger.info(JOBS)
    return JOBS.get(job_id)


def update_loading_job(job_id: str, progress: int) -> None:
    logger.info(f"Updating job {job_id} to {progress}")
    if job_id not in JOBS.keys():
        raise ValueError("Job not found")
    JOBS[job_id] = progress
