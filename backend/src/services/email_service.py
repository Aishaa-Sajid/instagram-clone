import smtplib
from email.mime.text import MIMEText
from src.database.config import settings
from loguru import logger

def send_verification_email(email: str, token: str):
    try:
        sender = settings.SMTP_USER
        receiver = email
        password = settings.SMTP_PASS
        port = settings.SMTP_PORT
        host = settings.SMTP_HOST
        verification_link = f"{settings.BASE_URL}/auth/verify-email?token={token}"
        message = f"""
        Click this link to verify your account:
        {verification_link}
        """
        msg = MIMEText(message)
        msg["Subject"] = "Verify your account"
        msg["From"] = sender
        msg["To"] = receiver

        # Send email
        with smtplib.SMTP(host, port) as server:
            server.starttls()  # Secure connection
            server.login(sender, password)
            server.send_message(msg)

        logger.info("Verification email sent")
    except Exception as e:
        logger.error("Failed to send verification email")
        raise Exception("Failed to send verification email") from e
