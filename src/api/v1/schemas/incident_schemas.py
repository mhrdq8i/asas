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
    RolesEnum,
    AffectedItemEnum
)
from src.api.v1.schemas.user_schemas import (
    UserRead
)


# --- CREATE Schemas (Request) ---

class IncidentProfileCreate(BaseModel):
    title: str = PydanticField(max_length=255)
    severity: SeverityLevelEnum
    datetime_detected_utc: datetime
    detected_by: str
    commander_id: UUID
    summary: str
    status: IncidentStatusEnum = IncidentStatusEnum.OPEN


class ImpactsCreate(BaseModel):
    customer_impact: str
    business_impact: str


class ShallowRCACreate(BaseModel):
    what_happened: str
    why_it_happened: str
    technical_causes: str
    detection_mechanisms: str


class AffectedItemCreate(BaseModel):
    item_type: AffectedItemEnum
    description: Optional[str] = None


class TimelineEventCreate(BaseModel):
    time_utc: datetime
    owner_user_id: Optional[UUID] = None
    event_description: str


class CommunicationLogCreate(BaseModel):
    time_utc: datetime
    message: str
    channel: str = PydanticField(
        max_length=100
    )


class IncidentCreate(BaseModel):
    profile: IncidentProfileCreate
    impacts: ImpactsCreate
    shallow_rca: ShallowRCACreate
    affected_items: List[AffectedItemCreate] = []
    timeline_events: List[TimelineEventCreate] = []
    communication_logs: List[CommunicationLogCreate] = []


# --- Update Schemas (Request) ---

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
    what_happened: Optional[str] = None
    why_it_happened: Optional[str] = None
    technical_causes: Optional[str] = None
    detection_mechanisms: Optional[str] = None


class ResolutionMitigationCreate(BaseModel):
    resolution_time_utc: Optional[datetime] = None
    short_term_remediation_steps: List[str] = []
    long_term_preventative_measures: List[str] = []


# --- Read Schemas  (Response) ---

class IncidentProfileRead(IncidentProfileCreate):
    id: UUID
    commander: Optional[UserRead] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AffectedItemRead(AffectedItemCreate):
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
    owner_user: Optional[UserRead] = None

    class Config:
        from_attributes = True


class CommunicationLogRead(CommunicationLogCreate):
    id: UUID

    class Config:
        from_attributes = True


class ResolutionMitigationRead(ResolutionMitigationCreate):
    id: UUID

    class Config:
        from_attributes = True


class SignOffRead(BaseModel):
    id: UUID
    role: RolesEnum
    date_approved: date
    approver_user: UserRead

    class Config:
        from_attributes = True


class IncidentRead(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    profile: IncidentProfileRead
    impacts: ImpactsRead
    shallow_rca: ShallowRCARead
    resolution_mitigation: Optional[
        ResolutionMitigationRead
    ] = None
    affected_items: List[AffectedItemRead] = []
    timeline_events: List[TimelineEventRead] = []
    communication_logs: List[CommunicationLogRead] = []
    postmortem: Optional[Any] = None
    sign_offs: List[SignOffRead] = []

    class Config:
        from_attributes = True
