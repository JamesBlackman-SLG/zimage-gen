"""Image storage service."""

from pathlib import Path
from uuid import uuid4

from PIL import Image
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import IMAGES_DIR
from app.models.database import ImageRecord


async def save_image(
    session: AsyncSession,
    image: Image.Image,
    prompt: str,
    seed: int,
    width: int,
    height: int,
) -> ImageRecord:
    """Save an image to disk and create a database record.

    Args:
        session: Database session
        image: PIL Image to save
        prompt: The prompt used to generate the image
        seed: The seed used for generation
        width: Image width
        height: Image height

    Returns:
        The created ImageRecord
    """
    image_id = str(uuid4())
    filename = f"{image_id}.png"
    filepath = IMAGES_DIR / filename

    # Save image to disk
    image.save(filepath, "PNG")

    # Create database record
    record = ImageRecord(
        id=image_id,
        prompt=prompt,
        seed=seed,
        width=width,
        height=height,
        filepath=str(filepath),
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)

    return record


def get_image_path(image_id: str) -> Path | None:
    """Get the file path for an image by ID."""
    filepath = IMAGES_DIR / f"{image_id}.png"
    if filepath.exists():
        return filepath
    return None


async def get_image_record(
    session: AsyncSession, image_id: str
) -> ImageRecord | None:
    """Get an image record by ID."""
    result = await session.execute(
        select(ImageRecord).where(ImageRecord.id == image_id)
    )
    return result.scalar_one_or_none()


async def list_images(
    session: AsyncSession, limit: int = 20, offset: int = 0
) -> list[ImageRecord]:
    """List recent images with pagination."""
    result = await session.execute(
        select(ImageRecord)
        .order_by(desc(ImageRecord.created_at))
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_total_count(session: AsyncSession) -> int:
    """Get total number of images."""
    from sqlalchemy import func

    result = await session.execute(select(func.count(ImageRecord.id)))
    return result.scalar() or 0


async def delete_image(session: AsyncSession, image_id: str) -> bool:
    """Delete an image record and file."""
    record = await get_image_record(session, image_id)
    if not record:
        return False

    # Delete file
    filepath = Path(record.filepath)
    if filepath.exists():
        filepath.unlink()

    # Delete record
    await session.delete(record)
    await session.commit()
    return True
