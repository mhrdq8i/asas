from logging import getLogger
from typing import List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from sqlmodel.ext.asyncio.session import AsyncSession

from src.crud.alert_filter_rule_crud import (
    CrudAlertFilterRule
)
from src.crud.incident_crud import CrudIncident
from src.crud.user_crud import CrudUser
from src.models.alert_filter_rule import (
    AlertFilterRule,
    MatchTypeEnum
)
from src.models.incident import Incident
from src.api.v1.schemas.incident_schemas import (
    IncidentCreate,
    IncidentProfileCreate,
    ImpactsCreate,
    ShallowRCACreate
)
from src.models.enums import (
    SeverityLevelEnum,
    IncidentStatusEnum
)


logger = getLogger(__name__)


class AlertService:
    """
    Service for processing alerts from AlertManager.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initializes the AlertService.

        Args:
            db_session: The asynchronous database session.
        """
        self.db_session = db_session
        self.rule_crud = CrudAlertFilterRule(db_session)
        self.incident_crud = CrudIncident(db_session)
        self.user_crud = CrudUser(db_session)

    async def process_alerts(self, alerts: List[Dict[str, Any]]) -> None:
        """
        Processes a list of alerts, filters them,
        and creates incidents if necessary.

        Args:
            alerts: A list of alerts from AlertManager.
        """

        active_rules = await self.rule_crud.get_all_active_rules()

        if not active_rules:
            logger.info(
                "No active alert filter rules found. "
                "Skipping alert processing."
            )
            return

        for alert in alerts:
            # Check if an incident for this alert
            # already exists to avoid duplicates
            fingerprint = alert.get('fingerprint')
            if fingerprint and await self.incident_crud.get_incident_by_fingerprint(
                    fingerprint
            ):
                logger.info(
                    "Incident for alert with fingerprint "
                    f"{fingerprint} already exists. Skipping."
                )
                continue

            if await self._should_create_incident(alert, active_rules):
                await self._create_incident_from_alert(alert)

    async def _should_create_incident(
            self, alert: Dict[str, Any],
            rules: List[AlertFilterRule]
    ) -> bool:
        """
        Determines if an incident should be created based on the defined rules.

        Args:
            alert: The alert to check.
            rules: The list of active filter rules.

        Returns:
            True if an incident should be created, False otherwise.
        """

        matched_an_inclusion_rule = False

        for rule in rules:
            if self._matches(alert, rule):
                if rule.is_exclusion_rule:
                    logger.info(
                        "Alert matched exclusion rule "
                        f"'{rule.rule_name}'. "
                        "Incident will NOT be created."
                    )
                    # An exclusion rule immediately
                    # stops incident creation
                    return False
                else:
                    logger.info(
                        f"Alert matched inclusion rule '{rule.rule_name}'."
                    )
                    matched_an_inclusion_rule = True

        # Create incident only if it matched at least
        # one inclusion rule and was not excluded
        return matched_an_inclusion_rule

    def _matches(
        self,
        alert: Dict[str, Any],
        rule: AlertFilterRule
    ) -> bool:
        """
        Checks if an alert's field matches a rule's condition.

        Args:
            alert: The alert data.
            rule: The filter rule to check against.

        Returns:
            True if the alert matches the rule, False otherwise.
        """
        def get_nested_value(data: Dict, key: str):
            keys = key.split('.')
            value = data
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return None
            return value

        target_value = get_nested_value(alert, rule.target_field)
        if target_value is None:
            return False

        match_value = rule.match_value
        match_type = rule.match_type
        target_str = str(target_value)

        if match_type == MatchTypeEnum.EQUALS:
            return target_str == match_value
        if match_type == MatchTypeEnum.NOT_EQUALS:
            return target_str != match_value
        if match_type == MatchTypeEnum.CONTAINS:
            return match_value in target_str
        if match_type == MatchTypeEnum.NOT_CONTAINS:
            return match_value not in target_str
        # TODO: Implement REGEX and other match types if needed
        return False

    async def _create_incident_from_alert(
            self, alert: Dict[str, Any]
    ) -> Incident:
        """
        Creates an Incident record in the database from an alert.

        Args:
            alert: The alert data from which to create the incident.

        Returns:
            The newly created Incident object.
        """

        annotations = alert.get('annotations', {})

        labels = alert.get('labels', {})

        title = annotations.get(
            'summary', labels.get(
                'alertname', 'Untitled Incident'
            )
        )

        summary = annotations.get('description', 'No description provided.')

        severity_str = labels.get('severity', 'critical').lower()

        severity_mapping = {
            "critical": SeverityLevelEnum.CRITICAL,
            "high": SeverityLevelEnum.HIGH,
            "medium": SeverityLevelEnum.MEDIUM,
            "low": SeverityLevelEnum.LOW,
            "informational": SeverityLevelEnum.INFORMATIONAL,
        }

        severity = severity_mapping.get(
            severity_str, SeverityLevelEnum.CRITICAL
        )

        # A placeholder commander ID.
        # You MUST replace this with a valid user UUID
        # from your database who has the INCIDENT_COMMANDER role.
        # Consider implementing logic to fetch
        # a default user or from an on-call rotation.
        default_commander_id = UUID("f1f296a8-46c8-4fa3-9795-0626130b7da0")

        # You might want to find a user in the DB to assign as commander
        # commander = await self.user_crud.get_default_commander()
        # if commander:
        #     default_commander_id = commander.id

        try:
            detected_at = datetime.fromisoformat(
                alert['startsAt'].replace('Z', '+00:00')
            )
        except (KeyError, ValueError):
            detected_at = datetime.now(timezone.utc)

        incident_in = IncidentCreate(
            profile=IncidentProfileCreate(
                title=f"[AUTO] {title}",
                summary=summary,
                severity=severity,
                status=IncidentStatusEnum.OPEN,
                commander_id=default_commander_id,
                is_auto_detected=True,
                datetime_detected_utc=detected_at
            ),
            impacts=ImpactsCreate(
                customer_impact="Automatically generated from alert. TBD.",
                business_impact="Automatically generated from alert. TBD."
            ),
            shallow_rca=ShallowRCACreate(
                what_happened=(
                    f"Alert '{labels.get('alertname', 'N/A')}' fired."
                ),
                why_it_happened="To be investigated.",
                technical_causes="To be investigated.",
                detection_mechanisms="Prometheus AlertManager"
            ),
            # Store the unique fingerprint to prevent duplicate incidents
            alert_fingerprint=alert.get('fingerprint')
        )

        new_incident = await self.incident_crud.create_incident(
            incident_in=incident_in
        )

        logger.info(
            "Successfully created incident "
            f"{new_incident.id} from alert fingerprint "
            f"{alert.get('fingerprint')}."
        )

        return new_incident
