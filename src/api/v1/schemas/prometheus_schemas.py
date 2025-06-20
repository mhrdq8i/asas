from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class PrometheusAlert(BaseModel):
    """
    Represents a single alert from the Prometheus/Alertmanager API.
    """
    labels: Dict[str, str]
    annotations: Dict[str, str]
    state: str  # e.g., 'firing', 'pending'
    activeAt: Optional[datetime] = None
    startsAt: datetime
    endsAt: Optional[datetime] = None
    generatorURL: str
    fingerprint: str

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "labels": {
                    "alertname": "HighRequestLatency",
                    "severity": "critical",
                    "instance": "my-app:8080"
                },
                "annotations": {
                    "summary": "High request latency detected",
                    "description": "The P99 latency is over 500ms."
                },
                "state": "firing",
                "startsAt": "2025-06-20T16:00:00Z",
                "generatorURL": "http://prometheus/graph?g0.expr...",
                "fingerprint": "a1b2c3d4e5f6g7h8"
            }
        }


class AlertData(BaseModel):
    """
    The 'data' part of the Prometheus API response.
    """
    alerts: List[PrometheusAlert]


class PrometheusAlertResponse(BaseModel):
    """
    The top-level structure of the response from the /api/v1/alerts endpoint.
    """
    status: str  # e.g., 'success'
    data: AlertData
