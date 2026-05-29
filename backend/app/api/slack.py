from fastapi import APIRouter
from app.services.slack_service import fetch_channels

router = APIRouter()

@router.get('/slack/channels')
def get_channels():
    return fetch_channels()