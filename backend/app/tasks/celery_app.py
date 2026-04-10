from __future__ import annotations

from celery import Celery

from backend.app.core.config import settings

celery_app = Celery(
    "jinshouzhi",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_default_queue="default",
    task_track_started=True,
    task_time_limit=360,
    result_expires=3600,
)


@celery_app.task(name="backend.tasks.generate_suggestions")
def generate_suggestions(project_id: str, asset_id: str | None = None) -> dict[str, str | None]:
    return {
        "project_id": project_id,
        "asset_id": asset_id,
        "status": "queued-placeholder",
    }
