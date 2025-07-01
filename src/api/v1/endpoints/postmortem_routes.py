from uuid import UUID
from typing import Annotated, List

from fastapi import (
    APIRouter,
    Depends,
    status,
    Response
)

from src.models.user import (
    User
)
from src.dependencies.service_deps import (
    get_postmortem_service
)
from src.dependencies.auth_deps import (
    get_current_active_user
)
from src.services.postmortem_service import (
    PostmortemService
)
from src.api.v1.schemas.postmortem_schemas import (
    PostMortemRead,
    PostMortemCreate,
    PostMortemUpdate
)


pm_router = APIRouter(
    prefix="/postmortems",
    dependencies=[
        Depends(
            get_current_active_user
        )
    ]
)


@pm_router.post(
    "/",
    response_model=PostMortemRead,
    status_code=status.HTTP_201_CREATED,
    summary=(
        "Create a new Post-mortem "
        "for a Resolved Incident"
    )
)
async def create_postmortem(
    postmortem_in: PostMortemCreate,
    postmortem_service: Annotated[
        PostmortemService,
        Depends(
            get_postmortem_service
        )
    ],
    current_user: Annotated[
        User,
        Depends(
            get_current_active_user
        )
    ]
) -> PostMortemRead:
    """
    Creates a new draft post-mortem linked
    to a specific resolved incident.
    - **incident_id**:
      The UUID of the incident that
      must be in 'Resolved' status.
    """

    new_postmortem = await \
        postmortem_service.create_postmortem(
            incident_id=postmortem_in.incident_id,
            current_user=current_user
        )

    return new_postmortem


@pm_router.get(
    "/",
    response_model=List[
        PostMortemRead
    ]
)
async def list_postmortems(
    skip: int = 0,
    limit: int = 100,
    service: PostmortemService = Depends(
        get_postmortem_service
    )
) -> List[PostMortemRead]:
    """
    Retrieve a list of all postmortem reports.
    """

    postmortems = await \
        service.get_all_postmortems(
            skip=skip,
            limit=limit
        )

    return postmortems


@pm_router.get(
    "/{postmortem_id}",
    response_model=PostMortemRead,
    status_code=status.HTTP_200_OK,
    summary="Get a Post-mortem by ID"
)
async def get_postmortem(
    postmortem_id: UUID,
    postmortem_service: Annotated[
        PostmortemService,
        Depends(
            get_postmortem_service
        )
    ]
) -> PostMortemRead:
    """
    Retrieves the full details of a
    single post-mortem by its unique ID.
    """

    postmortem = await \
        postmortem_service.get_postmortem_by_id(
            postmortem_id=postmortem_id
        )

    return postmortem


@pm_router.put(
    "/{postmortem_id}",
    response_model=PostMortemRead,
    status_code=status.HTTP_200_OK,
    summary="Update a Post-mortem"
)
async def update_postmortem(
    postmortem_id: UUID,
    postmortem_update: PostMortemUpdate,
    postmortem_service: Annotated[
        PostmortemService,
        Depends(
            get_postmortem_service
        )
    ],
    current_user: Annotated[
        User,
        Depends(
            get_current_active_user
        )
    ]
) -> PostMortemRead:
    """
    Updates the general details of a
    post-mortem, such as its status,
    links, RCA, and lessons learned.
    """

    updated_postmortem = await \
        postmortem_service.update_postmortem(
            postmortem_id=postmortem_id,
            update_data=postmortem_update,
            current_user=current_user
        )

    return updated_postmortem


@pm_router.delete(
    "/{postmortem_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Post-mortem"
)
async def delete_postmortem(
    postmortem_id: UUID,
    postmortem_service: Annotated[
        PostmortemService,
        Depends(
            get_postmortem_service
        )
    ],
    current_user: Annotated[
        User,
        Depends(
            get_current_active_user
        )
    ]
) -> Response:
    """
    Deletes a post-mortem.
    Only the incident
    commander or a superuser
    can perform this action.
    """

    await postmortem_service.delete_postmortem(
        postmortem_id=postmortem_id,
        current_user=current_user
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )
