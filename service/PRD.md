# Z-Image Web Service PRD

## Overview

Transform the Z-Image generation functionality into a web service with a user-friendly interface, progress tracking, image storage, and a simple API for local network access (enabling Claude skill integration).

## Technical Context

- Base script: `j.py` using `diffusers.ZImagePipeline`
- Model: `Tongyi-MAI/Z-Image-Turbo`
- Generation params: 2048x2048, 9 inference steps, guidance_scale=0.0
- Existing deps: torch, diffusers, pillow, accelerate, huggingface_hub

## Tasks

- [ ] Create app directory structure with main.py, routes, models, services, static, and templates subdirectories
- [ ] Add web dependencies to pyproject.toml: fastapi, uvicorn, websockets, python-multipart, aiosqlite, sqlalchemy
- [ ] Create config.py with environment variables for host, port, model path, image directory, and database path
- [ ] Implement pipeline initialization module that loads ZImagePipeline once at startup with CPU offloading
- [ ] Add health check endpoint at GET /health that returns pipeline status
- [ ] Create WebSocket endpoint at /ws/progress for streaming generation progress using diffusers callback mechanism
- [ ] Build HTML template index.html with prompt input form, progress bar, and image display area
- [ ] Add static JS file for WebSocket client that handles real-time progress updates and displays generated images
- [ ] Add static CSS file for clean minimal styling of the web interface
- [ ] Implement POST /generate endpoint that accepts prompt and returns task ID, queuing generation
- [ ] Design SQLite schema with table for id, prompt, seed, created_at, width, height, filepath
- [ ] Create database.py with SQLAlchemy models for image metadata
- [ ] Implement storage service that saves images to images directory with UUID filename and inserts metadata record
- [ ] Add GET /images/{id} endpoint that returns the image file directly
- [ ] Add GET /images/{id}/metadata endpoint that returns prompt and generation details as JSON
- [ ] Add GET /images endpoint that lists recent images with pagination
- [ ] Add gallery view to web UI showing grid of previous generations with prompts
- [ ] Create GET /api/generate endpoint that accepts prompt as querystring and returns PNG image directly
- [ ] Add request validation for API endpoint with prompt required, max length, dimension bounds 512-2048
- [ ] Implement simple in-memory rate limiting for API endpoint
- [ ] Configure CORS to allow requests from local network IPs
- [ ] Create run.py startup script that preloads model and starts uvicorn server
- [ ] Add graceful shutdown handling to clean up GPU memory and finish pending generation
- [ ] Create .env.example documenting all configuration options
- [ ] Create zimage-skill.json skill definition file for Claude with endpoint, parameters, and response format
- [ ] Add API documentation with example curl commands to README

## Proposed Directory Structure

```
Z-Image/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry
│   ├── config.py            # Configuration
│   ├── dependencies.py      # Pipeline singleton
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── generate.py      # /generate endpoints
│   │   ├── images.py        # /images endpoints
│   │   └── api.py           # /api/generate endpoint
│   ├── services/
│   │   ├── __init__.py
│   │   ├── generator.py     # Image generation logic
│   │   └── storage.py       # Image storage logic
│   ├── models/
│   │   ├── __init__.py
│   │   └── database.py      # SQLAlchemy models
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   └── templates/
│       └── index.html
├── images/                   # Generated images storage
├── data/
│   └── images.db            # SQLite database
├── skills/
│   └── zimage-skill.json    # Claude skill definition
└── run.py                   # Startup script
```

## API Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web UI |
| `/generate` | POST | Start generation (WebSocket for progress) |
| `/ws/progress/{task_id}` | WS | Real-time progress updates |
| `/images` | GET | List recent images |
| `/images/{id}` | GET | Get image file |
| `/images/{id}/metadata` | GET | Get image metadata |
| `/api/generate` | GET | Simple API - returns image directly |
| `/health` | GET | Health check |
| `/docs` | GET | API documentation |

## Success Criteria

1. User can open web UI, enter prompt, see progress, view generated image
2. Generated images persist with prompts and can be retrieved later
3. External service can call GET /api/generate?prompt=... and receive PNG
4. Claude can use this as a skill to generate images on demand
5. Service runs on local network accessible to other machines
