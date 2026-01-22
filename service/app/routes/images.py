"""Image retrieval endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_session
from app.services.storage import get_image_path, get_image_record, get_total_count, list_images

router = APIRouter(prefix="/images", tags=["images"])


class ImageMetadata(BaseModel):
    """Image metadata response model."""

    id: str
    prompt: str
    seed: int
    width: int
    height: int
    created_at: str


class ImageListResponse(BaseModel):
    """Response model for image listing."""

    images: list[ImageMetadata]
    total: int
    limit: int
    offset: int


@router.get("", response_model=ImageListResponse)
async def list_all_images(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List recent images with pagination."""
    images = await list_images(session, limit=limit, offset=offset)
    total = await get_total_count(session)

    return ImageListResponse(
        images=[
            ImageMetadata(
                id=img.id,
                prompt=img.prompt,
                seed=img.seed,
                width=img.width,
                height=img.height,
                created_at=img.created_at.isoformat(),
            )
            for img in images
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{image_id}")
async def get_image(image_id: str):
    """Get an image file by ID."""
    path = get_image_path(image_id)
    if not path:
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path, media_type="image/png")


@router.get("/{image_id}/metadata", response_model=ImageMetadata)
async def get_image_metadata(
    image_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Get image metadata by ID."""
    record = await get_image_record(session, image_id)
    if not record:
        raise HTTPException(status_code=404, detail="Image not found")

    return ImageMetadata(
        id=record.id,
        prompt=record.prompt,
        seed=record.seed,
        width=record.width,
        height=record.height,
        created_at=record.created_at.isoformat(),
    )
