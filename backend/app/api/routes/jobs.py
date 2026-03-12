"""Manual job execution routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_scheduler
from app.schemas.common import JobRunRequest, JobRunResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/run-now", response_model=JobRunResponse)
def run_job_now(
    payload: JobRunRequest,
    scheduler=Depends(get_scheduler),
):
    accepted = scheduler.run_job_now(payload.job_name)
    if not accepted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown job name")
    return JobRunResponse(
        requested_job=payload.job_name,
        accepted_jobs=accepted,
        message="Job dispatch completed synchronously.",
    )
