from src.models.base import BaseEntity
from src.models.user import User, UserRoleEnum
from src.models.incident import (
    Incident,
    IncidentMetadata,
    AffectedItemBase,
    AffectedService,
    AffectedRegion,
    Impacts,
    ShallowRCA,
    TimelineEvent,
    ResolutionMitigation,
    RemediationStep,
    LongTermPreventativeMeasure,
    CommunicationLogEntry,
    SignOffEntry,
    IncidentStatus,  # Enum
    SeverityLevel,   # Enum
)
from src.models.postmortem import (
    PostMortem,
    ContributingFactor,
    LessonLearned,
    ActionItem,
    PostMortemApproval,
    ActionItemStatus
)


print("Rebuilding forward references for models...")

User.model_rebuild()
Incident.model_rebuild()
IncidentMetadata.model_rebuild()
AffectedService.model_rebuild()
AffectedRegion.model_rebuild()
Impacts.model_rebuild()
ShallowRCA.model_rebuild()
TimelineEvent.model_rebuild()
ResolutionMitigation.model_rebuild()
RemediationStep.model_rebuild()
LongTermPreventativeMeasure.model_rebuild()
CommunicationLogEntry.model_rebuild()
SignOffEntry.model_rebuild()
PostMortem.model_rebuild()
ContributingFactor.model_rebuild()
LessonLearned.model_rebuild()
ActionItem.model_rebuild()
PostMortemApproval.model_rebuild()

print("All models from 'src.models' package imported and forward references updated.")
