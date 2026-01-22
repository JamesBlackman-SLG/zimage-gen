"""Route modules."""

from app.routes.api import router as api_router
from app.routes.generate import router as generate_router
from app.routes.images import router as images_router

__all__ = ["api_router", "generate_router", "images_router"]
