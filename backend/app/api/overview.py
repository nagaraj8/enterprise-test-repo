from fastapi import APIRouter

from app.services.event_repository import get_event_stats, list_sources

router = APIRouter()


@router.get('/overview')
def overview():
    return get_event_stats()


@router.get('/sources')
def sources():
    return {
        'sources': list_sources()
    }
