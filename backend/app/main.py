import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.incidents import router as incidents_router
from app.api.events import router as events_router
from app.api.overview import router as overview_router
from app.api.query import router as query_router
from app.api.github import router as github_router
from app.api.slack import router as slack_router
from app.api.timeline import router as timeline_router
from app.api.reasoning import router as reasoning_router
from app.api.search import router as search_router
from app.database.schema import ensure_local_schema

app = FastAPI(
    title='Enterprise Decision Brain API',
    version='1.0.0',
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        'CORS_ALLOW_ORIGINS',
        'http://localhost:3000,http://127.0.0.1:3000'
    ).split(',')
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(incidents_router)
app.include_router(events_router)
app.include_router(overview_router)
app.include_router(query_router)
app.include_router(github_router)
app.include_router(slack_router)
app.include_router(timeline_router)
app.include_router(reasoning_router)
app.include_router(search_router)


@app.on_event('startup')
def startup():
    ensure_local_schema()


@app.get('/')
def root():
    return {
        'message': 'Enterprise Decision Brain API Running'
    }


@app.get('/health')
def health():
    return {
        'status': 'ok'
    }
