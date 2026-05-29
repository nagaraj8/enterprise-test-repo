from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.search_service import semantic_search

router = APIRouter()

class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=8, ge=1, le=25)
    source: str | None = None

@router.post('/search')
def search(request: SearchRequest):
    results = semantic_search(
        query=request.query,
        limit=request.limit,
        source=request.source,
    )

    return results
