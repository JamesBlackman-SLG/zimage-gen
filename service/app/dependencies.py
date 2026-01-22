"""Pipeline singleton and dependency injection."""

import torch
from diffusers import ZImagePipeline

from app.config import MODEL_PATH, USE_CPU_OFFLOAD

_pipeline: ZImagePipeline | None = None
_pipeline_ready = False


def get_pipeline() -> ZImagePipeline:
    """Get the loaded pipeline instance."""
    global _pipeline
    if _pipeline is None:
        raise RuntimeError("Pipeline not initialized. Call init_pipeline() first.")
    return _pipeline


def is_pipeline_ready() -> bool:
    """Check if the pipeline is loaded and ready."""
    return _pipeline_ready


def init_pipeline() -> ZImagePipeline:
    """Initialize the ZImage pipeline. Called once at startup."""
    global _pipeline, _pipeline_ready

    if _pipeline is not None:
        return _pipeline

    print(f"Loading ZImage pipeline from {MODEL_PATH}...")
    _pipeline = ZImagePipeline.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
    )

    if USE_CPU_OFFLOAD:
        print("Enabling CPU offload...")
        _pipeline.enable_model_cpu_offload()
    else:
        _pipeline = _pipeline.to("cuda")

    _pipeline_ready = True
    print("Pipeline ready!")
    return _pipeline


def cleanup_pipeline():
    """Clean up pipeline resources."""
    global _pipeline, _pipeline_ready
    if _pipeline is not None:
        del _pipeline
        _pipeline = None
        _pipeline_ready = False
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print("Pipeline cleaned up.")
