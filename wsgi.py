"""WSGI entry point for Gunicorn (used by the web service in docker-compose)."""

from app import create_app

app = create_app()
