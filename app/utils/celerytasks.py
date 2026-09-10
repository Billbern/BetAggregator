from app.celery_app import celery


@celery.task(name="app.utils.celerytasks.get_bet_slips")
def get_bet_slips():
    """Placeholder for the future scrape-and-persist pipeline (Batch 3)."""
