"""Generation endpoints with WebSocket progress."""

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import DEFAULT_HEIGHT, DEFAULT_STEPS, DEFAULT_WIDTH, MAX_DIMENSION, MIN_DIMENSION
from app.models.database import get_session
from app.services.generator import GenerationTask, create_task, generate_image, get_task, remove_task
from app.services.storage import save_image

router = APIRouter()


class GenerateRequest(BaseModel):
    """Request model for image generation."""

    prompt: str = Field(..., min_length=1, max_length=2000)
    width: int = Field(DEFAULT_WIDTH, ge=MIN_DIMENSION, le=MAX_DIMENSION)
    height: int = Field(DEFAULT_HEIGHT, ge=MIN_DIMENSION, le=MAX_DIMENSION)
    steps: int = Field(DEFAULT_STEPS, ge=1, le=50)
    seed: int | None = None


class GenerateResponse(BaseModel):
    """Response model for generation task creation."""

    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    """Response model for task status."""

    task_id: str
    status: str
    progress: int
    error: str | None = None
    image_id: str | None = None


@router.post("/generate", response_model=GenerateResponse)
async def start_generation(request: GenerateRequest):
    """Start an image generation task."""
    task = create_task(
        prompt=request.prompt,
        width=request.width,
        height=request.height,
        steps=request.steps,
        seed=request.seed,
    )
    return GenerateResponse(task_id=task.task_id, status=task.status)


@router.get("/generate/{task_id}", response_model=TaskStatusResponse)
async def get_generation_status(task_id: str):
    """Get the status of a generation task."""
    task = get_task(task_id)
    if not task:
        return TaskStatusResponse(
            task_id=task_id,
            status="not_found",
            progress=0,
        )
    return TaskStatusResponse(
        task_id=task.task_id,
        status=task.status,
        progress=task.progress,
        error=task.error,
    )


@router.websocket("/ws/progress/{task_id}")
async def websocket_progress(
    websocket: WebSocket,
    task_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """WebSocket endpoint for real-time progress updates during generation."""
    await websocket.accept()

    task = get_task(task_id)
    if not task:
        await websocket.send_json({"error": "Task not found"})
        await websocket.close()
        return

    try:
        # Progress callback that sends updates via WebSocket
        async def send_progress(step: int, total: int):
            try:
                await websocket.send_json({
                    "type": "progress",
                    "step": step,
                    "total": total,
                    "percent": int(step / total * 100),
                })
            except Exception:
                pass

        # Wrapper for sync callback
        loop = asyncio.get_event_loop()

        def progress_callback(step: int, total: int):
            asyncio.run_coroutine_threadsafe(send_progress(step, total), loop)

        # Start generation
        await websocket.send_json({"type": "started", "task_id": task_id})

        image = await generate_image(task, progress_callback)

        # Save the image
        record = await save_image(
            session=session,
            image=image,
            prompt=task.prompt,
            seed=task.seed,
            width=task.width,
            height=task.height,
        )

        await websocket.send_json({
            "type": "completed",
            "image_id": record.id,
            "seed": task.seed,
        })

        # Clean up task
        remove_task(task_id)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
