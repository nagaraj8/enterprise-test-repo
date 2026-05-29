from app.services.event_repository import list_events
from app.services.incident_repository import (
    create_incident,
    find_incident_by_correlation_key,
    find_incident_for_event,
    link_event_to_incident,
    touch_incident,
    update_incident_summary,
)
from app.services.operations_repository import record_event_correlation
from app.services.operations_intelligence import (
    build_incident_ai_summary,
    score_event_risk,
    severity_for_score,
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
    event_text = " ".join(
        str(event.get(field) or "")
        for field in ("source", "actor", "action", "target", "event_type", "summary")
    ).lower()

    return any(
        keyword in event_text
        for keyword in RISK_KEYWORDS
    )


def build_correlation_key(event: dict) -> str:
    service = event.get("service_name") or event.get("target") or event.get("source") or "unknown"
    environment = event.get("environment") or "unknown"
    event_type = event.get("event_type") or "activity"

    return f"{service}:{environment}:{event_type}".lower()


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

    previous_event = None

    for event in risky_events:
        correlation_key = build_correlation_key(event)
        existing_incident_id = (
            find_incident_for_event(event["id"])
            or find_incident_by_correlation_key(correlation_key)
        )
        risk_score, _ = score_event_risk(event)
        severity = severity_for_score(risk_score)

        if existing_incident_id:
            link_event_to_incident(
                existing_incident_id,
                event["id"],
            )
            touch_incident(
                existing_incident_id,
                risk_score=risk_score,
                severity=severity,
            )
            continue

        title = (
            f"Operational issue involving "
            f"{event.get('service_name') or event.get('target') or event.get('source') or 'unknown service'}"
        )

        summary = event.get(
            "summary"
        ) or "Risky operational activity was detected and grouped into an incident."

        incident_id = create_incident(
            title=title,
            summary=summary,
            severity=severity,
            risk_score=risk_score,
            priority="p1" if risk_score >= 75 else "p2" if risk_score >= 55 else "p3",
            service_name=event.get("service_name") or event.get("target"),
            environment=event.get("environment"),
            impact="Potential customer or service impact inferred from correlated operational events.",
            correlation_key=correlation_key,
        )

        link_event_to_incident(
            incident_id,
            event["id"],
        )

        ai_summary = build_incident_ai_summary(
            {
                "id": incident_id,
                "title": title,
                "summary": summary,
                "severity": severity,
            },
            [event],
        )

        update_incident_summary(
            incident_id,
            ai_summary,
            risk_score,
        )

        incidents_created.append({
            "incident_id": incident_id,
            "event_id": event["id"],
            "risk_score": risk_score,
        })

        if previous_event:
            record_event_correlation(
                source_event_id=previous_event["id"],
                target_event_id=event["id"],
                correlation_type="risk_sequence",
                confidence=0.72,
                reason="Risky events appeared together in the recent operational window.",
            )

        previous_event = event

    return incidents_created
