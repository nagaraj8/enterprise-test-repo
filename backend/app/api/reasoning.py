from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.services.reasoning_service import analyze_incident

router = APIRouter()

class IncidentQuestion(BaseModel):
    question: str = Field(min_length=1)

@router.post('/reason')
def reason(request: IncidentQuestion):
    return analyze_incident(request.question)
