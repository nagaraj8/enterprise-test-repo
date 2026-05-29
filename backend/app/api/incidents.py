from fastapi import APIRouter

from app.services.correlation_engine import (
    correlate_events
)

from app.services.incident_repository import (
    list_incidents
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
