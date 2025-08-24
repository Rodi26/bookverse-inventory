from fastapi import FastAPI

app = FastAPI(title="BookVerse Inventory Service")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/info")
def info():
    return {"service": "inventory", "version": "0.1.0"}


