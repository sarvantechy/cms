from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TenantSummary(BaseModel):
    """Expose safe tenant identity and branding fields to an authenticated client."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    key: str
    display_name: str
    short_name: str
    status: str
    timezone: str
    primary_color: str
    accent_color: str
