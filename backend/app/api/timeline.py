from fastapi import APIRouter
from app.services.timeline_service import get_timeline

router = APIRouter()

@router.get('/timeline')
def timeline():
    return get_timeline()