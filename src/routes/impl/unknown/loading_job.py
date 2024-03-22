from sqlmodel import Session
from src.models import UnknownLoadingJob


def create_loading_job(session: Session) -> UnknownLoadingJob:
    job = UnknownLoadingJob(progress=0)
    session.add(job)
    session.commit()
    return job


def get_loading_job(session: Session, job_id: int) -> UnknownLoadingJob | None:
    job = session.get(UnknownLoadingJob, job_id)
    return job


def update_loading_job(
    session: Session, job_id: int, progress: int
) -> UnknownLoadingJob | None:
    job_db = session.get(UnknownLoadingJob, job_id)
    if job_db:
        job_db.progress = progress
        session.add(job_db)
        session.commit()
    return job_db
