from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from src.dev_env_requests.models.enums import EnvironmentType, OSType, RequestStatus


class EnvironmentRequestCreate(BaseModel):
    requester_name: str = Field(..., max_length=100)
    requester_email: EmailStr
    team: str = Field(..., max_length=100)
    env_name: str = Field(..., max_length=100)
    env_type: EnvironmentType
    os_type: OSType
    os_version: str = Field(..., max_length=50)
    cpu_cores: int = Field(default=2, ge=1)
    ram_gb: int = Field(default=4, ge=1)
    storage_gb: int = Field(default=50, ge=1)
    required_tools: Optional[str] = None
    purpose: str
    duration_days: int = Field(default=30, ge=1)


class EnvironmentRequestUpdate(BaseModel):
    env_name: Optional[str] = Field(default=None, max_length=100)
    env_type: Optional[EnvironmentType] = None
    os_type: Optional[OSType] = None
    os_version: Optional[str] = Field(default=None, max_length=50)
    cpu_cores: Optional[int] = Field(default=None, ge=1)
    ram_gb: Optional[int] = Field(default=None, ge=1)
    storage_gb: Optional[int] = Field(default=None, ge=1)
    required_tools: Optional[str] = None
    purpose: Optional[str] = None
    duration_days: Optional[int] = Field(default=None, ge=1)


class EnvironmentRequestReview(BaseModel):
    status: RequestStatus
    reviewed_by: str = Field(..., max_length=100)
    rejection_reason: Optional[str] = None


class EnvironmentRequestResponse(BaseModel):
    id: UUID
    requester_name: str
    requester_email: str
    team: str
    env_name: str
    env_type: EnvironmentType
    os_type: OSType
    os_version: str
    cpu_cores: int
    ram_gb: int
    storage_gb: int
    required_tools: Optional[str]
    purpose: str
    duration_days: int
    status: RequestStatus
    rejection_reason: Optional[str]
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EnvRequestStats(BaseModel):
    total: int
    pending: int = 0
    approved: int = 0
    rejected: int = 0
    provisioning: int = 0
    active: int = 0
    expired: int = 0
    cancelled: int = 0
