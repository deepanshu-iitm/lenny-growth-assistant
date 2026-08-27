from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.db import init_db, ping_db
from app.sessions import router as sessions_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Lenny Growth Assistant", lifespan=lifespan)
app.include_router(sessions_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    try:
        await ping_db()
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "database": "down",
                "error": str(exc),
            },
        )
    return {"status": "ok", "database": "up"}
