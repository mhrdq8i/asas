from uuid import UUID
from typing import List, Optional
from datetime import datetime, timezone

from sqlmodel.ext.asyncio.session import AsyncSession

from src.crud.crud_user import CRUDUser
from src.crud.crud_incident import CrudIncident
from src.models.user import User
from src.models.incident import (
    Incident,
    TimelineEvent,
    CommunicationLog,
    IncidentStatusEnum,
    SeverityLevelEnum
)
from src.api.v1.schemas.incident_schemas import (
    IncidentCreate,
    IncidentProfileUpdate,
    ImpactsUpdate,
    ShallowRCAUpdate,
    TimelineEventCreate,
    CommunicationLogCreate,
)
from src.exceptions.incident_exceptions import (
    IncidentNotFoundException,
    IncidentAlreadyResolvedException,
    InvalidStatusTransitionException,
)
from src.exceptions.user_exceptions import (
    InsufficientPermissionsException,
    UserNotFoundException,
)


class IncidentService:
    """
    The "brain" for all business logic related to incidents.
    It uses the CRUD layer to interact with the
    database and enforces business rules.
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.crud_user = CRUDUser(self.db_session)
        self.crud_incident = CrudIncident(self.db_session)

    async def get_incident_by_id(self, *, incident_id: UUID) -> Incident:
        """
        Retrieves an incident by its ID.
        Raises an exception if the incident is not found.
        """
        incident = await self.crud_incident.get_incident_by_id(
            incident_id=incident_id)
        if not incident:
            raise IncidentNotFoundException(identifier=str(incident_id))
        return incident

    async def get_incidents_list(
        self,
        *,
        statuses: Optional[List[IncidentStatusEnum]] = None,
        severities: Optional[List[SeverityLevelEnum]] = None,
        commander_id: Optional[UUID] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Incident]:
        """
        Searches and retrieves a list of incidents based on filter criteria.
        """
        incidents = await self.crud_incident.search_incidents(
            statuses=statuses,
            severities=severities,
            commander_id=commander_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit,
        )
        return incidents

    async def create_incident(
            self, *, incident_in: IncidentCreate, current_user: User
    ) -> Incident:
        """
        Creates a new incident.
        Business logic:
        1. Ensures the assigned commander exists and is active.
        2. Adds the initial timeline event to the
        creation schema itself to avoid lazy loading issues.
        """
        commander = await self.crud_user.get_user_by_id(
            user_id=incident_in.profile.commander_id)
        if not commander or not commander.is_active:
            raise UserNotFoundException(
                detail=(
                    "Commander with ID "
                    f"{incident_in.profile.commander_id} "
                    "not found or is inactive."
                )
            )

        # FIX: Create the initial timeline event
        # with the correct data type (a list).
        creation_event_data = TimelineEventCreate(
            time_utc=datetime.now(timezone.utc),
            event_description=[(
                "Incident created by "
                f"{current_user.username}"
            )],
            owner_user_id=current_user.id
        )

        # Add the event to the list of timeline
        # events in the main creation schema
        if incident_in.timeline_events is None:
            incident_in.timeline_events = []
        incident_in.timeline_events.append(
            creation_event_data
        )

        # Now, call the CRUD method with
        # the fully prepared data.
        new_incident = await self.crud_incident.create_incident(
            incident_in=incident_in
        )

        return new_incident

    async def _check_permission(
            self,
            *,
            incident: Incident,
            user: User,
            allow_viewer: bool = False
    ):
        """A helper method to standardize permission checks."""
        is_commander = incident.profile \
            and incident.profile.commander_id == user.id
        is_superuser = user.is_superuser

        # Permission granted
        if is_commander or is_superuser:
            return

        # For read-only operations
        if allow_viewer:
            return

        raise InsufficientPermissionsException(
            "You do not have permission to perform this action."
        )

    async def update_incident_profile(
        self,
        *,
        incident_id: UUID,
        update_data: IncidentProfileUpdate,
        current_user: User
    ) -> Incident:
        """
        Updates an incident's profile
        (status, severity, etc.).
        """
        incident = await self.get_incident_by_id(
            incident_id=incident_id
        )
        await self._check_permission(
            incident=incident,
            user=current_user
        )

        update_dict = update_data.model_dump(
            exclude_unset=True
        )

        if not incident.profile:
            return await self.crud_incident.update_incident_profile(
                db_incident=incident,
                update_data=update_dict
            )

        old_status = incident.profile.status
        new_status = update_dict.get('status')

        if old_status == IncidentStatusEnum.RESOLVED:
            if new_status and new_status != IncidentStatusEnum.RESOLVED:
                raise InvalidStatusTransitionException(
                    from_status=old_status,
                    to_status=new_status
                )
            elif len(
                update_dict
            ) > 1 or (
                    len(
                        update_dict
                    ) == 1 and 'status' not in update_dict
            ):
                raise IncidentAlreadyResolvedException(
                    "Cannot update profile details of a resolved incident."
                )

        return await self.crud_incident.update_incident_profile(
            db_incident=incident,
            update_data=update_dict
        )

    async def update_incident_impacts(
        self, *, incident_id: UUID,
        update_data: ImpactsUpdate,
        current_user: User
    ) -> Incident:
        """
        Updates the impacts section of an incident.
        """
        incident = await self.get_incident_by_id(
            incident_id=incident_id
        )
        await self._check_permission(
            incident=incident,
            user=current_user
        )

        if incident.profile and incident.profile.status \
                == IncidentStatusEnum.RESOLVED:
            raise IncidentAlreadyResolvedException(
                "Cannot update impacts of a resolved incident."
            )

        update_dict = update_data.model_dump(
            exclude_unset=True
        )

        return await self.crud_incident.update_incident_impacts(
            db_incident=incident,
            impacts_data=update_dict
        )

    async def update_shallow_rca(
        self,
        *,
        incident_id: UUID,
        update_data: ShallowRCAUpdate,
        current_user: User
    ) -> Incident:
        """
        Updates the shallow root cause analysis section of an incident.
        """
        incident = await self.get_incident_by_id(
            incident_id=incident_id
        )
        await self._check_permission(
            incident=incident,
            user=current_user
        )

        if incident.profile and incident.profile.status \
                == IncidentStatusEnum.RESOLVED:
            raise IncidentAlreadyResolvedException(
                "Cannot update RCA of a resolved incident."
            )

        update_dict = update_data.model_dump(
            exclude_unset=True
        )

        return await self.crud_incident.update_shallow_rca(
            db_incident=incident,
            rca_data=update_dict

        )

    async def add_timeline_event(
        self,
        *,
        incident_id: UUID,
        event_in: TimelineEventCreate,
        current_user: User
    ) -> Incident:
        """
        Adds a new event to the incident's timeline.
        """
        incident = await self.get_incident_by_id(
            incident_id=incident_id
        )
        await self._check_permission(
            incident=incident,
            user=current_user,
            allow_viewer=True
        )

        new_event = TimelineEvent.model_validate(
            event_in,
            update={
                'owner_user_id': current_user.id
            }
        )

        return await self.crud_incident.add_timeline_event(
            incident=incident,
            new_event=new_event
        )

    async def add_communication_log(
        self,
        *,
        incident_id: UUID,
        log_in: CommunicationLogCreate,
        current_user: User
    ) -> Incident:
        """
        Adds a new communication log to the incident.
        """
        incident = await self.get_incident_by_id(
            incident_id=incident_id
        )
        await self._check_permission(
            incident=incident,
            user=current_user,
            allow_viewer=True
        )

        new_log = CommunicationLog.model_validate(
            log_in
        )
        return await self.crud_incident.add_communication_log(
            incident=incident,
            new_log=new_log
        )

    async def delete_incident(
        self,
        *,
        incident_id: UUID,
        current_user: User
    ) -> None:
        """Deletes an incident."""
        if not current_user.is_superuser:
            raise InsufficientPermissionsException(
                "Only an admin can delete an incident."
            )

        incident_to_delete = await self.get_incident_by_id(
            incident_id=incident_id
        )
        await self.crud_incident.delete_incident(
            incident=incident_to_delete
        )
        return
