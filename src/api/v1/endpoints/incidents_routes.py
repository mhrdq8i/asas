from uuid import UUID
from typing import (
    List,
    Annotated,
    Optional
)

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query
)

from src.dependencies.service_deps import (
    get_incident_service
)
from src.dependencies.auth_deps import (
    get_current_active_user,
    get_current_active_superuser
)
from src.models.user import (
    User as UserModel
)
from src.models.incident import (
    IncidentStatusEnum,
    SeverityLevelEnum
)
from src.api.v1.schemas.common_schemas import (
    PaginatedResponse
)
from src.api.v1.schemas.incident_schemas import (
    IncidentRead,
    IncidentCreate,
    IncidentProfileUpdate,
    ImpactsUpdate,
    ShallowRCAUpdate,
    TimelineEventCreate,
    CommunicationLogCreate,
)
from src.services.incident_service import (
    IncidentService
)
from src.exceptions.base_exceptions import (
    AppException
)


incidents_router = APIRouter(
    prefix="/incidents",
    # Protect all routes in this router
    dependencies=[
        Depends(
            get_current_active_user
        )
    ]
)


@incidents_router.post(
    "/",
    response_model=IncidentRead,
    status_code=status.HTTP_201_CREATED
)
async def create_incident(
    incident_in: IncidentCreate,
    current_user: Annotated[
        UserModel,
        Depends(
            get_current_active_user
        )
    ],
    incident_service: Annotated[
        IncidentService,
        Depends(
            get_incident_service
        )
    ],
):
    """
    Create a new incident.
    Requires authentication.
    """
    try:
        new_incident = await incident_service.create_incident(
            incident_in=incident_in,
            current_user=current_user
        )
        # We need to refetch the incident to get
        # all eager-loaded fields for the response
        return await incident_service.get_incident_by_id(
            incident_id=new_incident.id
        )

    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )


@incidents_router.get(
    "/",
    response_model=PaginatedResponse[IncidentRead]
)
async def search_incidents(
    incident_service: Annotated[
        IncidentService,
        Depends(get_incident_service)
    ],
    statuses: Optional[
        List[IncidentStatusEnum]
    ] = Query(None),
    severities: Optional[
        List[SeverityLevelEnum]
    ] = Query(None),
    commander_id: Optional[UUID] = Query(None),
    start_date: Optional[str] = Query(
        None,
        description=(
            "Start date in ISO format, "
            "e.g., 2023-01-01T00:00:00"
        )
    ),
    end_date: Optional[str] = Query(
        None,
        description=(
            "End date in ISO format, "
            "e.g., 2023-01-31T23:59:59"
        )
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
):
    """
    Search for incidents with
    various filter criteria.
    """
    incidents = await incident_service.get_incidents_list(
        statuses=statuses,
        severities=severities,
        commander_id=commander_id,
        skip=skip,
        limit=limit
    )

    return incidents


@incidents_router.get(
    "/{incident_id}",
    response_model=IncidentRead
)
async def get_incident(
    incident_id: UUID,
    incident_service: Annotated[
        IncidentService,
        Depends(
            get_incident_service
        )
    ],
):
    """
    Retrieve a single incident by its ID.
    """
    try:
        return await incident_service.get_incident_by_id(
            incident_id=incident_id
        )

    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )


@incidents_router.put(
    "/{incident_id}/profile",
    response_model=IncidentRead
)
async def update_incident_profile(
    incident_id: UUID,
    update_data: IncidentProfileUpdate,
    current_user: Annotated[
        UserModel,
        Depends(
            get_current_active_user
        )
    ],
    incident_service: Annotated[
        IncidentService,
        Depends(
            get_incident_service
        )
    ],
):
    """
    Update the profile of an incident.
    Only the commander or an
    admin can perform this action.
    """
    try:
        await incident_service.update_incident_profile(
            incident_id=incident_id,
            update_data=update_data,
            current_user=current_user
        )
        return await incident_service.get_incident_by_id(
            incident_id=incident_id
        )

    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )


@incidents_router.put(
    "/{incident_id}/impacts",
    response_model=IncidentRead
)
async def update_incident_impacts(
    incident_id: UUID,
    update_data: ImpactsUpdate,
    current_user: Annotated[
        UserModel,
        Depends(
            get_current_active_user
        )
    ],
    incident_service: Annotated[
        IncidentService,
        Depends(
            get_incident_service
        )
    ],
):
    """
    Update the impacts section of an incident.
    Only the commander or an
    admin can perform this action.
    """
    try:
        await incident_service.update_incident_impacts(
            incident_id=incident_id,
            update_data=update_data,
            current_user=current_user
        )
        return await incident_service.get_incident_by_id(
            incident_id=incident_id
        )
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )


@incidents_router.put(
    "/{incident_id}/rca",
    response_model=IncidentRead
)
async def update_shallow_rca(
    incident_id: UUID,
    update_data: ShallowRCAUpdate,
    current_user: Annotated[
        UserModel,
        Depends(
            get_current_active_user
        )
    ],
    incident_service: Annotated[
        IncidentService,
        Depends(
            get_incident_service
        )
    ],
):
    """
    Update the shallow RCA
    section of an incident.
    Only the commander or an
    admin can perform this action.
    """
    try:
        await incident_service.update_shallow_rca(
            incident_id=incident_id,
            update_data=update_data,
            current_user=current_user
        )
        return await incident_service.get_incident_by_id(
            incident_id=incident_id
        )
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )


@incidents_router.post(
    "/{incident_id}/timeline-events",
    response_model=IncidentRead
)
async def add_timeline_event(
    incident_id: UUID,
    event_in: TimelineEventCreate,
    current_user: Annotated[
        UserModel,
        Depends(
            get_current_active_user
        )
    ],
    incident_service: Annotated[
        IncidentService,
        Depends(
            get_incident_service
        )
    ],
):
    """
    Add a new timeline event to an incident.
    """
    try:
        return await incident_service.add_timeline_event(
            incident_id=incident_id,
            event_in=event_in,
            current_user=current_user
        )
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )


@incidents_router.post(
    "/{incident_id}/communication-logs",
    response_model=IncidentRead
)
async def add_communication_log(
    incident_id: UUID,
    log_in: CommunicationLogCreate,
    current_user: Annotated[
        UserModel,
        Depends(
            get_current_active_user
        )
    ],
    incident_service: Annotated[
        IncidentService,
        Depends(
            get_incident_service
        )
    ],
):
    """
    Add a new communication log
    to an incident.
    """
    try:
        return await incident_service.add_communication_log(
            incident_id=incident_id,
            log_in=log_in,
            current_user=current_user
        )
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )


@incidents_router.delete(
    "/{incident_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_incident(
    incident_id: UUID,
    # Requires admin
    current_user: Annotated[
        UserModel,
        Depends(
            get_current_active_superuser
        )
    ],
    incident_service: Annotated[
        IncidentService,
        Depends(
            get_incident_service
        )
    ],
):
    """
    Delete an incident.
    Requires superuser privileges.
    """
    try:
        await incident_service.delete_incident(
            incident_id=incident_id,
            current_user=current_user
        )
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )
