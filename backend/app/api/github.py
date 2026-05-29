from fastapi import APIRouter, Request
from app.services.embedding_service import create_embedding
from app.services.event_repository import insert_event

router = APIRouter()


def extract_github_timestamp(payload: dict):
    head_commit = payload.get('head_commit') or {}
    repository = payload.get('repository') or {}

    return (
        payload.get('created_at')
        or payload.get('updated_at')
        or head_commit.get('timestamp')
        or repository.get('pushed_at')
    )

@router.post('/github/webhook')
async def github_webhook(request: Request):
    payload = await request.json()

    actor = payload.get('sender', {}).get('login')
    action = payload.get('action')

    

    repository = payload.get(
        'repository',
        {}
    ).get('name')

    event_text = f'''
    GitHub event:
    actor={actor}
    action={action}
    repository={repository}
    '''
    embedding = create_embedding(event_text)

    insert_event(
        source='github',
        actor=actor,
        action=action,
        target=repository,
        event_type='github_event',
        raw_data=payload,
        embedding=embedding,
        timestamp=extract_github_timestamp(payload),
    )

    return {
        'status': 'stored'
    }
