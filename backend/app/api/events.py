from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.embedding_service import create_embedding
from app.services.event_repository import insert_event
from app.services.operations_repository import observe_event

router = APIRouter()


class EventIngestRequest(BaseModel):
    source: str = Field(min_length=1)
    actor: str | None = None
    action: str | None = None
    target: str | None = None
    event_type: str = 'activity'
    service_name: str | None = None
    environment: str | None = None
    severity: str | None = None
    raw_data: dict[str, Any] = Field(default_factory=dict)
    timestamp: str | int | float | None = None


@router.post('/events')
def ingest_event(request: EventIngestRequest):
    text = (
        f"source={request.source}; "
        f"actor={request.actor}; "
        f"action={request.action}; "
        f"target={request.target}; "
        f"type={request.event_type}; "
        f"raw={request.raw_data}"
    )
    embedding = create_embedding(text)

    event_id = insert_event(
        source=request.source,
        actor=request.actor,
        action=request.action,
        target=request.target,
        event_type=request.event_type,
        raw_data=request.raw_data,
        embedding=embedding,
        timestamp=request.timestamp,
        service_name=request.service_name,
        environment=request.environment,
        severity=request.severity,
    )

    observe_event(
        {
            'id': event_id,
            'source': request.source,
            'actor': request.actor,
            'action': request.action,
            'target': request.target,
            'event_type': request.event_type,
            'service_name': request.service_name or request.target,
            'environment': request.environment,
            'severity': request.severity,
            'timestamp': request.timestamp,
        }
    )

    return {
        'status': 'stored',
        'event_id': event_id,
    }
