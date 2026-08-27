from fastapi import FastAPI

app = FastAPI(title="Lenny Growth Assistant")


@app.get("/health")
def health():
    return {"status": "ok"}
