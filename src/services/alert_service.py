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
from src.models.incident import Incident
from src.crud.incident_crud import (
    CrudIncident
)
from src.crud.alert_filter_rule_crud import (
    CrudAlertFilterRule
)
from src.models.alert_filter_rule import (
    AlertFilterRule,
    MatchTypeEnum
)
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
SYSTEM_USER_USERNAME = "alert_manager"


class AlertService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.rule_crud = CrudAlertFilterRule(db_session)
        self.incident_crud = CrudIncident(db_session)
        self.user_crud = CrudUser(db_session)
        self.incident_service = IncidentService(db_session)

    async def fetch_alerts_from_prometheus(
            self
    ) -> List[Dict[str, Any]]:

        api_url = settings.PROMETHEUS_API_URL

        if not api_url:
            logger.error(
                "PROMETHEUS_API_URL is not configured."
            )
            return []

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    api_url,
                    timeout=10.0
                )

                response.raise_for_status()

                response_data = response.json()

                if isinstance(
                    response_data,
                    dict
                ) and response_data.get('status') == 'success':

                    return response_data.get('data', [])

                # If the structure is unexpected,
                # return it as is for debugging
                return response_data

        except httpx.RequestError as e:
            logger.error(
                f"Failed to fetch alerts from {api_url}: {e}"
            )

            return []

        except Exception as e:
            logger.error(
                f"Error parsing JSON from Alertmanager: {e}"
            )

            return []

    async def process_alerts(
        self,
        alerts: List[Dict[str, Any]]
    ) -> None:

        active_rules = await self.rule_crud.get_all_active_rules()

        if not active_rules:
            logger.warning(
                "No active filter rules found. "
                "Skipping processing."
            )

            return

        system_user = await self.user_crud.get_user_by_username(
            username=SYSTEM_USER_USERNAME
        )

        if not system_user:
            logger.error(
                "CRITICAL: System user "
                f"'{SYSTEM_USER_USERNAME}' not found. "
                "Cannot create incidents."
            )

            return

        for alert in alerts:
            # Ensure 'alert' is a
            # dictionary before processing
            if not isinstance(alert, dict):
                logger.warning(
                    "Skipping non-dictionary item "
                    f"in alerts list: {alert}"
                )
                continue

            fingerprint = alert.get('fingerprint')

            if fingerprint and await \
                    self.incident_crud.get_incident_by_fingerprint(
                        fingerprint
                    ):
                logger.info(
                    "Duplicate incident for fingerprint "
                    f"{fingerprint}. Skipping."
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
            else:
                logger.info(
                    f"Alert with fingerprint {fingerprint} "
                    "did not match filters."
                )

    async def _should_create_incident(
        self,
        alert: Dict[str, Any],
        rules: List[AlertFilterRule]
    ) -> bool:

        matched_inclusion = False

        for rule in rules:
            if self._matches(alert, rule):
                if rule.is_exclusion_rule:
                    logger.info(
                        "Alert matched EXCLUSION rule "
                        f"'{rule.rule_name}'. "
                        "Will not create incident."
                    )
                    return False

                matched_inclusion = True

        return matched_inclusion

    def _matches(
        self,
        alert: Dict[str, Any],
        rule: AlertFilterRule
    ) -> bool:
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

        target_value = get_nested_value(
            alert,
            rule.target_field
        )

        if target_value is None:
            return False

        if rule.match_type == MatchTypeEnum.EQUALS:
            return target_value == rule.match_value

        if rule.match_type == MatchTypeEnum.NOT_EQUALS:
            return target_value != rule.match_value

        if rule.match_type == MatchTypeEnum.CONTAINS:
            return rule.match_value in target_value

        if rule.match_type == MatchTypeEnum.NOT_CONTAINS:
            return rule.match_value not in target_value

        return False

    async def _create_incident_from_alert(
        self,
        alert: Dict[str, Any],
        system_user: User
    ) -> Incident:

        annotations = alert.get('annotations', {})

        labels = alert.get('labels', {})

        title = annotations.get(
            'summary',
            labels.get(
                'alertname',
                'Untitled Incident'
            )
        )

        summary = annotations.get(
            'description',
            'No description provided.'
        )

        severity_str = labels.get(
            'severity',
            'critical'
        ).lower()

        severity_map = {
            "critical": SeverityLevelEnum.CRITICAL,
            "high": SeverityLevelEnum.HIGH,
            "medium": SeverityLevelEnum.MEDIUM,
            "low": SeverityLevelEnum.LOW,
            "informational": SeverityLevelEnum.INFORMATIONAL,
        }

        severity = severity_map.get(
            severity_str,
            SeverityLevelEnum.CRITICAL
        )

        try:
            detected_at = datetime.fromisoformat(
                alert[
                    'startsAt'
                ].replace('Z', '+00:00')
            )

        except (KeyError, ValueError):
            detected_at = datetime.now(timezone.utc)

        incident_in = IncidentCreate(

            alert_fingerprint=alert.get('fingerprint'),

            profile=IncidentProfileCreate(
                title=f"[AUTO] {title}",
                summary=summary,
                severity=severity,
                status=IncidentStatusEnum.OPEN,
                commander_id=system_user.id,
                is_auto_detected=True,
                datetime_detected_utc=detected_at
            ),

            impacts=ImpactsCreate(
                customer_impact="To be determined.",
                business_impact="To be determined."
            ),

            shallow_rca=ShallowRCACreate(
                what_happened=f"Alert '{labels.get('alertname', 'N/A')}' fired.",
                why_it_happened="To be investigated.",
                technical_causes="To be investigated.",
                detection_mechanisms="Prometheus AlertManager"
            )
        )

        new_incident = await self.incident_service.create_incident(
            incident_in=incident_in,
            current_user=system_user
        )

        logger.info(
            "Successfully created incident "
            f"{new_incident.id} for alert "
            f"{alert.get('fingerprint')}."
        )

        return new_incident
