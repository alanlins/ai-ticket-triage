from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from app.routes.tickets import router as tickets_router
from app.schemas import HealthResponse
from app.database import init_db

app = FastAPI(
    title="AI Ticket Triage",
    description="AI-powered support ticket classification and triage service",
    version="1.0.0",
)

# Initialize database tables (only if not in testing mode)
# Tests will handle their own database initialization via conftest
if not os.getenv('PYTEST_CURRENT_TEST'):
    init_db()

# Include routers
app.include_router(tickets_router)


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok")


# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def serve_index():
    """Serve the demo page."""
    index_path = os.path.join(os.path.dirname(__file__), "..", "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return {"message": "Demo page not found. Navigate to /docs for API documentation."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
