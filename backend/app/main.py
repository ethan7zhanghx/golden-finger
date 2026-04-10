from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.auth import router as auth_router
from backend.app.api.projects import router as projects_router
from backend.app.api.routes import router as ai_router

app = FastAPI(
    title="金手指 Backend",
    version="0.2.0",
    description="金手指 AI 辅助剧本创作平台后端",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(ai_router)


@app.get("/")
async def root():
    return {"message": "金手指 backend ready"}
