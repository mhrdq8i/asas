from logging import getLogger
from typing import List

from src.models.incident import Incident
from src.core.config import settings
from src.core.email_utils import (
    send_email_async
)


logger = getLogger(__name__)


class NotificationService:
    """
    A dedicated service to handle sending
    notifications via various channels.
    """

    def __init__(self):
        """
        Initializes the notification service.
        In the future, it can load channel-specific
        configurations from settings.
        """
        pass

    async def send_incident_creation_email(
        self,
        incident: Incident
    ):
        """
        Formats and sends an email notification
        about a newly created incident.
        """

        recipients_str = \
            settings.INCIDENT_NOTIFICATION_RECIPIENTS

        if not recipients_str:
            logger.warning(
                "INCIDENT_NOTIFICATION_RECIPIENTS "
                "is not set. "
                "Skipping email notification."
            )

            return

        recipients: List[str] = [
            email.strip(
            ) for email in recipients_str.split(
                ','
            ) if email.strip()
        ]

        if not recipients:
            logger.warning(
                "No valid recipients found. "
                "Skipping email notification."
            )

            return

        subject = (
            "New Incident "
            f"[{incident.profile.severity.value}]: "
            f"{incident.profile.title}"
        )

        # Basic HTML content for the email
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: sans-serif; margin: 20px; }}
                p {{ margin: 5px 0; }}
                strong {{ color: #333; }}
                h2 {{ color: #d9534f; }}
                hr {{ border: 0; border-top: 1px solid #eee; }}
            </style>
        </head>
        <body>
            <h2>New Incident Reported</h2>
            <p><strong>ID:</strong> {incident.id}</p>
            <p><strong>Title:</strong> {incident.profile.title}</p>
            <p><strong>Severity:</strong> {incident.profile.severity.value}</p>
            <p><strong>Status:</strong> {incident.profile.status.value}</p>
            <p>
            <strong>Commander:</strong>
            {incident.profile.commander.username if incident.profile.commander else 'N/A'}
            </p>
            <hr>
            <h3>Summary:</h3>
            <p>{incident.profile.summary}</p>
            <hr>
            <p>Automated notification from the Incident Management System.</p>
        </body>
        </html>
        """

        logger.info(
            "Attempting to send incident "
            "creation notification "
            f"for incident {incident.id} "
            f"to: {recipients}"
        )

        for recipient in recipients:
            try:
                # CORRECTED:
                # Pass the actual subject and
                # html_content variables
                await send_email_async(
                    email_to=recipient,
                    subject=subject,
                    html_content=html_content
                )

            except Exception as e:
                logger.error(
                    "Failed to send incident notification "
                    f"email to {recipient}: {e}",
                    exc_info=True
                )

        logger.info(
            "Finished sending incident "
            "creation notifications "
            f"for incident {incident.id}."
        )
