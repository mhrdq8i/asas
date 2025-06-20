import logging
import httpx
from typing import List

from sqlmodel.ext.asyncio.session import AsyncSession

from src.crud.user_crud import CRUDUser
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
from src.models.enums import SeverityLevelEnum, IncidentStatusEnum
from src.exceptions.base_exceptions import (
    ConfigurationError
)


logger = logging.getLogger(__name__)


class AlertingService:
    """
    Service to handle fetching and processing
    alerts from a monitoring source.
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.incident_crud = CrudIncident(db_session)
        self.incident_service = IncidentService(db_session)

        # The user performing the action will be a system user.
        # A robust strategy is needed here, e.g.,
        # fetching a dedicated 'system' user.
        self.system_user = None

    async def _get_system_user(self):
        """
        Retrieves the dedicated system user
        configured to be the incident commander.
        This user must exist and be flagged
        as both a system user and a commander.
        """

        if self.system_user is None:
            commander_username = settings.SYSTEM_COMMANDER_USERNAME

            if not commander_username:
                raise ConfigurationError(
                    "SYSTEM_COMMANDER_USERNAME is not configured."
                )

            user_crud = CRUDUser(self.db_session)

            system_user = await user_crud.get_user_by_username(
                username=commander_username
            )

            if not system_user:
                raise ConfigurationError(
                    "The configured system commander user "
                    f"'{commander_username}' was not found."
                )

            if not system_user.is_system_user:
                raise ConfigurationError(
                    f"The configured user '{commander_username}' "
                    "is not a designated system user (is_system_user=False)."
                )

            if not system_user.is_commander:
                raise ConfigurationError(
                    f"The configured system user '{commander_username}' "
                    "is not designated as an Incident Commander (is_commander=False)."
                )

            logger.info(f"Loaded system commander: {system_user.username}")

            self.system_user = system_user

        return self.system_user

    async def _fetch_alerts_from_source(self) -> List[IncomingAlert]:
        """
        Fetches active alerts from the configured Alert Manager API.
        """
        api_url = settings.ALERT_MANAGER_API_URL

        if not api_url:
            logger.warning(
                "ALERT_MANAGER_API_URL is not configured. "
                " Skipping alert check."
            )

            return []

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(api_url)

                response.raise_for_status()

                alert_data = response.json()

                validated_response = AlertManagerResponse.model_validate(
                    alert_data
                )

                if validated_response.status == "success":
                    firing_alerts = [
                        alert for alert in validated_response.data.alerts if alert.state == "firing"]
                    logger.info(
                        f"Successfully fetched {len(firing_alerts)} firing alerts from the monitoring source.")
                    return firing_alerts
                else:
                    logger.error(
                        f"Alert Manager API returned status '{validated_response.status}'.")
                    return []

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error occurred while fetching alerts: {e.response.status_code}", exc_info=True)
        except Exception:
            logger.error(
                "An unexpected error occurred while fetching alerts from monitoring source.", exc_info=True)

        return []

    def _map_alert_to_incident_create(self, alert: IncomingAlert) -> IncidentCreate:
        """
        Maps an incoming alert to an IncidentCreate schema.
        This contains the business logic for how alerts become incidents.
        """
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
        what_happened = f"Monitoring alert '{alert.labels.get('alertname')}' started firing at {alert.startsAt}."

        profile = IncidentProfileCreate(
            title=f"[Auto-Generated] {title}",
            severity=severity,
            datetime_detected_utc=alert.startsAt,
            is_auto_detected=True,  # This is the key change
            commander_id=commander_id,
            summary=summary,
            status=IncidentStatusEnum.OPEN
        )
        impacts = ImpactsCreate(
            customer_impact="To be determined.",
            business_impact="To be determined."
        )
        shallow_rca = ShallowRCACreate(
            what_happened=what_happened,
            why_it_happened="Investigation required.",
            technical_causes="Investigation required.",
            detection_mechanisms="Detected via automated monitoring."
        )

        return IncidentCreate(
            profile=profile,
            impacts=impacts,
            shallow_rca=shallow_rca
        )

    async def process_incoming_alerts(self):
        """
        Main method to fetch alerts and create incidents if they don't already exist.
        """
        logger.info("Starting monitoring alert processing cycle.")
        firing_alerts = await self._fetch_alerts_from_source()
        if not firing_alerts:
            logger.info("No firing alerts to process.")
            return

        await self._get_system_user()

        for alert in firing_alerts:
            try:
                incident_in = self._map_alert_to_incident_create(alert)
                incident_title = incident_in.profile.title

                # De-duplication Logic: Check if an open, auto-detected incident with the same title exists.
                existing_incident = await self.incident_crud.get_open_auto_detected_incident_by_title(
                    title=incident_title
                )
                if existing_incident:
                    logger.info(
                        f"An active, auto-detected incident with title '{incident_title}' already exists. Skipping.")
                    continue

                logger.warning(
                    f"New firing alert detected. Creating incident with title: '{incident_title}'.")

                await self.incident_service.create_incident(
                    incident_in=incident_in,
                    current_user=self.system_user
                )

            except Exception as e:
                logger.error(
                    f"Failed to process alert with fingerprint {alert.fingerprint}: {e}", exc_info=True)

        logger.info("Finished monitoring alert processing cycle.")
