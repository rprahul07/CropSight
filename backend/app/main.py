from fastapi import FastAPI
from app.routes import analyze

app = FastAPI(
    title="CropSight API",
    description="Backend architecture for AI-powered crop health analysis",
    version="1.0.0"
)

app.include_router(analyze.router, prefix="", tags=["Analysis"])

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}
