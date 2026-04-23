from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter()


class HealthCheck(BaseModel):
    """
    Response model used for health check endpoint.

    This model represents the standard response returned when checking
    the application's health status.

    """

    status: str = "OK"


@router.get(
    "",
    tags=["Health Check"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
)
def get_health() -> HealthCheck:
    """
    Check the health status of the application.

    This endpoint is used to verify that the service is running correctly.
    It returns a simple status response indicating the API is operational.

    Returns:
        HealthCheck: An object containing the current health status.
    """
    return HealthCheck(status="OK")
