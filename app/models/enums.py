from enum import Enum


class SeverityEnum(str, Enum):
    severity_l1 = "Severity Level 1"
    severity_l2 = "Severity Level 2"
    severity_l3 = "Severity Level 3"
    severity_l4 = "Severity Level 4"
    severity_l5 = "Severity Level 5"


class StatusEnum(str, Enum):
    open = "Open"
    doing = "Doing"
    resolved = "Resolved"


class UserRoleEnum(str, Enum):
    admin = "Admin"
    team = "Team"
    viewer = "Viewer"
