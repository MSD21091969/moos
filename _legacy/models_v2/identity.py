from typing import Optional
from pydantic import BaseModel, Field

class UserObject(BaseModel):
    """
    Represents an authenticated user in the Collider ecosystem.
    Used for context, ownership, and permission checks.
    """
    id: str = Field(default="guest", description="Unique user identifier")
    email: str = Field(..., description="User email address")
    role: str = Field(default="ACCOUNTUSER", description="User role (ADMIN, ACCOUNTUSER)")
    tier: str = Field(default="free", description="Subscription tier")
    auth_provider_id: str = Field(default="local", description="Auth provider ID")
    display_name: str = Field(default="", description="User display name")
    
    class Config:
        frozen = True
