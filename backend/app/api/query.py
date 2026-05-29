from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.services.ai_service import ask_ai

router = APIRouter()

class QueryRequest(BaseModel):
    query: str = Field(min_length=1)

@router.post('/query')
def query_ai(request: QueryRequest):
    answer = ask_ai(request.query)

    return {
        'answer': answer
    }
