from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, HttpUrl


class IncomingAlert(BaseModel):
    """
    Represents a single alert from a generic monitoring system like Prometheus/Alertmanager.
    The structure is kept compatible with Prometheus for ease of use.
    """
    labels: Dict[str, str] = {}
    annotations: Dict[str, str] = {}
    state: str
    activeAt: Optional[datetime] = None
    startsAt: datetime
    endsAt: Optional[datetime] = None
    generatorURL: HttpUrl
    fingerprint: str

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "labels": {
                    "alertname": "HighRequestLatency",
                    "severity": "critical",
                    "instance": "my-app:8080",
                    "namespace": "production"
                },
                "annotations": {
                    "summary": "High request latency detected on my-app",
                    "description": "The P99 latency for the main service is over 500ms for the last 5 minutes.",
                    "runbook_url": "http://runbooks.example.com/latency-issues"
                },
                "state": "firing",
                "activeAt": "2025-06-21T00:00:00Z",
                "startsAt": "2025-06-20T23:55:00Z",
                "endsAt": "0001-01-01T00:00:00Z",
                "generatorURL": "http://prometheus.example.com/graph?g0.expr=...",
                "fingerprint": "a1b2c3d4e5f6g7h8i9j0"
            }
        }


class AlertData(BaseModel):
    """
    The 'data' object within the Alert Manager API response.
    """
    alerts: List[IncomingAlert]


class AlertManagerResponse(BaseModel):
    """
    The top-level structure of a Prometheus-compatible /api/v1/alerts endpoint response.
    """
    status: str
    data: AlertData
