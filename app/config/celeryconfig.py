from celery import Celery


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_BACKEND_URL'],
        broker=app.config['CELERY_BROKER_URL']
    )
    
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        
        def __call__(self, *args, **kwds):
            with app.app_context():
                return self.run(*args, **kwds)
    
    celery.Task = ContextTask
    return celery