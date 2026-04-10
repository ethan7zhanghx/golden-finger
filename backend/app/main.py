from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.include_router(api_router, prefix=settings.api_v1_str)


@app.get('/healthz', tags=['health'])
def healthcheck() -> dict[str, str]:
    return {'status': 'ok'}
