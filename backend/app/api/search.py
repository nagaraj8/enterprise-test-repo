from fastapi import APIRouter
from pydantic import BaseModel

from app.services.search_service import semantic_search

router = APIRouter()

class SearchRequest(BaseModel):
    query: str

@router.post('/search')
def search(request: SearchRequest):
    results = semantic_search(
        request.query
    )

    return results