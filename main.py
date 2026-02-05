from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.ats_score import router as ats_router
import os

app = FastAPI(title="ResuCurate ML Services", version="1.0.0")

# Configure CORS - Use environment variable for production, allow all for development
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
if allowed_origins == ["*"]:
    # Development mode - allow all origins
    cors_origins = ["*"]
else:
    # Production mode - use specific origins
    cors_origins = [origin.strip() for origin in allowed_origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ats_router)

@app.get("/")
async def root():
    return {"message": "ResuCurate ML Services API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
