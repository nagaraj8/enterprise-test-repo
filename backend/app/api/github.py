from fastapi import APIRouter, Request

from app.services.embedding_service import create_embedding
from app.services.event_repository import insert_event
from app.services.operations_repository import observe_event

router = APIRouter()


def extract_commit_messages(payload: dict) -> str:

    commits = payload.get("commits", [])

    messages = []

    for commit in commits:

        message = commit.get("message")

        if message:
            messages.append(message)

    return " | ".join(messages)


def extract_actor(payload: dict) -> str | None:

    sender = payload.get("sender", {})

    return sender.get("login")


def extract_repository(payload: dict) -> str | None:

    repository = payload.get("repository", {})

    return repository.get("name")


def extract_timestamp(payload: dict):

    head_commit = payload.get("head_commit", {})

    return (
        head_commit.get("timestamp")
        or payload.get("repository", {}).get("updated_at")
    )


def build_action(
    github_event: str,
    payload: dict,
) -> str:

    commit_messages = extract_commit_messages(payload)

    if commit_messages:
        return commit_messages

    payload_action = payload.get("action")

    if payload_action:
        return payload_action

    return github_event


def build_embedding_text(
    actor: str | None,
    repository: str | None,
    action: str | None,
    github_event: str | None,
) -> str:

    return f"""
    GitHub operational event

    actor={actor}
    repository={repository}
    action={action}
    event_type={github_event}
    """


@router.post("/github/webhook")
async def github_webhook(request: Request):

    payload = await request.json()

    github_event = request.headers.get(
        "X-GitHub-Event",
        "github_event"
    )

    actor = extract_actor(payload)

    repository = extract_repository(payload)

    action = build_action(
        github_event,
        payload,
    )

    timestamp = extract_timestamp(payload)

    embedding_text = build_embedding_text(
        actor,
        repository,
        action,
        github_event,
    )

    embedding = create_embedding(
        embedding_text
    )

    print("========== GITHUB EVENT ==========")
    print("EVENT:", github_event)
    print("ACTOR:", actor)
    print("REPOSITORY:", repository)
    print("ACTION:", action)
    print("==================================")

    event_id = insert_event(
        source="github",
        actor=actor,
        action=action,
        target=repository,
        event_type=github_event,
        raw_data=payload,
        embedding=embedding,
        timestamp=timestamp,
        service_name=repository,
        environment=payload.get("deployment", {}).get("environment"),
    )

    observe_event(
        {
            "id": event_id,
            "source": "github",
            "actor": actor,
            "action": action,
            "target": repository,
            "event_type": github_event,
            "service_name": repository,
            "environment": payload.get("deployment", {}).get("environment"),
            "timestamp": timestamp,
        }
    )

    return {
        "status": "stored",
        "event_id": event_id,
    }
