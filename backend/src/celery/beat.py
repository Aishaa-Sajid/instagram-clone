from src.celery.app import celery_app

# Run beat scheduler:
# celery -A src.celery.beat beat --loglevel=info