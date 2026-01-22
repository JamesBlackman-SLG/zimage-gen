# Z-Image Web Service

Web service for AI image generation using Z-Image-Turbo.

## Quick Start

```bash
# Install dependencies
cd service
pip install -e .

# Copy and edit configuration
cp .env.example .env

# Start the server (preloads model, then starts)
python run.py
```

The web UI will be available at http://localhost:8080

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web UI |
| `/generate` | POST | Start generation task |
| `/ws/progress/{task_id}` | WS | Real-time progress |
| `/images` | GET | List recent images |
| `/images/{id}` | GET | Get image file |
| `/images/{id}/metadata` | GET | Get image metadata |
| `/api/generate` | GET | Simple API - returns PNG |
| `/health` | GET | Health check |
| `/docs` | GET | Swagger API docs |

## API Examples

### Simple API (returns PNG directly)

```bash
# Basic generation
curl "http://localhost:8080/api/generate?prompt=A%20beautiful%20sunset" -o sunset.png

# With custom dimensions
curl "http://localhost:8080/api/generate?prompt=Mountain%20landscape&width=1024&height=1024" -o landscape.png

# With specific seed for reproducibility
curl "http://localhost:8080/api/generate?prompt=Futuristic%20city&seed=12345" -o city.png

# Without saving to gallery
curl "http://localhost:8080/api/generate?prompt=Quick%20test&save=false" -o test.png
```

### Task-based API (with WebSocket progress)

```bash
# Start generation task
curl -X POST "http://localhost:8080/generate" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A serene forest", "width": 2048, "height": 2048}'

# Response: {"task_id": "uuid-here", "status": "pending"}
# Then connect to WebSocket: ws://localhost:8080/ws/progress/{task_id}
```

### Image Management

```bash
# List recent images
curl "http://localhost:8080/images?limit=10&offset=0"

# Get image file
curl "http://localhost:8080/images/{id}" -o image.png

# Get image metadata
curl "http://localhost:8080/images/{id}/metadata"
```

### Health Check

```bash
curl "http://localhost:8080/health"
# {"status": "healthy", "pipeline_ready": true}
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `ZIMAGE_HOST` | `0.0.0.0` | Server bind address |
| `ZIMAGE_PORT` | `8080` | Server port |
| `ZIMAGE_MODEL_PATH` | `Tongyi-MAI/Z-Image-Turbo` | Model path or HF repo |
| `ZIMAGE_CPU_OFFLOAD` | `true` | Enable CPU offloading |
| `ZIMAGE_DEFAULT_WIDTH` | `2048` | Default image width |
| `ZIMAGE_DEFAULT_HEIGHT` | `2048` | Default image height |
| `ZIMAGE_DEFAULT_STEPS` | `9` | Default inference steps |
| `ZIMAGE_RATE_LIMIT` | `10` | Requests per window |
| `ZIMAGE_RATE_LIMIT_WINDOW` | `60` | Rate limit window (seconds) |
| `ZIMAGE_CORS_ORIGINS` | `*` | Allowed CORS origins |

## Claude Skill Integration

The service includes a skill definition at `skills/zimage-skill.json` for Claude integration.

Example skill usage:
```
Generate an image of a cosmic nebula with vibrant colors
```

Claude can call the `/api/generate` endpoint directly to create images.

## Development

```bash
# Run with auto-reload (development)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# Note: Pipeline is not preloaded in reload mode, first request will be slow
```

## Architecture

```
service/
├── app/
│   ├── main.py           # FastAPI app
│   ├── config.py         # Configuration
│   ├── dependencies.py   # Pipeline singleton
│   ├── routes/           # API endpoints
│   ├── services/         # Business logic
│   ├── models/           # Database models
│   ├── static/           # CSS, JS
│   └── templates/        # HTML
├── images/               # Generated images
├── data/                 # SQLite database
├── skills/               # Claude skill definitions
└── run.py                # Startup script
```
