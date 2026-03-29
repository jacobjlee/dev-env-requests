from advanced_alchemy.extensions.litestar import repository

from src.dev_env_requests.models.request import EnvironmentRequest


class EnvironmentRequestRepository(
    repository.SQLAlchemyAsyncRepository[EnvironmentRequest]
):
    """Repository for environment request database operations.

    Note:
        Basic CRUD is inherited from SQLAlchemyAsyncRepository.
        Custom workflow operations (review, cancel) are handled
        in the service layer.
    """

    model_type = EnvironmentRequest
