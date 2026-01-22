"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from app.config import CORS_ORIGINS
from app.dependencies import cleanup_pipeline, is_pipeline_ready
from app.models.database import init_db
from app.routes import api_router, generate_router, images_router

STATIC_DIR = Path(__file__).parent / "static"
TEMPLATES_DIR = Path(__file__).parent / "templates"

templates = Jinja2Templates(directory=TEMPLATES_DIR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    await init_db()
    print("Database initialized.")
    yield
    # Shutdown
    cleanup_pipeline()
    print("Shutdown complete.")


app = FastAPI(
    title="Z-Image Service",
    description="AI Image Generation Service using Z-Image-Turbo",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Include routers
app.include_router(generate_router)
app.include_router(images_router)
app.include_router(api_router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main web UI."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "ready": is_pipeline_ready()},
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "pipeline_ready": is_pipeline_ready(),
    }
