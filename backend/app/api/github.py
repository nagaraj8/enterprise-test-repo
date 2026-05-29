from fastapi import APIRouter, Request
from sqlalchemy import text
from app.database.db import engine
from sqlalchemy.dialects.postgresql import JSONB
from app.services.embedding_service import create_embedding
import json

router = APIRouter()

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

    print(event_text)

    print(len(embedding))

    with engine.connect() as conn:
        query = text(
            '''
            INSERT INTO events (
                source,
                actor,
                action,
                target,
                event_type,
                raw_data,
                embedding
            )
            VALUES (
                :source,
                :actor,
                :action,
                :target,
                :event_type,
                :raw_data,
                :embedding
            )
            '''
        ).bindparams(
            raw_data=JSONB,
            embedding=JSONB
        )

        conn.execute(
            query,
            {
                'source': 'github',
                'actor': actor,
                'action': action,
                'target': repository,
                'event_type': 'github_event',
                'raw_data': payload,
                'embedding': embedding
            }
        )

        conn.commit()

    return {
        'status': 'stored'
    }