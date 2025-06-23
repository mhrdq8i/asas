import logging
import asyncio
from typing import List
import httpx

from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.config import settings
from src.services.incident_service import IncidentService
from src.crud.incident_crud import CrudIncident
from src.api.v1.schemas.alerting_schemas import (
    IncomingAlert,
    AlertManagerResponse
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
from src.exceptions.base_exceptions import (
    ConfigurationError
)


logger = logging.getLogger(__name__)


class AlertingService:
    """
    Service to handle fetching and processing
    alerts from multiple monitoring sources.
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.incident_crud = CrudIncident(db_session)
        self.incident_service = IncidentService(db_session)
        self.system_user = None

    async def _get_system_user(self):
        """
        Retrieves the dedicated system user for auto-generated incidents.
        """
        if self.system_user is None:
            commander_username = settings.SYSTEM_COMMANDER_USERNAME
            if not commander_username:
                raise ConfigurationError(
                    "SYSTEM_COMMANDER_USERNAME is not configured.")

            from src.crud.user_crud import CRUDUser
            user_crud = CRUDUser(self.db_session)

            system_user = await user_crud.get_user_by_username(
                username=commander_username
            )

            if not system_user or not system_user.is_system_user\
                    or not system_user.is_commander:
                raise ConfigurationError(
                    f"The user '{commander_username}' "
                    "is not a valid, configured system commander."
                )

            logger.info(f"Loaded system commander: {system_user.username}")
            self.system_user = system_user

        return self.system_user

    async def _fetch_alerts_from_endpoint(
        self, api_url: str, client: httpx.AsyncClient
    ) -> List[IncomingAlert]:
        """
        Fetches and validates alerts from a single Alert Manager API endpoint.
        """
        try:
            response = await client.get(api_url, timeout=10.0)
            response.raise_for_status()

            alert_data = response.json()
            validated_response = AlertManagerResponse.model_validate(
                alert_data)

            if validated_response.status == "success":
                firing_alerts = [
                    alert for alert in validated_response.data.alerts
                    if alert.state == "firing"
                ]
                logger.info(
                    f"Successfully fetched {len(firing_alerts)} "
                    f"firing alerts from {api_url}."
                )
                return firing_alerts
            else:
                logger.error(
                    f"Alert Manager endpoint {api_url} "
                    "returned status '{validated_response.status}'."
                )
                return []

        except httpx.RequestError as e:
            logger.error(
                "HTTP request error occurred while "
                f"fetching alerts from {api_url}: {e}"
            )
        except Exception:
            logger.error(
                "An unexpected error occurred while "
                f"fetching alerts from {api_url}.",
                exc_info=True
            )

        return []

    async def _fetch_all_alerts(self) -> List[IncomingAlert]:
        """
        Fetches alerts from all configured
        Alert Manager endpoints concurrently.
        """
        api_urls = settings.ALERT_MANAGER_API_URLS
        if not api_urls:
            logger.warning(
                "ALERT_MANAGER_API_URLS is not configured. "
                "Skipping alert check."
            )
            return []

        all_firing_alerts: List[IncomingAlert] = []
        async with httpx.AsyncClient() as client:
            tasks = [self._fetch_alerts_from_endpoint(
                url, client) for url in api_urls]
            results = await asyncio.gather(*tasks)

            for alert_list in results:
                all_firing_alerts.extend(alert_list)

        # De-duplicate alerts based on fingerprint,
        # in case multiple sources report the same alert
        unique_alerts = {
            alert.fingerprint: alert for alert in all_firing_alerts
        }
        logger.info(
            "Total unique firing alerts gathered from "
            f"all sources: {len(unique_alerts)}"
        )
        return list(unique_alerts.values())

    def _map_alert_to_incident_create(
        self, alert: IncomingAlert
    ) -> IncidentCreate:
        """
        Maps an incoming alert to an IncidentCreate schema.
        """
        # ... (This method remains the same as before) ...
        commander_id = self.system_user.id
        severity_mapping = {
            "critical": SeverityLevelEnum.CRITICAL,
            "warning": SeverityLevelEnum.HIGH,
            "info": SeverityLevelEnum.INFORMATIONAL,
        }
        severity = severity_mapping.get(alert.labels.get(
            "severity", "info").lower(), SeverityLevelEnum.MEDIUM)
        title = alert.annotations.get(
            "summary", alert.labels.get("alertname", "Untitled Alert"))
        summary = alert.annotations.get(
            "description", "No description provided.")
        profile = IncidentProfileCreate(
            title=f"[Auto-Generated] {title}",
            severity=severity,
            datetime_detected_utc=alert.startsAt,
            is_auto_detected=True,
            commander_id=commander_id,
            summary=summary,
            status=IncidentStatusEnum.OPEN
        )
        impacts = ImpactsCreate(
            customer_impact="To be determined.",
            business_impact="To be determined."
        )
        shallow_rca = ShallowRCACreate(
            what_happened=f"Alert '{title}' fired.",
            why_it_happened="Investigation needed.",
            technical_causes="Investigation needed.",
            detection_mechanisms="Automated Monitoring"
        )
        return IncidentCreate(
            profile=profile, impacts=impacts, shallow_rca=shallow_rca
        )

    async def process_incoming_alerts(self):
        """
        Main method to fetch alerts from all sources and create incidents.
        """
        logger.info("Starting monitoring alert processing cycle.")

        try:
            await self._get_system_user()
        except ConfigurationError as e:
            logger.critical(
                f"Aborting alert processing due to configuration error: {e}")
            return

        all_alerts = await self._fetch_all_alerts()
        if not all_alerts:
            logger.info("No firing alerts to process from any source.")
            return

        for alert in all_alerts:
            try:
                incident_in = self._map_alert_to_incident_create(alert)
                incident_title = incident_in.profile.title

                existing_incident = await self.incident_crud.get_open_auto_detected_incident_by_title(
                    title=incident_title
                )
                if existing_incident:
                    logger.info(
                        "An active, auto-detected incident with title "
                        f"'{incident_title}' already exists. Skipping."
                    )
                    continue

                logger.warning(
                    "New firing alert detected. Creating incident with title: "
                    f"'{incident_title}'."
                )
                await self.incident_service.create_incident(
                    incident_in=incident_in,
                    current_user=self.system_user
                )

            except Exception:
                logger.error(
                    "Failed to process alert with fingerprint "
                    f"{alert.fingerprint}.",
                    exc_info=True
                )

        logger.info("Finished monitoring alert processing cycle.")
