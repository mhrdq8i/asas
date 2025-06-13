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
        incident = await self.crud_incident.get_incident_by_id(incident_id=incident_id)
        if not incident:
            raise IncidentNotFoundException(identifier=incident_id)
        return incident

    async def _get_postmortem_or_fail(self, postmortem_id: UUID) -> PostMortem:
        postmortem = await self.crud_postmortem.get_postmortem_by_id(postmortem_id=postmortem_id)
        if not postmortem:
            raise PostMortemNotFoundException(identifier=postmortem_id)
        return postmortem

    async def _check_permission(self, *, incident: Incident, user: User):
        is_commander = incident.profile.commander_id == user.id
        is_superuser = user.is_superuser
        if not (is_commander or is_superuser):
            raise InsufficientPermissionsException(
                "You do not have permission to manage this post-mortem.")

    async def create_postmortem_for_incident(self, *, incident_id: UUID, current_user: User) -> PostMortem:
        incident = await self._get_incident_or_fail(incident_id)

        # Permission Check
        await self._check_permission(incident=incident, user=current_user)

        # Business Rule: Check if incident is resolved
        if incident.profile.status != IncidentStatusEnum.RESOLVED:
            raise IncidentNotResolvedException(incident_id=incident_id)

        # Business Rule: Check if post-mortem already exists
        existing_postmortem = await self.crud_postmortem.get_postmortem_by_incident_id(incident_id=incident_id)
        if existing_postmortem:
            raise PostMortemAlreadyExistsException(incident_id=incident_id)

        # Create a new draft post-mortem
        new_postmortem = PostMortem(
            incident_id=incident_id, status=PostMortemStatusEnum.DRAFT)

        db_postmortem = await self.crud_postmortem.create_postmortem(postmortem=new_postmortem)
        await self.db_session.commit()
        await self.db_session.refresh(db_postmortem)

        return db_postmortem

    async def get_postmortem_by_id(self, *, postmortem_id: UUID) -> PostMortem:
        # No permission check on read, assuming post-mortems are public within the org
        return await self._get_postmortem_or_fail(postmortem_id)

    async def update_postmortem(self, *, postmortem_id: UUID, update_data: PostMortemUpdate, current_user: User) -> PostMortem:
        db_postmortem = await self._get_postmortem_or_fail(postmortem_id)

        # Fetch related incident for permission check
        incident = await self._get_incident_or_fail(db_postmortem.incident_id)
        await self._check_permission(incident=incident, user=current_user)

        update_dict = update_data.model_dump(exclude_unset=True)

        # If status is changing to "Completed", set the completion date
        if update_dict.get("status") == PostMortemStatusEnum.COMPLETED and db_postmortem.status != PostMortemStatusEnum.COMPLETED:
            update_dict["date_completed_utc"] = datetime.now(timezone.utc)

        updated_pm = await self.crud_postmortem.update_postmortem(
            db_postmortem=db_postmortem,
            update_data=update_dict
        )
        await self.db_session.commit()
        return updated_pm
