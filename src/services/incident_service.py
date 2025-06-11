from uuid import UUID
from typing import List, Optional
from datetime import datetime, timezone
import logging

from sqlmodel.ext.asyncio.session import AsyncSession

from src.crud.user_crud import CRUDUser
from src.crud.incident_crud import CrudIncident
from src.models.user import User
from src.models.incident import (
    Incident,
    TimelineEvent,
    CommunicationLog,
    IncidentStatusEnum,
    SeverityLevelEnum,
)
from src.api.v1.schemas.incident_schemas import (
    IncidentCreate,
    IncidentProfileUpdate,
    ImpactsUpdate,
    ShallowRCAUpdate,
    TimelineEventCreate,
    CommunicationLogCreate,
    ResolutionMitigationCreate,
)
from src.api.v1.schemas.common_schemas import PaginatedResponse
from src.exceptions.common_exceptions import (
    InvalidOperationException,
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

logger = logging.getLogger(__name__)


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

    async def _check_permission(
        self,
        *,
        incident: Incident,
        user: User,
        allow_viewer: bool = False
    ):
        """
        A helper method to standardize permission checks.
        - Superusers can do anything.
        - Commanders can edit their own incidents.
        - Any authenticated user can view or add
        timeline/logs if `allow_viewer` is True.
        """

        is_commander = incident.profile.commander_id == user.id
        is_superuser = user.is_superuser

        if is_superuser or is_commander:
            return

        if allow_viewer:
            return

        raise InsufficientPermissionsException(
            "You do not have permission to perform this action."
        )

    async def get_incident_by_id(
            self,
            *,
            incident_id: UUID
    ) -> Incident:
        """
        Retrieves an incident by its ID.
        Raises an exception if the incident is not found.
        """

        incident = await self.crud_incident.get_incident_by_id(
            incident_id=incident_id
        )

        if not incident:
            raise IncidentNotFoundException(
                identifier=str(incident_id)
            )

        return incident

    async def get_incidents_list(
        self,
        *,
        statuses: Optional[
            List[IncidentStatusEnum]
        ] = None,
        severities: Optional[List[SeverityLevelEnum]] = None,
        commander_id: Optional[UUID] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> PaginatedResponse[Incident]:
        """
        Searches and retrieves a paginated list
        of incidents based on filter criteria.
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

        total_count = await self.crud_incident.count_incidents(
            statuses=statuses,
            severities=severities,
            commander_id=commander_id,
        )

        return PaginatedResponse(
            items=incidents,
            total=total_count,
            skip=skip,
            limit=limit
        )

    async def create_incident(
        self,
        *,
        incident_in: IncidentCreate,
        current_user: User
    ) -> Incident:

        logger.info(
            "Creating incident "
            f"'{incident_in.profile.title}' "
            " by user "
            f"'{current_user.username}'"
        )

        commander_id = incident_in.profile.commander_id

        if commander_id:
            commander = await self.crud_user.get_user_by_id(
                user_id=commander_id
            )

            if not commander or not commander.is_active:
                raise UserNotFoundException(
                    detail=(
                        "Commander with ID "
                        f"{commander_id} "
                        "not found or is inactive."
                    )
                )

        creation_event = TimelineEventCreate(
            time_utc=datetime.now(timezone.utc),
            event_description=(
                "Incident created by "
                f"{current_user.username}"
            ),
            owner_user_id=current_user.id,
        )
        incident_in.timeline_events.insert(
            0, creation_event
        )

        new_incident = await self.crud_incident.create_incident(
            incident_in=incident_in
        )

        # Commit the transaction at the end of the service method.
        await self.db_session.commit()
        await self.db_session.refresh(new_incident)

        logger.info(
            "Successfully created incident with ID: "
            f"{new_incident.id}"
        )

        return new_incident

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

        # Business logic for status transitions
        old_status = incident.profile.status
        if 'status' in update_dict and old_status != update_dict['status']:
            if old_status == IncidentStatusEnum.RESOLVED:
                raise InvalidStatusTransitionException(
                    from_status=old_status,
                    to_status=update_dict['status']
                )

        elif old_status == IncidentStatusEnum.RESOLVED and len(
            update_dict
        ) > 0:
            raise IncidentAlreadyResolvedException(
                "Cannot update profile details of a resolved incident."
            )

        return await self.crud_incident.update_incident_profile(
            db_incident=incident,
            update_data=update_dict
        )

    async def update_incident_impacts(
        self,
        *,
        incident_id: UUID,
        update_data: ImpactsUpdate,
        current_user: User
    ) -> Incident:

        incident = await self.get_incident_by_id(
            incident_id=incident_id
        )

        await self._check_permission(
            incident=incident,
            user=current_user
        )

        if incident.profile.status == IncidentStatusEnum.RESOLVED:
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
        incident = await self.get_incident_by_id(incident_id=incident_id)
        await self._check_permission(incident=incident, user=current_user)

        if incident.profile.status == IncidentStatusEnum.RESOLVED:
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

        incident = await self.get_incident_by_id(
            incident_id=incident_id
        )

        await self._check_permission(
            incident=incident,
            user=current_user,
            allow_viewer=True
        )

        if incident.profile.status == IncidentStatusEnum.RESOLVED:
            raise IncidentAlreadyResolvedException(
                "Cannot add timeline events to a resolved incident."
            )

        event_in.owner_user_id = current_user.id

        # Pass the incident_id from the path
        # to create a valid TimelineEvent model.
        new_event = TimelineEvent.model_validate(
            event_in,
            update={'incident_id': incident_id}
        )

        updated_incident = await self.crud_incident.add_timeline_event(
            incident=incident,
            new_event=new_event
        )

        await self.db_session.commit()

        return updated_incident

    async def add_communication_log(
        self,
        *,
        incident_id: UUID,
        log_in: CommunicationLogCreate,
        current_user: User
    ) -> Incident:

        incident = await self.get_incident_by_id(
            incident_id=incident_id
        )

        await self._check_permission(
            incident=incident,
            user=current_user,
            allow_viewer=True
        )

        if incident.profile.status == IncidentStatusEnum.RESOLVED:
            raise IncidentAlreadyResolvedException(
                "Cannot add communication logs to a resolved incident."
            )

        new_log = CommunicationLog.model_validate(
            log_in,
            update={'incident_id': incident_id}
        )

        updated_incident = await self.crud_incident.add_communication_log(
            incident=incident,
            new_log=new_log
        )

        return updated_incident

    async def update_resolution(
        self,
        *,
        incident_id: UUID,
        resolution_in: ResolutionMitigationCreate,
        current_user: User
    ) -> Incident:

        incident = await self.get_incident_by_id(
            incident_id=incident_id
        )

        await self._check_permission(
            incident=incident,
            user=current_user
        )

        if incident.profile.status == IncidentStatusEnum.RESOLVED \
                and not incident.resolution_mitigation:
            raise InvalidOperationException(
                "Cannot add resolution to an already "
                "resolved incident without one."
            )

        return await self.crud_incident.update_resolution(
            db_incident=incident,
            resolution_data=resolution_in
        )

    async def delete_incident(
            self,
            *,
            incident_id: UUID,
            current_user: User
    ) -> None:

        if not current_user.is_superuser:
            raise InsufficientPermissionsException(
                "Only an admin can delete an incident."
            )

        incident_to_delete = await self.get_incident_by_id(
            incident_id=incident_id
        )

        if incident_to_delete.profile.status != IncidentStatusEnum.RESOLVED:
            raise InvalidOperationException(
                "Cannot delete an incident that "
                "is not in 'Resolved' status. "
                f"Current status is "
                f"'{incident_to_delete.profile.status.value}'."
            )

        await self.crud_incident.delete_incident(
            incident=incident_to_delete
        )

        return
