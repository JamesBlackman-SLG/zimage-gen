#!/usr/bin/env python3
"""Startup script for Z-Image service."""

import asyncio
import signal
import sys
from contextlib import suppress

import uvicorn

from app.config import HOST, PORT
from app.dependencies import cleanup_pipeline, init_pipeline


def handle_shutdown(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\nReceived signal {signum}, shutting down...")
    cleanup_pipeline()
    sys.exit(0)


async def main():
    """Main entry point."""
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    # Preload the model
    print("Preloading Z-Image pipeline...")
    init_pipeline()
    print(f"Pipeline loaded. Starting server on {HOST}:{PORT}")

    # Configure uvicorn
    config = uvicorn.Config(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level="info",
        access_log=True,
    )

    server = uvicorn.Server(config)

    # Run the server
    with suppress(asyncio.CancelledError):
        await server.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete.")
