from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, status, Response

from src.dependencies.service_deps import get_postmortem_service
from src.dependencies.auth_deps import get_current_active_user
from src.services.postmortem_service import PostmortemService
from src.models.user import User
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
    summary="Create a new Post-mortem for a Resolved Incident"
)
async def create_postmortem(
    pm_in: PostMortemCreate,
    pm_service: Annotated[PostmortemService, Depends(get_postmortem_service)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Creates a new draft post-mortem linked to a specific resolved incident.
    - **incident_id**: The UUID of the incident that must be in 'Resolved' status.
    """
    new_pm = await pm_service.create_postmortem(
        incident_id=pm_in.incident_id,
        current_user=current_user
    )
    return new_pm


@pm_router.get(
    "/{postmortem_id}",
    response_model=PostMortemRead,
    status_code=status.HTTP_200_OK,
    summary="Get a Post-mortem by ID"
)
async def get_postmortem(
    postmortem_id: UUID,
    postmortem_service: Annotated[
        PostmortemService, Depends(get_postmortem_service)
    ]
):
    """
    Retrieves the full details of a single post-mortem by its unique ID.
    """
    postmortem = await postmortem_service.get_postmortem_by_id(
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
    pm_update: PostMortemUpdate,
    pm_service: Annotated[PostmortemService, Depends(get_postmortem_service)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Updates the general details of a post-mortem, such as its status,
    links, RCA, and lessons learned.
    """
    updated_pm = await pm_service.update_postmortem(
        postmortem_id=postmortem_id,
        update_data=pm_update,
        current_user=current_user
    )
    return updated_pm


@pm_router.delete(
    "/{postmortem_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Post-mortem"
)
async def delete_postmortem(
    postmortem_id: UUID,
    pm_service: Annotated[PostmortemService, Depends(get_postmortem_service)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Deletes a post-mortem. Only the incident
    commander or a superuser can perform this action.
    """
    await pm_service.delete_postmortem(
        postmortem_id=postmortem_id,
        current_user=current_user
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
