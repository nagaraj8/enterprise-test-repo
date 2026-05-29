from fastapi import APIRouter
from pydantic import BaseModel
from app.services.ai_service import ask_ai

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

@router.post('/query')
def query_ai(request: QueryRequest):
    answer = ask_ai(request.query)

    return {
        'answer': answer
    }