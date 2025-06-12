from enum import Enum


# --- User Enums ---

class UserRoleEnum(str, Enum):
    SRE = "sre"
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"
    INCIDENT_COMMANDER = "incident_commander"


class RolesEnum(str, Enum):
    QA_LEAD = "QA Lead"
    SRE_LEAD = "SRE Lead"
    BE_LEAD = "Back-end Lead"
    FE_LEAD = "Front-end Lead"
    DEVOPS_LEAD = "DevOps Lead"
    PRODUCT_OWNER = "Product Owner"
    DEPARTMENT_HEAD = "Department Head"
    ENGINEERING_MANAGER = "Engineering Manager"


# --- Incident Enums ---

class IncidentStatusEnum(str, Enum):
    OPEN = "Open"
    DOING = "Doing"
    RESOLVED = "Resolved"
    UNKNOWN = "Unknown"


class SeverityLevelEnum(str, Enum):
    CRITICAL = "Sev1-Critical"
    HIGH = "Sev2-High"
    MEDIUM = "Sev3-Medium"
    LOW = "Sev4-Low"
    INFORMATIONAL = "Sev5-Informational"


class ActionItemStatusEnum(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"


class AffectedItemEnum(str, Enum):
    API = "API"
    DATABASE = "Database"
    INFRASTRUCTURE = "Infrastructure"
    NETWORK = "Network"
    APPLICATION = "Application"
    CUSTOMER_DATA = "Customer Data"
    SECURITY = "Security"
    EXTERNAL_SERVICE = "External Service"


# --- Postmortem Enums ---

class PostMortemStatusEnum(str, Enum):
    DRAFT = "Draft"
    IN_REVIEW = "In Review"
    COMPLETED = "Completed"
    CANCELED = "Canceled"


class FactorTypeEnum(str, Enum):
    TECHNICAL = "Technical"
    PROCESS = "Process"
    HUMAN = "Human"
    UNKNOWN = "Unknown"
