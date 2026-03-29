from datetime import datetime
from typing import Optional

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from src.dev_env_requests.models.enums import EnvironmentType, OSType, RequestStatus


class EnvironmentRequest(UUIDAuditBase):
    """SQLAlchemy model for a developer environment request.

    Attributes:
        requester_name: Full name of the person requesting the environment.
        requester_email: Email address of the requester.
        team: Team the requester belongs to.
        env_name: Slugified name for the environment.
        env_type: Type of environment (development, testing, etc).
        os_type: Operating system for the environment.
        os_version: Version of the operating system.
        cpu_cores: Number of CPU cores requested.
        ram_gb: Amount of RAM in gigabytes requested.
        storage_gb: Amount of storage in gigabytes requested.
        required_tools: Comma-separated list of tools to install.
        purpose: Description of what the environment will be used for.
        duration_days: How long the environment is needed in days.
        status: Current status of the request.
        rejection_reason: Reason for rejection if applicable.
        reviewed_by: Name of the admin who reviewed the request.
        reviewed_at: Timestamp of when the request was reviewed.
        expires_at: Timestamp of when the environment will expire.

    Note:
        id, created_at, updated_at are inherited from UUIDAuditBase.
    """

    __tablename__ = "environment_requests"
    __table_args__ = (Index("ix_env_requests_status_created", "status", "created_at"),)

    # Requester
    requester_name: Mapped[str] = mapped_column(String(100))
    requester_email: Mapped[str] = mapped_column(String(255), index=True)
    team: Mapped[str] = mapped_column(String(100))

    # Environment details
    env_name: Mapped[str] = mapped_column(String(100))
    env_type: Mapped[EnvironmentType] = mapped_column(SAEnum(EnvironmentType))
    os_type: Mapped[OSType] = mapped_column(SAEnum(OSType))
    os_version: Mapped[str] = mapped_column(String(50))

    # Resource specs
    cpu_cores: Mapped[int] = mapped_column(default=2)
    ram_gb: Mapped[int] = mapped_column(default=4)
    storage_gb: Mapped[int] = mapped_column(default=50)

    # Tools & purpose
    required_tools: Mapped[Optional[str]] = mapped_column(Text)
    purpose: Mapped[str] = mapped_column(Text)
    duration_days: Mapped[int] = mapped_column(default=30)

    # Status & workflow
    status: Mapped[RequestStatus] = mapped_column(
        SAEnum(RequestStatus),
        default=RequestStatus.PENDING,
        index=True,
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(100))
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return (
            f"<EnvironmentRequest "
            f"id={self.id} "
            f"env={self.env_name!r} "
            f"status={self.status}>"
        )
