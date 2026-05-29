from app.services.event_repository import list_events


def get_timeline(
    limit: int = 50,
    source: str | None = None,
    query: str | None = None,
):
    return list_events(
        limit=limit,
        source=source,
        query=query,
    )
