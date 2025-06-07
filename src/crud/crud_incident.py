from uuid import UUID
from typing import List, Optional

from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.incident import (
    Incident,
    IncidentProfile,
    ResolutionMitigation,
    TimelineEvent,
    SignOff,
    Impacts,
    ShallowRCA,
    AffectedService,
    AffectedRegion,
    CommunicationLog,
    IncidentStatusEnum,
)
from src.api.v1.schemas.incident_schemas import (
    IncidentCreate
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
        Initializes the CrudIncident
        with an active database session.
        """
        self.db: AsyncSession = db_session

    async def get_incident_by_id(
        self,
        *,
        incident_id: UUID
    ) -> Optional[Incident]:
        """
        Retrieve a single incident by its ID
        with all its related data preloaded.
        This is optimized for a
        detailed view of a single incident.
        """
        statement = (
            select(Incident)
            .where(
                Incident.id == incident_id
            )
            .options(
                selectinload(
                    Incident.profile
                ).selectinload(
                    IncidentProfile.commander
                ),
                # Preload one-to-one relationships
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
                selectinload(
                    Incident.communication_logs
                ),
                selectinload(
                    Incident.sign_offs
                ).selectinload(
                    SignOff.approver_user
                ),
                # Preload one-to-one relationship
                # and its nested lists
                selectinload(
                    Incident.resolution_mitigation
                ).options(
                    selectinload(
                        ResolutionMitigation.short_term_remediation_steps
                    ),
                    selectinload(
                        ResolutionMitigation.long_term_preventative_measures
                    )
                ),
            )
        )
        result = await self.db.exec(
            statement
        )
        return result.first()

    async def get_incidents(
        self,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Incident]:
        """
        Retrieve a list of incidents with pagination.
        This version only eager-loads the profile
        for basic info like title and status,
        making it efficient for list views.
        """
        statement = (
            select(Incident)
            .options(
                selectinload(
                    Incident.profile
                )
            )
            .order_by(
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
        return list(
            result.all()
        )

    async def create_with_details(
        self,
        *,
        incident_in: IncidentCreate
    ) -> Incident:
        """
        Create a new incident along with all
        its related components in a single transaction.
        Handles both one-to-one and one-to-many
        relationships from the input schema.
        """
        # --- Handle One-to-One relationships ---

        # Profile is mandatory and is an object
        profile_data = IncidentProfile.model_validate(
            incident_in.profile
        )

        # Impacts and ShallowRCA might be passed
        # as a list with one element
        impacts_data = None
        if incident_in.impacts:
            impact_input = incident_in.impacts[
                0
            ] if isinstance(
                incident_in.impacts,
                list
            ) else incident_in.impacts
            impacts_data = Impacts.model_validate(
                impact_input
            )

        shallow_rca_data = None
        if incident_in.shallow_rca:
            rca_input = incident_in.shallow_rca[
                0
            ] if isinstance(
                incident_in.shallow_rca,
                list
            ) else incident_in.shallow_rca
            shallow_rca_data = ShallowRCA.model_validate(
                rca_input
            )

        # --- Handle One-to-Many relationships ---

        affected_services_data = [
            AffectedService.model_validate(
                s
            ) for s in incident_in.affected_services
        ]

        affected_regions_data = [
            AffectedRegion.model_validate(
                r
            ) for r in incident_in.affected_regions
        ]

        timeline_events_data = [
            TimelineEvent.model_validate(
                t
            ) for t in incident_in.timeline_events
        ]

        communication_logs_data = [
            CommunicationLog.model_validate(
                c
            ) for c in incident_in.communication_logs
        ]

        # Create the main Incident object
        # and link all child objects to it.
        db_incident = Incident(
            profile=profile_data,
            impacts=impacts_data,
            shallow_rca=shallow_rca_data,
            affected_services=affected_services_data,
            affected_regions=affected_regions_data,
            timeline_events=timeline_events_data,
            communication_logs=communication_logs_data
        )

        # Add the main incident object.
        # `cascade="all, delete-orphan"`
        # handles child objects.
        self.db.add(
            db_incident
        )
        await self.db.commit()
        await self.db.refresh(
            db_incident
        )

        return db_incident

    async def update_incident(
        self,
        *,
        db_incident: Incident,
        update_data: dict
    ) -> Incident:
        """
        A generic method to update an incident's fields.
        """
        for field, value in update_data.items():
            if hasattr(
                db_incident,
                field
            ):
                setattr(
                    db_incident,
                    field,
                    value
                )

        self.db.add(
            db_incident
        )
        await self.db.commit()
        await self.db.refresh(
            db_incident
        )

        return db_incident


async def update_incident_profile(
        self,
        *,
        db_incident: Incident,
        update_data: dict
    ) -> Incident:
        """
        A generic method to update an incident's profile fields.
        """
        if db_incident.profile:
            for field, value in update_data.items():
                if hasattr(db_incident.profile, field):
                    setattr(db_incident.profile, field, value)

            self.db.add(db_incident)
            await self.db.commit()
            await self.db.refresh(db_incident)
        return db_incident

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
            )
            .where(
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
