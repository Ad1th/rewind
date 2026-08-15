from fastapi import FastAPI

app = FastAPI(
    title="REWIND Control Plane API",
    version="0.1.0",
    description="Safety Proxy & Transactional Execution Runtime for AI Agents"
)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "rewind-backend",
        "version": "0.1.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
