"""Simple API endpoint for direct image generation."""

import time
from collections import defaultdict
from io import BytesIO
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import (
    DEFAULT_HEIGHT,
    DEFAULT_STEPS,
    DEFAULT_WIDTH,
    MAX_DIMENSION,
    MIN_DIMENSION,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW,
)
from app.models.database import get_session
from app.services.generator import GenerationTask, generate_image
from app.services.storage import save_image

router = APIRouter(prefix="/api", tags=["api"])

# Simple in-memory rate limiter
_rate_limit_store: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(client_ip: str) -> bool:
    """Check if client has exceeded rate limit."""
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW

    # Clean old entries
    _rate_limit_store[client_ip] = [
        t for t in _rate_limit_store[client_ip] if t > window_start
    ]

    # Check limit
    if len(_rate_limit_store[client_ip]) >= RATE_LIMIT_REQUESTS:
        return False

    # Record request
    _rate_limit_store[client_ip].append(now)
    return True


@router.get("/generate")
async def api_generate(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    prompt: str = Query(..., min_length=1, max_length=2000),
    width: int = Query(DEFAULT_WIDTH, ge=MIN_DIMENSION, le=MAX_DIMENSION),
    height: int = Query(DEFAULT_HEIGHT, ge=MIN_DIMENSION, le=MAX_DIMENSION),
    steps: int = Query(DEFAULT_STEPS, ge=1, le=50),
    seed: int | None = Query(None),
    save: bool = Query(True, description="Save image to gallery"),
):
    """Generate an image and return it directly as PNG.

    This is a simple synchronous API for external integrations.
    The image is returned directly in the response body.

    Args:
        prompt: The text prompt for image generation (required)
        width: Image width (512-2048, default 2048)
        height: Image height (512-2048, default 2048)
        steps: Number of inference steps (1-50, default 9)
        seed: Random seed for reproducibility (optional)
        save: Whether to save the image to the gallery (default true)

    Returns:
        PNG image data
    """
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds.",
        )

    # Create task
    task = GenerationTask(
        prompt=prompt,
        width=width,
        height=height,
        steps=steps,
        seed=seed,
    )

    try:
        # Generate image
        image = await generate_image(task)

        # Optionally save to gallery
        if save:
            await save_image(
                session=session,
                image=image,
                prompt=prompt,
                seed=task.seed,
                width=width,
                height=height,
            )

        # Convert to PNG bytes
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        return Response(
            content=buffer.getvalue(),
            media_type="image/png",
            headers={
                "X-Seed": str(task.seed),
                "X-Prompt": prompt[:100],
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
