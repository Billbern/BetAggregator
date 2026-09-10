"""Celery entry point for workers.

Run with:  celery -A app.celery_app.celery worker --loglevel=info
"""
from app import create_app
from app.config.celeryconfig import make_celery

flask_app = create_app()
celery = make_celery(flask_app, include=["app.utils.celerytasks"])
