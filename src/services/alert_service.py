import logging
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio.session import (
    AsyncSession
)

from src.core.config import settings
from src.models.user import User
from src.crud.user_crud import CrudUser
from src.crud.alert_filter_rule_crud import (
    CrudAlertFilterRule
)
from src.crud.incident_crud import (
    CrudIncident
)
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
from src.services.incident_service import (
    IncidentService
)


logger = logging.getLogger(__name__)

# Define the username for the system account that creates incidents
SYSTEM_USER_USERNAME = "alert_manager"


class AlertService:
    """
    Service for fetching, processing,
    and creating incidents from alerts.
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.rule_crud = CrudAlertFilterRule(db_session)
        self.incident_crud = CrudIncident(db_session)
        self.user_crud = CrudUser(db_session)
        self.incident_service = IncidentService(db_session)

    async def fetch_alerts_from_prometheus(self) -> List[Dict[str, Any]]:
        """
        Fetches active alerts from
        the Prometheus Alertmanager API.
        """

        api_url = settings.PROMETHEUS_API_URL

        if not api_url:
            logger.error(
                "PROMETHEUS_API_URL is not configured. "
                "Cannot fetch alerts."
            )

            return []

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    api_url,
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()

        except httpx.RequestError as e:
            logger.error(
                f"Failed to fetch alerts from {api_url}: {e}"
            )

            return []

    async def process_alerts(
        self,
        alerts: List[Dict[str, Any]]
    ) -> None:
        """
        Processes a list of alerts,
        filters them, and creates incidents.
        """

        active_rules = await self.rule_crud.get_all_active_rules()

        if not active_rules:
            logger.warning(
                "No active alert filter rules found. "
                "Skipping alert processing."
            )

            return

        system_user = await self.user_crud.get_user_by_username(
            username=SYSTEM_USER_USERNAME
        )

        if not system_user:
            logger.error(
                f"CRITICAL: System user '{SYSTEM_USER_USERNAME}' "
                "not found in the database. Cannot create incidents."
            )

            return

        for alert in alerts:
            fingerprint = alert.get('fingerprint')
            if fingerprint and await \
                    self.incident_crud.get_incident_by_fingerprint(
                        fingerprint
                    ):
                logger.info(
                    f"Incident for fingerprint {fingerprint} "
                    "already exists. Skipping."
                )
                continue

            if await self._should_create_incident(
                alert,
                active_rules
            ):
                await self._create_incident_from_alert(
                    alert,
                    system_user
                )

    async def _should_create_incident(
        self,
        alert: Dict[str, Any],
        rules: List[AlertFilterRule]
    ) -> bool:
        """
        Determines if an incident should be
        created based on the defined rules.
        """

        matched_an_inclusion_rule = False

        for rule in rules:
            if self._matches(alert, rule):
                if rule.is_exclusion_rule:
                    logger.info(
                        "Alert matched EXCLUSION rule "
                        f"'{rule.rule_name}'. "
                        "Incident will NOT be created."
                    )

                    return False

                else:
                    logger.info(
                        "Alert matched INCLUSION rule "
                        f"'{rule.rule_name}'."
                    )
                    matched_an_inclusion_rule = True

        return matched_an_inclusion_rule

    def _matches(
        self,
        alert: Dict[str, Any],
        rule: AlertFilterRule
    ) -> bool:
        """
        Checks if an alert's field matches a rule's condition.
        """

        def get_nested_value(
                data: Dict,
                key: str
        ) -> Optional[str]:

            keys = key.split('.')
            value = data

            for k in keys:
                value = value.get(
                    k
                ) if isinstance(
                    value,
                    dict
                ) else None
                if value is None:
                    return None

            return str(value)

        target_value_str = get_nested_value(
            alert,
            rule.target_field
        )

        if target_value_str is None:
            return False

        match_value = rule.match_value
        match_type = rule.match_type

        if match_type == MatchTypeEnum.EQUALS:
            return target_value_str == match_value

        if match_type == MatchTypeEnum.NOT_EQUALS:
            return target_value_str != match_value

        if match_type == MatchTypeEnum.CONTAINS:
            return match_value in target_value_str

        if match_type == MatchTypeEnum.NOT_CONTAINS:
            return match_value not in target_value_str

        return False

    async def _create_incident_from_alert(
            self,
            alert: Dict[str, Any],
            system_user: User
    ) -> Incident:
        """
        Creates an incident record from an
        alert using a dedicated system user.
        """

        logger.info(
            "Creating incident from alert, "
            "initiated by system user "
            f"'{system_user.username}'."
        )

        annotations = alert.get('annotations', {})

        labels = alert.get('labels', {})

        title = annotations.get('summary', labels.get(
            'alertname', 'Untitled Incident')
        )

        summary = annotations.get(
            'description',
            'No description provided.'
        )

        severity_str = labels.get(
            'severity',
            'critical'
        ).lower()

        severity_mapping = {
            "critical": SeverityLevelEnum.CRITICAL,
            "high": SeverityLevelEnum.HIGH,
            "medium": SeverityLevelEnum.MEDIUM,
            "low": SeverityLevelEnum.LOW,
            "informational": SeverityLevelEnum.INFORMATIONAL,
        }

        severity = severity_mapping.get(
            severity_str,
            SeverityLevelEnum.CRITICAL
        )

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
                # The incident is created by the system user,
                # and by default, assigned to itself as commander.
                # This can be changed later or by an escalation policy.
                commander_id=system_user.id,
                is_auto_detected=True,
                datetime_detected_utc=detected_at
            ),
            impacts=ImpactsCreate(),
            shallow_rca=ShallowRCACreate(
                what_happened=(
                    f"Alert '{labels.get('alertname', 'N/A')}' fired."
                ),
                detection_mechanisms="Prometheus AlertManager"
            ),
            alert_fingerprint=alert.get('fingerprint')
        )

        new_incident = await self.incident_service.create_incident(
            incident_in=incident_in,
            current_user=system_user
        )

        logger.info(
            f"Successfully created incident {new_incident.id} "
            f"from alert fingerprint {alert.get('fingerprint')}."
        )
        return new_incident
