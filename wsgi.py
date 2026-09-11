"""WSGI entry point for Gunicorn (used by the web service in docker-compose)."""

from app import create_app
from whitenoise import WhiteNoise

app = create_app()


application = WhiteNoise(app.wsgi_app, root="app/static")
