from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from advanced_alchemy.extensions.litestar import service

from src.dev_env_requests.models.enums import RequestStatus
from src.dev_env_requests.models.request import EnvironmentRequest
from src.dev_env_requests.repositories.request import EnvironmentRequestRepository
from src.dev_env_requests.schemas.request import (
    EnvironmentRequestCreate,
    EnvironmentRequestReview,
)


class EnvironmentRequestService(
    service.SQLAlchemyAsyncRepositoryService[EnvironmentRequest]
):
    """Service for environment request business logic.

    Note:
        Standard CRUD (create, get, list, update, delete) is inherited.
        Custom workflow methods (review, cancel) are defined here.
    """

    repository_type = EnvironmentRequestRepository

    async def create(
        self,
        data: EnvironmentRequestCreate | dict[str, Any],
        **kwargs: Any,
    ) -> EnvironmentRequest:
        """Create a new environment request with expiry date.

        Args:
            data: Request creation schema or dict.
            **kwargs: Additional arguments passed to the parent.

        Returns:
            EnvironmentRequest: The newly created request.
        """
        if isinstance(data, EnvironmentRequestCreate):
            payload = data.model_dump()
        else:
            payload = data

        payload["expires_at"] = datetime.now(tz=timezone.utc) + timedelta(
            days=payload.get("duration_days", 30)
        )
        return await super().create(payload, **kwargs)

    async def review(
        self,
        item_id: UUID,
        data: EnvironmentRequestReview,
    ) -> EnvironmentRequest:
        """Approve or reject a pending environment request.

        Args:
            item_id: UUID of the request to review.
            data: Review schema containing status and reviewer info.

        Returns:
            EnvironmentRequest: The updated request.
        """
        return await self.update(
            {
                "status": data.status,
                "reviewed_by": data.reviewed_by,
                "reviewed_at": datetime.now(tz=timezone.utc),
                "rejection_reason": data.rejection_reason,
            },
            item_id=item_id,
        )

    async def cancel(self, item_id: UUID) -> EnvironmentRequest:
        """Cancel a pending or approved environment request.

        Args:
            item_id: UUID of the request to cancel.

        Returns:
            EnvironmentRequest: The cancelled request.
        """
        return await self.update(
            {"status": RequestStatus.CANCELLED},
            item_id=item_id,
        )

    async def get_stats(self) -> dict[str, int]:
        """Return counts of requests grouped by status.

        Returns:
            dict[str, int]: Mapping of status to count, plus total.
        """
        all_requests, total = await self.list_and_count()
        counts: dict[str, int] = {s.value: 0 for s in RequestStatus}
        for req in all_requests:
            counts[req.status.value] += 1
        return {"total": total, **counts}
