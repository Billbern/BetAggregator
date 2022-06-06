from app import celery

@celery.task()
def get_bet_slips():
    pass