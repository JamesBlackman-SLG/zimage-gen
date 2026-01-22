"""Configuration settings for Z-Image service."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Server settings
HOST = os.getenv("ZIMAGE_HOST", "0.0.0.0")
PORT = int(os.getenv("ZIMAGE_PORT", "8080"))

# Model settings
MODEL_PATH = os.getenv("ZIMAGE_MODEL_PATH", "Tongyi-MAI/Z-Image-Turbo")
USE_CPU_OFFLOAD = os.getenv("ZIMAGE_CPU_OFFLOAD", "true").lower() == "true"

# Image generation defaults
DEFAULT_WIDTH = int(os.getenv("ZIMAGE_DEFAULT_WIDTH", "2048"))
DEFAULT_HEIGHT = int(os.getenv("ZIMAGE_DEFAULT_HEIGHT", "2048"))
DEFAULT_STEPS = int(os.getenv("ZIMAGE_DEFAULT_STEPS", "9"))
MIN_DIMENSION = 512
MAX_DIMENSION = 2048

# Storage paths
BASE_DIR = Path(__file__).parent.parent
IMAGES_DIR = Path(os.getenv("ZIMAGE_IMAGES_DIR", str(BASE_DIR / "images")))
DATABASE_PATH = Path(os.getenv("ZIMAGE_DATABASE_PATH", str(BASE_DIR / "data" / "images.db")))

# Rate limiting
RATE_LIMIT_REQUESTS = int(os.getenv("ZIMAGE_RATE_LIMIT", "10"))
RATE_LIMIT_WINDOW = int(os.getenv("ZIMAGE_RATE_LIMIT_WINDOW", "60"))

# CORS
CORS_ORIGINS = os.getenv("ZIMAGE_CORS_ORIGINS", "*").split(",")

# Ensure directories exist
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
