from fastapi import FastAPI

app = FastAPI(
    title="LRMIS API",
    description="Land Registration Management Information System backend.",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "name": "LRMIS",
        "status": "ready",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}
