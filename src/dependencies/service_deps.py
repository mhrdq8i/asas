from fastapi import Depends
from sqlmodel.ext.asyncio.session import (
    AsyncSession
)  # type: ignore

from src.database.session import get_async_session

from src.services.user_service import UserService
# from src.services.alert_service import AlertService # For future use
# from src.services.incident_service import IncidentService # For future use


# --- User Service Dependency ---

def get_user_service(
    db_session: AsyncSession = Depends(get_async_session)
) -> UserService:
    """
    Dependency to get an instance of UserService.
    It initializes the UserService with an active database session.
    """
    return UserService(
        db_session=db_session
    )

# --- Example for other services (for future use) ---
# def get_alert_service(
#     db_session: AsyncSession = Depends(get_async_session)
# ) -> AlertService:
#     """
#     Dependency to get an instance of AlertService.
#     """
#     return AlertService(db_session=db_session)

# def get_incident_service(
#     db_session: AsyncSession = Depends(get_async_session)
# ) -> IncidentService:
#     """
#     Dependency to get an instance of IncidentService.
#     """
#     return IncidentService(db_session=db_session)
