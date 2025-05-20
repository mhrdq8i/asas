```mermaid

classDiagram
    class IncidentBase {
        +str title
        +str incident_id
        +str severity
        +str status
        +datetime detection_time
        +str detected_by
        +str description
        +str affected_services
        +str regions_affected
        +str customer_impact
        +str revenue_impact
        +str root_cause
        +datetime resolution_time
    }

    class Incident {
        +int id PK
    }

    class IncidentCreate {
    }

    class IncidentRead {
        +int id
        +List~TimelineRead~ timelines
        +List~ActionItemRead~ action_items
        +List~CommunicationLogRead~ communication_logs
    }

    class TimelineBase {
        +datetime timestamp
        +str update
        +str owner
        +int incident_id FK
    }

    class Timeline {
        +int id PK
    }

    class TimelineCreate {
    }

    class TimelineRead {
        +int id
    }

    class ActionItemBase {
        +str task
        +str owner
        +datetime due_date
        +str status
        +int incident_id FK
    }

    class ActionItem {
        +int id PK
    }

    class ActionItemCreate {
    }

    class ActionItemRead {
        +int id
    }

    class CommunicationLogBase {
        +datetime timestamp
        +str channel
        +str message
        +int incident_id FK
    }

    class CommunicationLog {
        +int id PK
    }

    class CommunicationLogCreate {
    }

    class CommunicationLogRead {
        +int id
    }

    IncidentBase <|-- Incident
    IncidentBase <|-- IncidentCreate
    IncidentBase <|-- IncidentRead
    TimelineBase <|-- Timeline
    TimelineBase <|-- TimelineCreate
    TimelineBase <|-- TimelineRead
    ActionItemBase <|-- ActionItem
    ActionItemBase <|-- ActionItemCreate
    ActionItemBase <|-- ActionItemRead
    CommunicationLogBase <|-- CommunicationLog
    CommunicationLogBase <|-- CommunicationLogCreate
    CommunicationLogBase <|-- CommunicationLogRead

    Incident        ||--o{      Timeline                : "has"
    Incident        ||--o{      ActionItem              : "has"
    Incident        ||--o{      CommunicationLog        : "has"
    IncidentRead    ||--o{      TimelineRead            : "includes"
    IncidentRead    ||--o{      ActionItemRead          : "includes"
    IncidentRead    ||--o{      CommunicationLogRead    : "includes"

```
