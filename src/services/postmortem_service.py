from uuid import UUID
from datetime import datetime, timezone

from sqlmodel.ext.asyncio.session import AsyncSession

from src.crud.postmortem_crud import CrudPostmortem
from src.crud.incident_crud import CrudIncident
from src.models.user import User
from src.models.incident import Incident, IncidentStatusEnum
from src.models.postmortem import PostMortem, PostMortemStatusEnum
from src.api.v1.schemas.postmortem_schemas import PostMortemUpdate

from src.exceptions.postmortem_exceptions import (
    PostMortemNotFoundException,
    PostMortemAlreadyExistsException,
    IncidentNotResolvedException,
)
from src.exceptions.incident_exceptions import IncidentNotFoundException
from src.exceptions.user_exceptions import InsufficientPermissionsException


class PostmortemService:

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.crud_postmortem = CrudPostmortem(self.db_session)
        self.crud_incident = CrudIncident(self.db_session)

    async def _get_incident_or_fail(self, incident_id: UUID) -> Incident:
        """Helper to fetch an incident by ID or raise a standard not-found exception."""
        incident = await self.crud_incident.get_incident_by_id(incident_id=incident_id)
        if not incident:
            raise IncidentNotFoundException(identifier=incident_id)
        return incident

    async def _get_postmortem_or_fail(self, postmortem_id: UUID) -> PostMortem:
        """Helper to fetch a postmortem by ID or raise a standard not-found exception."""
        postmortem = await self.crud_postmortem.get_postmortem_by_id(postmortem_id=postmortem_id)
        if not postmortem:
            raise PostMortemNotFoundException(identifier=postmortem_id)
        return postmortem

    async def _check_permission(self, *, incident: Incident, user: User):
        """Centralized permission check for post-mortem management."""
        is_commander = incident.profile.commander_id == user.id
        is_superuser = user.is_superuser
        if not (is_commander or is_superuser):
            raise InsufficientPermissionsException(
                "You do not have permission to manage this post-mortem.")

    async def create_postmortem(self, *, incident_id: UUID, current_user: User) -> PostMortem:
        """
        Creates a new draft post-mortem for a given incident, enforcing business rules.
        """
        incident = await self._get_incident_or_fail(incident_id)

        # Permission Check: Only commander or superuser can create it.
        await self._check_permission(incident=incident, user=current_user)

        # Business Rule: Ensure the incident is resolved before creating a post-mortem.
        if incident.profile.status != IncidentStatusEnum.RESOLVED:
            raise IncidentNotResolvedException(incident_id=incident_id)

        # Business Rule: Ensure a post-mortem doesn't already exist for this incident.
        existing_postmortem = await self.crud_postmortem.get_postmortem_by_incident_id(incident_id=incident_id)
        if existing_postmortem:
            raise PostMortemAlreadyExistsException(incident_id=incident_id)

        # Create a new draft post-mortem instance.
        new_postmortem = PostMortem(
            incident_id=incident_id, status=PostMortemStatusEnum.DRAFT)

        db_postmortem = await self.crud_postmortem.create_postmortem(postmortem=new_postmortem)
        await self.db_session.commit()

        # Eagerly load relationships after commit to prevent MissingGreenlet error.
        refreshed_pm = await self.crud_postmortem.refresh_with_relationships(postmortem=db_postmortem)

        return refreshed_pm

    async def get_postmortem_by_id(self, *, postmortem_id: UUID) -> PostMortem:
        """
        Retrieves a single post-mortem by its ID.
        Note: Assumes read access is public within the organization.
        """
        return await self._get_postmortem_or_fail(postmortem_id)

    async def update_postmortem(self, *, postmortem_id: UUID, update_data: PostMortemUpdate, current_user: User) -> PostMortem:
        """
        Updates the main properties of a post-mortem.
        """
        db_postmortem = await self._get_postmortem_or_fail(postmortem_id)

        # Fetch related incident for permission checking.
        incident = await self._get_incident_or_fail(db_postmortem.incident_id)
        await self._check_permission(incident=incident, user=current_user)

        update_dict = update_data.model_dump(exclude_unset=True)

        # Business Rule: If status changes to "Completed", set the completion date.
        if update_dict.get("status") == PostMortemStatusEnum.COMPLETED and db_postmortem.status != PostMortemStatusEnum.COMPLETED:
            update_dict["date_completed_utc"] = datetime.now(timezone.utc)

        updated_pm = await self.crud_postmortem.update_postmortem(
            db_postmortem=db_postmortem,
            update_data=update_dict
        )
        await self.db_session.commit()

        # Eagerly load relationships after the update as well.
        refreshed_pm = await self.crud_postmortem.refresh_with_relationships(postmortem=updated_pm)

        return refreshed_pm

    async def delete_postmortem(self, *, postmortem_id: UUID, current_user: User) -> None:
        """Deletes a post-mortem after checking permissions."""
        db_postmortem = await self._get_postmortem_or_fail(postmortem_id)

        # We need the associated incident to check permissions
        incident = await self._get_incident_or_fail(db_postmortem.incident_id)
        await self._check_permission(incident=incident, user=current_user)

        await self.crud_postmortem.delete_postmortem(db_postmortem=db_postmortem)
        await self.db_session.commit()
