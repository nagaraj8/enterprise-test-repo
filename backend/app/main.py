from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.incidents import router as incidents_router
from app.api.query import router as query_router
from app.api.github import router as github_router
from app.api.slack import router as slack_router
from app.api.timeline import router as timeline_router
from app.api.reasoning import router as reasoning_router
from app.api.search import router as search_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(incidents_router)
app.include_router(query_router)
app.include_router(github_router)
app.include_router(slack_router)
app.include_router(timeline_router)
app.include_router(reasoning_router)
app.include_router(search_router)

@app.get('/')
def root():
    return {
        'message': 'Enterprise Decision Brain API Running'
    }