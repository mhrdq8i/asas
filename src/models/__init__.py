"""
This file imports all SQLModel table models and Base models,
ensuring they are registered with SQLModel's metadata.
It also runs model_rebuild() for models with forward references.
This __init__.py should be imported once when the application starts,
for example in src/database/session.py before creating tables.
"""

from src.models.base import (
    IncidentStatusEnum,
    SeverityLevelEnum,
    ActionItemStatusEnum,
    UserRoleEnum,
    PostMortemApproverRoleEnum,
    BaseEntity,
)
from src.models.user import User
from src.models.incident import (
    Incident,
    IncidentProfile,
    AffectedItemBase,
    AffectedService,
    AffectedRegion,
    Impacts,
    ShallowRCA,
    TimelineEvent,
    ResolutionMitigation,
    RemediationStep,
    LongTermPreventativeMeasure,
    CommunicationLog,
    SignOff
)
from src.models.postmortem import (
    PostMortem,
    PostMortemProfile,
    ContributingFactor,
    LessonLearned,
    ActionItem,
    PostMortemApproval
)


User.model_rebuild()
Incident.model_rebuild()
IncidentProfile.model_rebuild()
AffectedService.model_rebuild()
AffectedRegion.model_rebuild()
Impacts.model_rebuild()
ShallowRCA.model_rebuild()
TimelineEvent.model_rebuild()
ResolutionMitigation.model_rebuild()
RemediationStep.model_rebuild()
LongTermPreventativeMeasure.model_rebuild()
CommunicationLog.model_rebuild()
SignOff.model_rebuild()
PostMortem.model_rebuild()
PostMortemProfile.model_rebuild()
ContributingFactor.model_rebuild()
LessonLearned.model_rebuild()
ActionItem.model_rebuild()
PostMortemApproval.model_rebuild()


print(
    "[INFO] "
    "All models from 'src.models' "
    "package imported and forward "
    "references updated."
)

# Define __all__ to control
# `from src.models import *` behavior
__all__ = [
    # Bases and Enums
    "BaseEntity",
    "AffectedItemBase",
    "IncidentStatusEnum",
    "SeverityLevelEnum",
    "ActionItemStatusEnum",
    "UserRoleEnum",
    "PostMortemApproverRoleEnum",

    # User Models
    "User",

    # Incident Models
    "Incident",
    "IncidentProfile",
    "AffectedService",
    "AffectedRegion",
    "Impacts",
    "ShallowRCA",
    "TimelineEvent",
    "ResolutionMitigation",
    "RemediationStep",
    "LongTermPreventativeMeasure",
    "CommunicationLogEntry",
    "SignOff",

    # PostMortem Models
    "PostMortem",
    "PostMortemProfile",
    "ContributingFactor",
    "LessonLearned",
    "ActionItem",
    "PostMortemApproval",
]
