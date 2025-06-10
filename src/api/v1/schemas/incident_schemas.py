from uuid import UUID
from datetime import (
    date,
    datetime
)
from typing import (
    List,
    Optional,
    Any
)

from pydantic import (
    BaseModel,
    Field as PydanticField
)

from src.models.base import (
    SeverityLevelEnum,
    IncidentStatusEnum,
)
from src.api.v1.schemas.user_schemas import (
    UserRead
)
from src.models.base import (
    RolesEnum
)


# Schemas for Incident Components
class IncidentProfileCreate(BaseModel):
    title: str = PydanticField(
        max_length=255
    )
    severity: SeverityLevelEnum
    datetime_detected_utc: datetime
    detected_by: str
    commander_id: UUID
    status: IncidentStatusEnum = (
        IncidentStatusEnum.OPEN
    )
    summary: str


class AffectedServiceCreate(BaseModel):
    name: str = PydanticField(
        max_length=255
    )


class AffectedRegionCreate(BaseModel):
    name: str = PydanticField(
        max_length=255
    )


class ImpactsCreate(BaseModel):
    customer_impact: str
    business_impact: str


class ShallowRCACreate(BaseModel):
    what_happened: List[str] = []
    why_it_happened: List[str] = []
    technical_causes: List[str] = []
    detection_mechanisms: List[str] = []


class TimelineEventCreate(BaseModel):
    time_utc: datetime
    owner_user_id: UUID
    event_description: List[str] = []


class CommunicationLogCreate(BaseModel):
    time_utc: datetime
    message: List[str] = []
    channel: str = PydanticField(
        max_length=100
    )


# Main Schema for Creating a Full Incident
class IncidentCreate(BaseModel):
    profile: IncidentProfileCreate
    impacts: List[ImpactsCreate]
    shallow_rca: List[ShallowRCACreate]
    affected_services: List[AffectedServiceCreate] = []
    affected_regions: List[AffectedRegionCreate] = []
    timeline_events: List[TimelineEventCreate] = []
    communication_logs: List[CommunicationLogCreate] = []


# Schemas for Updating Incident Components
class IncidentProfileUpdate(BaseModel):
    title: Optional[str] = PydanticField(
        default=None,
        max_length=255
    )
    severity: Optional[SeverityLevelEnum] = None
    commander_id: Optional[UUID] = None
    status: Optional[IncidentStatusEnum] = None
    summary: Optional[str] = None


class ImpactsUpdate(BaseModel):
    customer_impact: Optional[str] = None
    business_impact: Optional[str] = None


class ShallowRCAUpdate(BaseModel):
    what_happened: Optional[List[str]] = None
    why_it_happened: Optional[List[str]] = None
    technical_causes: Optional[List[str]] = None
    detection_mechanisms: Optional[List[str]] = None


# Schemas for Reading Incident Data (API Response)
class IncidentProfileRead(IncidentProfileCreate):
    id: UUID
    commander: UserRead
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AffectedServiceRead(AffectedServiceCreate):
    id: UUID

    class Config:
        from_attributes = True


class AffectedRegionRead(AffectedRegionCreate):
    id: UUID

    class Config:
        from_attributes = True


class ImpactsRead(ImpactsCreate):
    id: UUID

    class Config:
        from_attributes = True


class ShallowRCARead(ShallowRCACreate):
    id: UUID

    class Config:
        from_attributes = True


class TimelineEventRead(TimelineEventCreate):
    id: UUID
    owner_user: UserRead

    class Config:
        from_attributes = True


class CommunicationLogRead(CommunicationLogCreate):
    id: UUID

    class Config:
        from_attributes = True


class ResolutionMitigationRead(BaseModel):
    id: UUID
    resolution_time_utc: datetime | None = None

    class Config:
        from_attributes = True


class SignOffRead(BaseModel):
    id: UUID
    role: RolesEnum
    date_approved: date
    approver_user: UserRead

    class Config:
        from_attributes = True


# Main Schema for Reading a Full Incident
class IncidentRead(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    profile: IncidentProfileRead
    impacts: ImpactsRead
    shallow_rca: ShallowRCARead
    resolution_mitigation: Optional[ResolutionMitigationRead] = None
    postmortem: Optional[Any] = None
    affected_services: List[AffectedServiceRead] = []
    affected_regions: List[AffectedRegionRead] = []
    timeline_events: List[TimelineEventRead] = []
    communication_logs: List[CommunicationLogRead] = []
    sign_offs: List[SignOffRead] = []

    class Config:
        from_attributes = True
