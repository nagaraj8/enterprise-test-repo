from fastapi import APIRouter, Query
from app.services.timeline_service import get_timeline

router = APIRouter()

@router.get('/timeline')
def timeline(
    limit: int = Query(default=50, ge=1, le=200),
    source: str | None = None,
    q: str | None = None,
):
    return get_timeline(
        limit=limit,
        source=source,
        query=q,
    )


@router.get('/history')
def history(
    limit: int = Query(default=50, ge=1, le=200),
    source: str | None = None,
    q: str | None = None,
):
    return get_timeline(
        limit=limit,
        source=source,
        query=q,
    )
