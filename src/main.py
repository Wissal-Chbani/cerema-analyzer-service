from fastapi import FastAPI

app = FastApi()

@app.get("/api/v0")
def read_root():
    return {"status": "ok"}