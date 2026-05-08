from pydantic_settings import BaseSettings


class CelerySettings(BaseSettings):
    """
    Central Celery configuration.

    Keeps broker/backend settings separate from application logic.
    """

    BROKER_URL: str = "redis://localhost:6379/0"
    RESULT_BACKEND: str = "redis://localhost:6379/0"

    TIMEZONE: str = "UTC"
    ENABLE_UTC: bool = True


settings = CelerySettings()