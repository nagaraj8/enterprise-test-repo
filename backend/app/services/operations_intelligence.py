from datetime import datetime, timezone
from typing import Any

from app.services.event_repository import list_events
from app.services.incident_repository import get_incident_events, list_incidents


DEPLOYMENT_TERMS = [
    "deploy",
    "deployment",
    "release",
    "rollout",
    "merge",
    "push",
]

RISK_TERMS = {
    "outage": 28,
    "rollback": 24,
    "failed": 20,
    "failure": 20,
    "error": 16,
    "timeout": 16,
    "latency": 14,
    "incident": 18,
    "degraded": 14,
}


def _event_text(event: dict[str, Any]) -> str:
    return " ".join(
        str(event.get(field) or "")
        for field in ("source", "actor", "action", "target", "event_type", "summary")
    ).lower()


def score_event_risk(event: dict[str, Any]) -> tuple[int, list[str]]:
    text = _event_text(event)
    score = 20
    factors: list[str] = []

    for term, weight in RISK_TERMS.items():
        if term in text:
            score += weight
            factors.append(f"Contains '{term}'")

    if any(term in text for term in DEPLOYMENT_TERMS):
        score += 12
        factors.append("Deployment-related change")

    if (event.get("source") or "").lower() in {"slack", "pagerduty", "incident"}:
        score += 10
        factors.append("Alert or incident source")

    return min(score, 100), factors


def severity_for_score(score: int) -> str:
    if score >= 75:
        return "critical"
    if score >= 55:
        return "high"
    if score >= 35:
        return "medium"
    return "low"


def build_incident_ai_summary(
    incident: dict[str, Any],
    events: list[dict[str, Any]],
) -> str:
    if not events:
        return incident.get("summary") or "No linked operational evidence is available yet."

    top_events = events[:5]
    sources = sorted({event.get("source") for event in events if event.get("source")})
    targets = sorted({event.get("target") for event in events if event.get("target")})
    risky_events = [
        event
        for event in events
        if score_event_risk(event)[0] >= 55
    ]

    first_event = top_events[-1]
    latest_event = top_events[0]
    source_text = ", ".join(sources) if sources else "unknown sources"
    target_text = ", ".join(targets[:3]) if targets else "unknown targets"

    return (
        f"{incident.get('title')} appears linked to {len(events)} event(s) "
        f"across {source_text}, primarily affecting {target_text}. "
        f"The earliest linked signal is '{first_event.get('action') or 'activity recorded'}' "
        f"and the latest is '{latest_event.get('action') or 'activity recorded'}'. "
        f"{len(risky_events)} linked event(s) contain high-risk operational language. "
        "Recommended next checks: confirm the latest deployment/change, inspect service logs, "
        "and verify customer-facing impact before changing status."
    )


def build_correlation_graph(incident_id: int | None = None) -> dict[str, Any]:
    events = get_incident_events(incident_id) if incident_id else list_events(limit=80)
    incidents = list_incidents()
    linked_incident_ids = {incident_id} if incident_id else {
        incident.get("id")
        for incident in incidents[:20]
    }

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    seen_nodes: set[str] = set()

    for incident in incidents:
        if incident.get("id") not in linked_incident_ids:
            continue

        node_id = f"incident-{incident['id']}"
        seen_nodes.add(node_id)
        nodes.append(
            {
                "id": node_id,
                "label": incident.get("title"),
                "type": "incident",
                "severity": incident.get("severity"),
            }
        )

    previous_event_id: str | None = None

    for event in events:
        event_node_id = f"event-{event['id']}"
        seen_nodes.add(event_node_id)
        nodes.append(
            {
                "id": event_node_id,
                "label": event.get("action") or event.get("event_type") or "Activity",
                "type": "event",
                "source": event.get("source"),
                "timestamp": event.get("timestamp"),
            }
        )

        source = event.get("source") or "unknown"
        source_node_id = f"source-{source}"
        if source_node_id not in seen_nodes:
            seen_nodes.add(source_node_id)
            nodes.append(
                {
                    "id": source_node_id,
                    "label": source,
                    "type": "source",
                }
            )

        edges.append(
            {
                "from": source_node_id,
                "to": event_node_id,
                "label": "emitted",
            }
        )

        if incident_id:
            edges.append(
                {
                    "from": event_node_id,
                    "to": f"incident-{incident_id}",
                    "label": "evidence",
                }
            )

        if previous_event_id:
            edges.append(
                {
                    "from": event_node_id,
                    "to": previous_event_id,
                    "label": "nearby",
                }
            )

        previous_event_id = event_node_id

    return {
        "nodes": nodes,
        "edges": edges,
    }


def assess_deployment_risk(target: str | None = None) -> dict[str, Any]:
    events = list_events(limit=120)
    if target:
        target_lower = target.lower()
        events = [
            event
            for event in events
            if target_lower in _event_text(event)
        ]

    deployment_events = [
        event
        for event in events
        if any(term in _event_text(event) for term in DEPLOYMENT_TERMS)
    ]
    evaluation_events = deployment_events or events[:20]

    factor_counts: dict[str, int] = {}
    scored_events = []
    total_score = 20

    for event in evaluation_events[:20]:
        score, factors = score_event_risk(event)
        total_score = max(total_score, score)
        scored_events.append(
            {
                **event,
                "risk_score": score,
                "risk_factors": factors,
            }
        )

        for factor in factors:
            factor_counts[factor] = factor_counts.get(factor, 0) + 1

    if len(deployment_events) >= 5:
        total_score = min(total_score + 10, 100)
        factor_counts["Frequent deployment/change activity"] = len(deployment_events)

    recent_incidents = list_incidents()[:5]
    if recent_incidents:
        total_score = min(total_score + 8, 100)
        factor_counts["Recent open incidents exist"] = len(recent_incidents)

    top_factors = [
        {"label": label, "count": count}
        for label, count in sorted(
            factor_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:6]
    ]

    recommendations = [
        "Review the most recent deployment and rollback plan before release.",
        "Check error-rate, latency, and saturation dashboards for the target service.",
        "Hold promotion if a high-severity incident is still open for the same target.",
    ]

    return {
        "score": total_score,
        "level": severity_for_score(total_score),
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "target": target,
        "deployment_events": len(deployment_events),
        "factors": top_factors,
        "recommendations": recommendations,
        "evidence": scored_events[:6],
    }
