from typing import Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, delete, get, patch, post
from litestar.exceptions import NotFoundException, ValidationException
from litestar.params import Dependency
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT

from src.dev_env_requests.logging import get_logger
from src.dev_env_requests.models.enums import RequestStatus
from src.dev_env_requests.schemas.request import (
    EnvironmentRequestCreate,
    EnvironmentRequestResponse,
    EnvironmentRequestReview,
    EnvironmentRequestUpdate,
    EnvRequestStats,
)
from src.dev_env_requests.services.request import EnvironmentRequestService

logger = get_logger(__name__)


class EnvironmentRequestController(Controller):
    """CRUD controller for developer environment requests."""

    path = "/environment-requests"
    tags = ["Environment Requests"]
    dependencies = providers.create_service_dependencies(
        EnvironmentRequestService,
        "env_request_service",
        filters={
            "pagination_type": "limit_offset",
            "id_filter": UUID,
            "search": "env_name",
            "search_ignore_case": True,
        },
    )

    @post("/", summary="Submit a new environment request", status_code=HTTP_201_CREATED)
    async def create_request(
        self,
        data: EnvironmentRequestCreate,
        env_request_service: EnvironmentRequestService,
    ) -> EnvironmentRequestResponse:
        """Create a new environment request.

        Args:
            data: Validated request creation payload.
            env_request_service: Injected service instance.

        Returns:
            EnvironmentRequestResponse: The created request.
        """
        obj = await env_request_service.create(data)
        logger.info(
            "environment_request_created",
            request_id=str(obj.id),
            env_name=obj.env_name,
            requester=obj.requester_email,
        )
        return env_request_service.to_schema(
            obj, schema_type=EnvironmentRequestResponse
        )

    @get("/", summary="List all environment requests", status_code=HTTP_200_OK)
    async def list_requests(
        self,
        env_request_service: EnvironmentRequestService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> service.OffsetPagination[EnvironmentRequestResponse]:
        """List environment requests with pagination and filtering.

        Args:
            env_request_service: Injected service instance.
            filters: Injected pagination and search filters.

        Returns:
            OffsetPagination: Paginated list of requests.
        """
        results, total = await env_request_service.list_and_count(*filters)
        return env_request_service.to_schema(
            results,
            total,
            filters=filters,
            schema_type=EnvironmentRequestResponse,
        )

    @get(
        "/{request_id:uuid}",
        summary="Get a single environment request",
        status_code=HTTP_200_OK,
    )
    async def get_request(
        self,
        request_id: UUID,
        env_request_service: EnvironmentRequestService,
    ) -> EnvironmentRequestResponse:
        """Retrieve a single environment request by ID.

        Args:
            request_id: UUID of the request.
            env_request_service: Injected service instance.

        Returns:
            EnvironmentRequestResponse: The matched request.

        Raises:
            NotFoundException: If the request does not exist.
        """
        obj = await env_request_service.get(request_id)
        if not obj:
            raise NotFoundException(
                detail=f"Environment request {request_id} not found"
            )
        return env_request_service.to_schema(
            obj, schema_type=EnvironmentRequestResponse
        )

    @patch(
        "/{request_id:uuid}",
        summary="Update an environment request",
        status_code=HTTP_200_OK,
    )
    async def update_request(
        self,
        request_id: UUID,
        data: EnvironmentRequestUpdate,
        env_request_service: EnvironmentRequestService,
    ) -> EnvironmentRequestResponse:
        """Update a pending environment request.

        Args:
            request_id: UUID of the request to update.
            data: Fields to update.
            env_request_service: Injected service instance.

        Returns:
            EnvironmentRequestResponse: The updated request.

        Raises:
            NotFoundException: If the request does not exist.
            ValidationException: If the request is not in pending status.
        """
        obj = await env_request_service.get(request_id)
        if not obj:
            raise NotFoundException(
                detail=f"Environment request {request_id} not found"
            )
        if obj.status != RequestStatus.PENDING:
            raise ValidationException(
                detail=f"Cannot update request with status: {obj.status}"
            )
        updated = await env_request_service.update(
            data.model_dump(exclude_unset=True),
            item_id=request_id,
        )
        logger.info("environment_request_updated", request_id=str(request_id))
        return env_request_service.to_schema(
            updated, schema_type=EnvironmentRequestResponse
        )

    @patch(
        "/{request_id:uuid}/review",
        summary="Approve or reject a request",
        status_code=HTTP_200_OK,
        tags=["Admin"],
    )
    async def review_request(
        self,
        request_id: UUID,
        data: EnvironmentRequestReview,
        env_request_service: EnvironmentRequestService,
    ) -> EnvironmentRequestResponse:
        """Approve or reject a pending environment request.

        Args:
            request_id: UUID of the request to review.
            data: Review decision and reviewer info.
            env_request_service: Injected service instance.

        Returns:
            EnvironmentRequestResponse: The reviewed request.

        Raises:
            NotFoundException: If the request does not exist.
            ValidationException: If request is not pending or rejection has no reason.
        """
        obj = await env_request_service.get(request_id)
        if not obj:
            raise NotFoundException(
                detail=f"Environment request {request_id} not found"
            )
        if obj.status != RequestStatus.PENDING:
            raise ValidationException(
                detail=f"Can only review pending requests. Current status: {obj.status}"
            )
        if data.status == RequestStatus.REJECTED and not data.rejection_reason:
            raise ValidationException(
                detail="rejection_reason is required when rejecting"
            )
        reviewed = await env_request_service.review(request_id, data)
        logger.info(
            "environment_request_reviewed",
            request_id=str(request_id),
            status=data.status,
            reviewed_by=data.reviewed_by,
        )
        return env_request_service.to_schema(
            reviewed, schema_type=EnvironmentRequestResponse
        )

    @patch(
        "/{request_id:uuid}/cancel",
        summary="Cancel a request",
        status_code=HTTP_200_OK,
    )
    async def cancel_request(
        self,
        request_id: UUID,
        env_request_service: EnvironmentRequestService,
    ) -> EnvironmentRequestResponse:
        """Cancel a pending or approved environment request.

        Args:
            request_id: UUID of the request to cancel.
            env_request_service: Injected service instance.

        Returns:
            EnvironmentRequestResponse: The cancelled request.

        Raises:
            NotFoundException: If the request does not exist.
            ValidationException: If the request cannot be cancelled.
        """
        obj = await env_request_service.get(request_id)
        if not obj:
            raise NotFoundException(
                detail=f"Environment request {request_id} not found"
            )
        if obj.status not in {RequestStatus.PENDING, RequestStatus.APPROVED}:
            raise ValidationException(
                detail=f"Cannot cancel request with status: {obj.status}"
            )
        cancelled = await env_request_service.cancel(request_id)
        logger.info("environment_request_cancelled", request_id=str(request_id))
        return env_request_service.to_schema(
            cancelled, schema_type=EnvironmentRequestResponse
        )

    @delete(
        "/{request_id:uuid}",
        summary="Delete a request",
        status_code=HTTP_204_NO_CONTENT,
    )
    async def delete_request(
        self,
        request_id: UUID,
        env_request_service: EnvironmentRequestService,
    ) -> None:
        """Delete an environment request permanently.

        Args:
            request_id: UUID of the request to delete.
            env_request_service: Injected service instance.

        Raises:
            NotFoundException: If the request does not exist.
        """
        obj = await env_request_service.get(request_id)
        if not obj:
            raise NotFoundException(
                detail=f"Environment request {request_id} not found"
            )
        await env_request_service.delete(request_id)
        logger.info("environment_request_deleted", request_id=str(request_id))

    @get(
        "/stats",
        summary="Get request statistics",
        status_code=HTTP_200_OK,
        tags=["Admin"],
    )
    async def get_stats(
        self,
        env_request_service: EnvironmentRequestService,
    ) -> EnvRequestStats:
        """Return counts of requests grouped by status.

        Args:
            env_request_service: Injected service instance.

        Returns:
            EnvRequestStats: Counts per status and total.
        """
        return EnvRequestStats(**(await env_request_service.get_stats()))
