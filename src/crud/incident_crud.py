from uuid import UUID
from typing import (
    List,
    Optional,
    Dict,
    Any
)
from datetime import datetime

from sqlmodel import (
    select,
    func,
    and_
)
from sqlmodel.ext.asyncio.session import (
    AsyncSession
)
from sqlalchemy.orm import selectinload

from src.models.incident import (
    Incident,
    IncidentProfile,
    TimelineEvent,
    SignOff,
    Impacts,
    ShallowRCA,
    AffectedItem,
    CommunicationLog,
    IncidentStatusEnum,
    SeverityLevelEnum,
)
from src.api.v1.schemas.incident_schemas import (
    IncidentCreate
)


class CrudIncident:
    def __init__(self, db_session: AsyncSession):
        self.db: AsyncSession = db_session

    async def get_incident_by_id(
            self,
            *,
            incident_id: UUID
    ) -> Optional[Incident]:
        statement = (
            select(
                Incident
            ).where(
                Incident.id == incident_id
            ).options(
                selectinload(Incident.profile).selectinload(
                    IncidentProfile.commander
                ),
                selectinload(Incident.impacts),
                selectinload(Incident.shallow_rca),
                selectinload(Incident.postmortem),
                selectinload(Incident.resolution_mitigation),
                selectinload(Incident.affected_items),
                selectinload(Incident.communication_logs),
                selectinload(Incident.timeline_events).selectinload(
                    TimelineEvent.owner_user
                ),
                selectinload(Incident.sign_offs).selectinload(
                    SignOff.approver_user
                )
            )
        )
        result = await self.db.exec(statement)

        return result.unique().first()

    async def create_incident(
        self,
        *,
        incident_in: IncidentCreate
    ) -> Incident:

        db_incident = Incident()

        db_incident.profile = IncidentProfile(
            **incident_in.profile.model_dump()
        )
        db_incident.impacts = Impacts(
            **incident_in.impacts.model_dump()
        )
        db_incident.shallow_rca = ShallowRCA(
            **incident_in.shallow_rca.model_dump()
        )

        db_incident.affected_items = [
            AffectedItem(
                **item.model_dump()
            ) for item in incident_in.affected_items
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

        self.db.add(db_incident)
        await self.db.commit()
        await self.db.refresh(db_incident)

        return db_incident

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

        statement = select(Incident).join(
            IncidentProfile
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

        # Eager load necessary data for
        # the list view to avoid N+1 queries
        statement = statement.options(
            selectinload(
                Incident.profile
            ),
            selectinload(
                Incident.affected_items
            )
        ).order_by(
            Incident.created_at.desc()
        ).offset(skip).limit(limit)

        result = await self.db.exec(statement)

        return list(result.unique().all())

    async def update_incident_profile(
        self,
        *,
        db_incident: Incident,
        update_data: Dict[str, Any]
    ) -> Incident:

        for field, value in update_data.items():
            if hasattr(db_incident.profile, field):
                setattr(db_incident.profile, field, value)

        self.db.add(db_incident)
        await self.db.commit()
        await self.db.refresh(db_incident)

        return db_incident

    async def update_incident_impacts(
        self,
        *,
        db_incident: Incident,
        impacts_data: Dict[str, Any]
    ) -> Incident:

        for field, value in impacts_data.items():
            if hasattr(db_incident.impacts, field):
                setattr(db_incident.impacts, field, value)

        self.db.add(db_incident)
        await self.db.commit()
        await self.db.refresh(db_incident)

        return db_incident

    async def update_shallow_rca(
        self,
        *,
        db_incident: Incident,
        rca_data: Dict[str, Any]
    ) -> Incident:

        for field, value in rca_data.items():
            if hasattr(db_incident.shallow_rca, field):
                setattr(db_incident.shallow_rca, field, value)

        self.db.add(db_incident)
        await self.db.commit()
        await self.db.refresh(db_incident)

        return db_incident

    async def add_timeline_event(
        self,
        *,
        incident: Incident,
        new_event: TimelineEvent
    ) -> Incident:

        incident.timeline_events.append(new_event)

        self.db.add(incident)
        await self.db.commit()
        await self.db.refresh(incident)

        return incident

    async def add_communication_log(
        self,
        *,
        incident: Incident,
        new_log: CommunicationLog
    ) -> Incident:

        incident.communication_logs.append(new_log)

        self.db.add(incident)
        await self.db.commit()
        await self.db.refresh(incident)

        return incident

    async def delete_incident(
        self,
        *,
        incident: Incident
    ) -> None:

        await self.db.delete(incident)
        await self.db.commit()

    async def is_user_active_commander(
        self,
        *,
        user_id: UUID
    ) -> bool:

        statement = select(
            func.count(IncidentProfile.id)
        ).where(
            IncidentProfile.commander_id == user_id,
            IncidentProfile.status.in_(
                [
                    IncidentStatusEnum.OPEN,
                    IncidentStatusEnum.DOING
                ]
            )
        )

        result = await self.db.exec(statement)
        count = result.one()

        return count > 0
