from fastapi import APIRouter
from pydantic import BaseModel
from app.services.reasoning_service import analyze_incident

router = APIRouter()

class IncidentQuestion(BaseModel):
    question: str

@router.post('/reason')
def reason(request: IncidentQuestion):
    return analyze_incident(request.question)