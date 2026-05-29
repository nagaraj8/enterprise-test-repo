from datetime import timedelta

from app.services.event_repository import list_events
from app.services.incident_repository import (
    create_incident,
    link_event_to_incident,
)


RISK_KEYWORDS = [
    "failed",
    "rollback",
    "timeout",
    "error",
    "incident",
    "outage",
    "latency",
]


def is_risky_event(event: dict) -> bool:

    action = (
        event.get("action")
        or ""
    ).lower()

    return any(
        keyword in action
        for keyword in RISK_KEYWORDS
    )


def correlate_events():

    events = list_events(
        limit=200
    )

    risky_events = [
        event
        for event in events
        if is_risky_event(event)
    ]

    incidents_created = []

    for event in risky_events:

        title = (
            f"Operational issue involving "
            f"{event.get('target')}"
        )

        summary = event.get(
            "summary"
        )

        incident_id = create_incident(
            title=title,
            summary=summary,
            severity="high",
        )

        link_event_to_incident(
            incident_id,
            event["id"],
        )

        incidents_created.append({
            "incident_id": incident_id,
            "event_id": event["id"],
        })

    return incidents_created
