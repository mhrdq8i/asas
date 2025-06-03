from src.models.user import User
from src.models.incident import (
    Incident,
    IncidentProfile,
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
