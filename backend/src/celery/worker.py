from src.celery.app import celery_app
import src.celery.tasks 
# Run worker:
# celery -A src.celery.worker worker --loglevel=info