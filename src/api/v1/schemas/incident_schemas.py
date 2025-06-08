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
# Using UserRead to display
# user info inside other schemas
from src.api.v1.schemas.user_schemas import (
    UserRead
)
from src.models.base import (
    RolesEnum
)


# --- Schemas for Incident Components (Input for Creation) ---

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

    what_happened: List[
        str
    ] = []

    why_it_happened: List[
        str
    ] = []

    technical_causes: List[
        str
    ] = []

    detection_mechanisms: List[
        str
    ] = []


class TimelineEventCreate(BaseModel):

    time_utc: datetime
    owner_user_id: UUID
    event_description: List[
        str
    ] = []


class CommunicationLogCreate(BaseModel):

    time_utc: datetime
    channel: str = PydanticField(
        max_length=100
    )
    message: List[
        str
    ] = []


# --- Main Schema for Creating a Full Incident ---

class IncidentCreate(BaseModel):
    """
    Schema to create a full incident
    with all its initial components.
    This schema is the main input
    for the incident creation endpoint.
    """
    profile: IncidentProfileCreate

    impacts: List[
        ImpactsCreate
    ]

    shallow_rca: List[
        ShallowRCACreate
    ]

    affected_services: List[
        AffectedServiceCreate
    ] = []

    affected_regions: List[
        AffectedRegionCreate
    ] = []

    timeline_events: List[
        TimelineEventCreate
    ] = []

    communication_logs: List[
        CommunicationLogCreate
    ] = []


# --- Schemas for Reading Incident Data (API Response) ---

# We need read schemas for each component
# to include fields like id, created_at, etc.,
# and to use `from_attributes` for ORM models.
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


class TimelineEventRead(BaseModel):

    id: UUID
    time_utc: datetime

    event_description: List[
        str
    ] = []

    # Nested user info
    owner_user: UserRead

    class Config:
        from_attributes = True


class CommunicationLogRead(
    CommunicationLogCreate
):

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

    # Nested user info
    approver_user: UserRead

    class Config:
        from_attributes = True


# --- Main Schema for Reading a Full Incident ---

class IncidentRead(BaseModel):
    """
    Schema to represent a full
    incident with all its
    components for API responses.
    """
    id: UUID

    created_at: datetime
    updated_at: datetime

    profile: IncidentProfileRead

    impacts: ImpactsRead

    shallow_rca: ShallowRCARead

    resolution_mitigation: (
        ResolutionMitigationRead
    )

    # Placeholder for a future
    # PostMortemRead schema
    postmortem: Optional[Any] = None

    affected_services: List[
        AffectedServiceRead
    ] = []

    affected_regions: List[
        AffectedRegionRead
    ] = []

    timeline_events: List[
        TimelineEventRead
    ] = []

    communication_logs: List[
        CommunicationLogRead
    ] = []

    sign_offs: List[
        SignOffRead
    ] = []

    class Config:
        from_attributes = True


class IncidentProfileUpdate(BaseModel):
    """
    Schema for updating an incident's profile.
    All fields are optional.
    """
    title: Optional[
        str
    ] = PydanticField(
        default=None,
        max_length=255
    )
    severity: Optional[
        SeverityLevelEnum
    ] = None
    commander_id: Optional[
        UUID
    ] = None
    status: Optional[
        IncidentStatusEnum
    ] = None
    summary: Optional[
        str
    ] = None


class ImpactsUpdate(BaseModel):
    """
    Schema for updating an incident's impacts.
    All fields are optional.
    """
    customer_impact: Optional[
        str
    ] = None
    business_impact: Optional[
        str
    ] = None


class ShallowRCAUpdate(BaseModel):
    """
    Schema for updating an incident's shallow RCA.
    All fields are optional.
    """
    what_happened: Optional[
        List[str]
    ] = None
    why_it_happened: Optional[
        List[str]
    ] = None
    technical_causes: Optional[
        List[str]
    ] = None
    detection_mechanisms: Optional[
        List[str]
    ] = None
