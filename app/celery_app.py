"""Celery instance + task registration, decoupled from the Flask app factory.

Tasks registered here run inside a Flask app context. When a worker boots this
module directly (``celery -A app.celery_app.celery worker``), there is no
``create_app()`` call at import time, so importing it from ``app.socket`` or
``app.utils.celerytasks`` never triggers the app factory circularly. Instead,
the ``ContextTask`` creates the Flask app lazily when a task actually runs.
"""

from __future__ import annotations

import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

broker = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
backend = os.environ.get("CELERY_BACKEND_URL", "redis://localhost:6379/1")

celery = Celery(
    "betaggregator",
    broker=broker,
    backend=backend,
    include=["app.utils.celerytasks"],
)


class ContextTask(celery.Task):
    """Run tasks inside a Flask app context."""

    abstract = True

    def __call__(self, *args, **kwargs):
        from flask import has_app_context

        if not has_app_context():
            from app import create_app

            app = create_app()
            with app.app_context():
                return self.run(*args, **kwargs)
        return self.run(*args, **kwargs)


celery.Task = ContextTask

# Importing the tasks module registers each ``@celery.task`` on the instance.
# Kept after the celery/ContextTask definition to avoid re-entering this module.
from app.utils import celerytasks  # noqa: E402, F401
