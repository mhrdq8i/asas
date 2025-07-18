"""
This file imports all SQLModel table models and Base models,
ensuring they are registered with SQLModel's metadata.
It also runs model_rebuild() for models with forward references.
This __init__.py should be imported once when the application starts,
for example in src/database/session.py before creating tables.
"""

# Import all Enums from the dedicated file
from src.models.enums import (
    UserRoleEnum,
    RolesEnum,
    IncidentStatusEnum,
    SeverityLevelEnum,
    ActionItemStatusEnum,
    AffectedItemEnum,
    FactorTypeEnum,
    PostMortemStatusEnum
)
# Import BaseEntity from its own file
from src.models.base import BaseEntity

# Import table models
from src.models.user import User
from src.models.incident import (
    Incident,
    IncidentProfile,
    AffectedItem,
    Impacts,
    ShallowRCA,
    TimelineEvent,
    ResolutionMitigation,
    CommunicationLog,
    SignOff
)
from src.models.postmortem import (
    PostMortem,
    ContributingFactor,
    ActionItem,
    PostMortemApproval,
)


# Rebuild models with forward references
User.model_rebuild()
Incident.model_rebuild()
IncidentProfile.model_rebuild()
AffectedItem.model_rebuild()
Impacts.model_rebuild()
ShallowRCA.model_rebuild()
TimelineEvent.model_rebuild()
ResolutionMitigation.model_rebuild()
CommunicationLog.model_rebuild()
SignOff.model_rebuild()
PostMortem.model_rebuild()
ContributingFactor.model_rebuild()
ActionItem.model_rebuild()
PostMortemApproval.model_rebuild()


print(
    "[INFO] "
    "All models from 'src.models' "
    "package imported and forward "
    "references updated."
)

# Define __all__ to control `from
# src.models import *` behavior
__all__ = [

    #  Enums
    "UserRoleEnum",
    "RolesEnum",
    "IncidentStatusEnum",
    "SeverityLevelEnum",
    "ActionItemStatusEnum",
    "AffectedItemEnum",
    "FactorTypeEnum",
    "PostMortemStatusEnum",

    # Bases
    "BaseEntity",

    # User Models
    "User",

    # Incident Models
    "Incident",
    "IncidentProfile",
    "AffectedItem",
    "Impacts",
    "ShallowRCA",
    "TimelineEvent",
    "ResolutionMitigation",
    "CommunicationLog",
    "SignOff",

    # PostMortem Models
    "PostMortem",
    "ContributingFactor",
    "ActionItem",
    "PostMortemApproval",
]
