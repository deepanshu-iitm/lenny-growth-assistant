from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.db import ping_db

app = FastAPI(title="Lenny Growth Assistant")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    try:
        await ping_db()
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": "down"},
        )
    return {"status": "ok", "database": "up"}
