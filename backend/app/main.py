from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import analyze, time_series

app = FastAPI(
    title="CropSight API",
    description="Backend architecture for AI-powered crop health analysis",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production (e.g. localhost:5173, production.app.co)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router, prefix="", tags=["Analysis"])
app.include_router(time_series.router, prefix="/api", tags=["Time Series Data"])

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}
