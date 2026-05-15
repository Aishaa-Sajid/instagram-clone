from src.celery.celery_app import celery_app
from src.services.email_service import send_verification_email


@celery_app.task(bind=True, max_retries=3)
def send_verification_email_task(self, email: str, token: str):
    try:
        return send_verification_email(email, token)

    except Exception as e:
        raise self.retry(exc=e, countdown=60)