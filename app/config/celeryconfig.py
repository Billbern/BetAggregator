from celery import Celery


def make_celery(app, include=None):
    """Build a Celery instance whose tasks run inside the Flask app context."""
    celery = Celery(
        app.import_name,
        include=include or [],
        broker=app.config.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
        result_backend=app.config.get(
            "CELERY_BACKEND_URL", "redis://localhost:6379/1"
        ),
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
