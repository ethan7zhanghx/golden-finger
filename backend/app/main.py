from fastapi import FastAPI

from backend.app.api.routes import router

app = FastAPI(
    title="Jinshouzhi Backend",
    version="0.1.0",
    description="Backend skeleton for the Jinshouzhi platform.",
)
app.include_router(router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "jinshouzhi backend ready"}
