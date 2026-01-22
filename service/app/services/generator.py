"""Image generation service."""

import asyncio
from dataclasses import dataclass, field
from typing import Callable
from uuid import uuid4

import torch
from PIL import Image

from app.config import DEFAULT_HEIGHT, DEFAULT_STEPS, DEFAULT_WIDTH
from app.dependencies import get_pipeline


@dataclass
class GenerationTask:
    """Represents an image generation task."""

    task_id: str = field(default_factory=lambda: str(uuid4()))
    prompt: str = ""
    width: int = DEFAULT_WIDTH
    height: int = DEFAULT_HEIGHT
    steps: int = DEFAULT_STEPS
    seed: int | None = None
    status: str = "pending"
    progress: int = 0
    error: str | None = None
    image: Image.Image | None = None


# Active tasks storage
_active_tasks: dict[str, GenerationTask] = {}


def get_task(task_id: str) -> GenerationTask | None:
    """Get a task by ID."""
    return _active_tasks.get(task_id)


def create_task(
    prompt: str,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    steps: int = DEFAULT_STEPS,
    seed: int | None = None,
) -> GenerationTask:
    """Create a new generation task."""
    task = GenerationTask(
        prompt=prompt,
        width=width,
        height=height,
        steps=steps,
        seed=seed,
    )
    _active_tasks[task.task_id] = task
    return task


def remove_task(task_id: str):
    """Remove a completed task."""
    _active_tasks.pop(task_id, None)


async def generate_image(
    task: GenerationTask,
    progress_callback: Callable[[int, int], None] | None = None,
) -> Image.Image:
    """Generate an image from a prompt.

    Args:
        task: The generation task with parameters
        progress_callback: Optional callback(step, total_steps) for progress updates

    Returns:
        The generated PIL Image
    """
    pipe = get_pipeline()
    task.status = "running"

    # Set up seed
    if task.seed is None:
        task.seed = torch.randint(0, 2**32, (1,)).item()

    generator = torch.Generator("cuda").manual_seed(task.seed)

    def callback_on_step_end(pipe, step, timestep, callback_kwargs):
        """Diffusers callback for progress tracking."""
        task.progress = int((step + 1) / task.steps * 100)
        if progress_callback:
            progress_callback(step + 1, task.steps)
        return callback_kwargs

    try:
        # Run generation in a thread pool to not block the event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: pipe(
                prompt=task.prompt,
                height=task.height,
                width=task.width,
                num_inference_steps=task.steps,
                guidance_scale=0.0,
                generator=generator,
                callback_on_step_end=callback_on_step_end,
            ),
        )

        task.image = result.images[0]
        task.status = "completed"
        task.progress = 100
        return task.image

    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        raise
