from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.services.embedding_service import create_embedding
from app.services.event_repository import insert_event
from app.services.operations_repository import observe_event

router = APIRouter()


def extract_slack_timestamp(payload: dict, event: dict):
    return (
        event.get("event_ts")
        or event.get("ts")
        or payload.get("event_time")
    )

@router.post("/slack/events")
async def slack_events(request: Request):

    payload = await request.json()

    # Slack verification
    if payload.get("type") == "url_verification":

        return JSONResponse(
            content={
                "challenge": payload.get("challenge")
            },
            status_code=200
        )

    event = payload.get("event", {})

    event_type = event.get("type")

    user = event.get("user", "unknown")
    text_message = event.get("text", "")
    channel = event.get("channel", "unknown")

    event_text = f"""
    Slack message:
    user={user}
    message={text_message}
    channel={channel}
    """

    embedding = create_embedding(event_text)

    if text_message:
        event_id = insert_event(
            source="slack",
            actor=user,
            action=text_message,
            target=channel,
            event_type=event_type or "slack_message",
            raw_data=payload,
            embedding=embedding,
            timestamp=extract_slack_timestamp(payload, event),
        )
        observe_event(
            {
                "id": event_id,
                "source": "slack",
                "actor": user,
                "action": text_message,
                "target": channel,
                "event_type": event_type or "slack_message",
                "timestamp": extract_slack_timestamp(payload, event),
            }
        )

    return JSONResponse(
        content={
            "status": "ok"
        },
        status_code=200
    )
