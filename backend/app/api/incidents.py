from fastapi import APIRouter, HTTPException, Query

from app.services.correlation_engine import (
    correlate_events
)

from app.services.incident_repository import (
    get_incident,
    get_incident_events,
    list_incidents,
    update_incident_summary,
)
from app.services.operations_repository import (
    get_incident_history,
    get_incident_notes,
)
from app.services.operations_intelligence import (
    assess_deployment_risk,
    build_correlation_graph,
    build_incident_ai_summary,
    score_event_risk,
)

router = APIRouter()


@router.post("/incidents/correlate")
def run_correlation():

    incidents = correlate_events()

    return {
        "incidents_created": incidents
    }


@router.get("/incidents")
def get_incidents():

    return {
        "incidents": list_incidents()
    }


@router.get("/incidents/correlation-graph")
def get_correlation_graph(
    incident_id: int | None = Query(default=None),
):
    return build_correlation_graph(incident_id=incident_id)


@router.get("/incidents/{incident_id}")
def get_incident_details(incident_id: int):
    incident = get_incident(incident_id)

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    events = get_incident_events(incident_id)

    if not incident.get("ai_summary"):
        ai_summary = build_incident_ai_summary(incident, events)
        risk_score = max(
            [score_event_risk(event)[0] for event in events],
            default=incident.get("risk_score", 50),
        )
        update_incident_summary(incident_id, ai_summary, risk_score)
        incident["ai_summary"] = ai_summary
        incident["risk_score"] = risk_score

    return {
        "incident": incident,
        "events": events,
        "history": get_incident_history(incident_id),
        "notes": get_incident_notes(incident_id),
        "graph": build_correlation_graph(incident_id=incident_id),
    }


@router.post("/incidents/{incident_id}/summarize")
def summarize_incident(incident_id: int):
    incident = get_incident(incident_id)

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    events = get_incident_events(incident_id)
    ai_summary = build_incident_ai_summary(incident, events)
    risk_score = max(
        [score_event_risk(event)[0] for event in events],
        default=incident.get("risk_score", 50),
    )

    update_incident_summary(incident_id, ai_summary, risk_score)

    return {
        "ai_summary": ai_summary,
        "risk_score": risk_score,
    }


@router.get("/deployments/risk")
def deployment_risk(target: str | None = None):
    return assess_deployment_risk(target=target)
