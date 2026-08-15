from fastapi import FastAPI
from backend.api.router import router as api_router
from backend.api.websocket import ws_router

app = FastAPI(
    title="REWIND Control Plane API",
    version="0.1.0",
    description="Safety Proxy & Transactional Execution Runtime for AI Agents",
)

app.include_router(api_router)
app.include_router(ws_router)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "rewind-backend",
        "version": "0.1.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
