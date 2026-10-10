from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(..., description="Operational status of the service")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="API semantic version")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ok",
                "service": "PRAVAAH API",
                "version": "0.1.0",
            }
        }
    )
