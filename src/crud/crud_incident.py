from uuid import UUID
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlmodel import select, func, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.incident import (
    Incident,
    IncidentProfile,
    TimelineEvent,
    SignOff,
    Impacts,
    ShallowRCA,
    AffectedService,
    AffectedRegion,
    CommunicationLog,
    IncidentStatusEnum,
    SeverityLevelEnum,
)
from src.api.v1.schemas.incident_schemas import (
    IncidentCreate,
)


class CrudIncident:
    """
    CRUD operations for Incident
    and its related models.
    An instance of this class should be
    initialized with an AsyncSession.
    """

    def __init__(
            self,
            db_session: AsyncSession
    ):
        """
        Initializes the CrudIncident with an active database session.
        """
        self.db: AsyncSession = db_session

    async def get_incident_by_id(
            self,
            *,
            incident_id: UUID
    ) -> Optional[Incident]:
        """
        Retrieve a single incident by its ID with all its related data preloaded.
        FIX: Removed the explicit join to rely solely on the options, which is a more
        robust pattern for complex eager loading.
        """
        statement = (
            select(Incident)
            .where(Incident.id == incident_id)
            .options(
                # Eager load all relationships needed for
                # serialization or other operations
                selectinload(Incident.profile).selectinload(
                    IncidentProfile.commander),
                selectinload(Incident.impacts),
                selectinload(Incident.shallow_rca),
                selectinload(Incident.postmortem),
                selectinload(Incident.resolution_mitigation),
                selectinload(Incident.affected_services),
                selectinload(Incident.affected_regions),
                selectinload(Incident.timeline_events).selectinload(
                    TimelineEvent.owner_user),
                selectinload(Incident.communication_logs),
                selectinload(Incident.sign_offs).selectinload(
                    SignOff.approver_user)
            )
        )
        result = await self.db.exec(statement)
        # Use .unique() to handle potential
        # duplicate rows from one-to-many loads
        return result.unique().first()

    async def get_incidents(
        self,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Incident]:
        """
        Retrieve a list of incidents with pagination.
        This version only eager-loads the profile for
        basic info like title and status,
        making it efficient for list views.
        """
        statement = (
            select(Incident).options(
                selectinload(
                    Incident.profile
                )
            ).order_by(
                Incident.created_at.desc()
            ).offset(
                offset=skip
            ).limit(
                limit=limit
            )
        )
        result = await self.db.exec(
            statement
        )
        return list(result.all())

    async def create_incident(
        self,
        *,
        incident_in: IncidentCreate
    ) -> Incident:
        """
        Create a new incident along with all its
        related components in a single transaction.
        This method explicitly creates child model
        instances before assigning them
        to the parent Incident's relationships.
        This is the correct and robust pattern.
        """
        # Create an empty parent Incident object.
        # We will attach children to it.
        db_incident = Incident()

        # Create child model instances from the input schemas
        db_incident.profile = IncidentProfile(
            **incident_in.profile.model_dump()
        )

        # Handle one-to-one relationships that might be in a list
        if incident_in.impacts:
            db_incident.impacts = Impacts(
                **incident_in.impacts[0].model_dump()
            )
        if incident_in.shallow_rca:
            db_incident.shallow_rca = ShallowRCA(
                **incident_in.shallow_rca[0].model_dump()
            )

        # Handle one-to-many relationships
        # by creating a list of model instances
        db_incident.affected_services = [
            AffectedService(
                **s.model_dump()
            ) for s in incident_in.affected_services
        ]
        db_incident.affected_regions = [
            AffectedRegion(
                **r.model_dump()
            ) for r in incident_in.affected_regions
        ]
        db_incident.timeline_events = [
            TimelineEvent(
                **t.model_dump()
            ) for t in incident_in.timeline_events
        ]
        db_incident.communication_logs = [
            CommunicationLog(
                **c.model_dump()
            ) for c in incident_in.communication_logs
        ]

        # Add the fully constructed parent object to the session.
        # SQLAlchemy's relationship magic
        # will handle setting the foreign keys.
        self.db.add(db_incident)
        await self.db.commit()
        await self.db.refresh(db_incident)

        return db_incident

    async def update_incident_profile(
        self,
        *,
        db_incident: Incident,
        update_data: Dict[str, Any]
    ) -> Incident:
        """
        Updates the fields of the
        related IncidentProfile object.
        """
        if db_incident.profile:
            for (
                field, value
            ) in update_data.items():
                if hasattr(
                    db_incident.profile,
                    field
                ):
                    setattr(
                        db_incident.profile,
                        field,
                        value
                    )

            self.db.add(db_incident.profile)
            await self.db.commit()
            await self.db.refresh(
                db_incident.profile
            )
        return db_incident

    async def update_incident_impacts(
        self,
        *,
        db_incident: Incident,
        impacts_data: Dict[str, Any]
    ) -> Incident:
        """
        Updates the fields of the
        related Impacts object.
        """
        if db_incident.impacts:
            for (
                field, value
            ) in impacts_data.items():
                if hasattr(
                    db_incident.impacts,
                    field
                ):
                    setattr(
                        db_incident.impacts,
                        field,
                        value
                    )

            self.db.add(
                db_incident.impacts
            )
            await self.db.commit()
            await self.db.refresh(
                db_incident.impacts
            )
        return db_incident

    async def update_shallow_rca(
        self,
        *,
        db_incident: Incident,
        rca_data: Dict[str, Any]
    ) -> Incident:
        """
        Updates the fields of the
        related ShallowRCA object.
        """
        if db_incident.shallow_rca:
            for (
                field, value
            ) in rca_data.items():
                if hasattr(
                    db_incident.shallow_rca,
                    field
                ):
                    setattr(
                        db_incident.shallow_rca,
                        field,
                        value
                    )

            self.db.add(
                db_incident.shallow_rca
            )
            await self.db.commit()
            await self.db.refresh(
                db_incident.shallow_rca
            )
        return db_incident

    async def add_timeline_event(
        self,
        *,
        incident: Incident,
        new_event: TimelineEvent
    ) -> Incident:
        """
        Adds a new timeline event
        to an existing incident.
        """
        incident.timeline_events.append(
            new_event
        )
        self.db.add(incident)
        await self.db.commit()
        await self.db.refresh(
            incident
        )
        return incident

    async def add_communication_log(
        self,
        *,
        incident: Incident,
        new_log: CommunicationLog
    ) -> Incident:
        """
        Adds a new communication log
        to an existing incident.
        """
        incident.communication_logs.append(
            new_log
        )
        self.db.add(incident)
        await self.db.commit()
        await self.db.refresh(
            incident
        )
        return incident

    async def search_incidents(
        self,
        *,
        statuses: Optional[
            List[IncidentStatusEnum]
        ] = None,
        severities: Optional[
            List[SeverityLevelEnum]
        ] = None,
        commander_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Incident]:
        """
        Searches for incidents based on
        various filter criteria with pagination.
        Eagerly loads ALL required relationships
        to prevent lazy loading during
        response serialization.
        """
        statement = (
            select(
                Incident
            ).join(
                IncidentProfile,
                # Use isouter=True if
                # profile might not exist
                isouter=True
            ).options(
                selectinload(
                    Incident.profile
                ).selectinload(
                    IncidentProfile.commander
                ),
                selectinload(
                    Incident.impacts
                ),
                selectinload(
                    Incident.shallow_rca
                ),
                selectinload(
                    Incident.postmortem
                ),
                selectinload(
                    Incident.resolution_mitigation
                ),
                selectinload(
                    Incident.affected_services
                ),
                selectinload(
                    Incident.affected_regions
                ),
                selectinload(
                    Incident.timeline_events
                ).selectinload(
                    TimelineEvent.owner_user
                ),
                selectinload(Incident.communication_logs),
                selectinload(
                    Incident.sign_offs
                ).selectinload(
                    SignOff.approver_user
                )
            )
        )

        conditions = []
        if statuses:
            conditions.append(
                IncidentProfile.status.in_(statuses)
            )
        if severities:
            conditions.append(
                IncidentProfile.severity.in_(severities)
            )
        if commander_id:
            conditions.append(
                IncidentProfile.commander_id == commander_id
            )
        if start_date:
            conditions.append(
                IncidentProfile.datetime_detected_utc >= start_date
            )
        if end_date:
            conditions.append(
                IncidentProfile.datetime_detected_utc <= end_date
            )

        if conditions:
            statement = statement.where(
                and_(*conditions)
            )

        statement = statement.order_by(
            Incident.created_at.desc()
        ).offset(skip).limit(limit)

        result = await self.db.exec(statement)

        return list(result.all())

    async def delete_incident(
            self,
            *,
            incident: Incident
    ) -> None:
        """
        Deletes an incident from the database.
        Thanks to `cascade="all, delete-orphan"`,
        all related data will be removed as well.
        """
        await self.db.delete(
            incident
        )
        await self.db.commit()

    async def is_user_active_commander(
            self,
            *,
            user_id: UUID
    ) -> bool:
        """
        Checks if a given user is the commander
        of any currently "Open" or "Doing" incident.
        This is crucial for preventing the deletion
        of users who are managing active incidents.
        """
        statement = (
            select(
                func.count(IncidentProfile.id)
            ).where(
                IncidentProfile.commander_id == user_id
            ).where(
                IncidentProfile.status.in_(
                    [
                        IncidentStatusEnum.OPEN,
                        IncidentStatusEnum.DOING
                    ]
                )
            )
        )
        result = await self.db.exec(
            statement
        )
        count = result.one()

        return count > 0
