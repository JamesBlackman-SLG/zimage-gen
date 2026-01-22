"""SQLAlchemy models for image metadata storage."""

from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import DATABASE_PATH


class Base(DeclarativeBase):
    pass


class ImageRecord(Base):
    """Model for storing generated image metadata."""

    __tablename__ = "images"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    prompt: Mapped[str] = mapped_column(String(2000), nullable=False)
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    filepath: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


# Create async engine
async_engine = create_async_engine(
    f"sqlite+aiosqlite:///{DATABASE_PATH}",
    echo=False,
)

# Session factory
async_session_factory = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """Initialize the database schema."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session."""
    async with async_session_factory() as session:
        yield session
