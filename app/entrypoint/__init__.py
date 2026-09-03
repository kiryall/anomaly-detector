"""Entrypoint module: bootstrap and application startup."""

from app.entrypoint.bootstrap import Bootstrap
from app.entrypoint.main import main

__all__ = ["Bootstrap", "main"]
