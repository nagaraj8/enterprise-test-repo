import json
import numpy as np

from sqlalchemy import text
from app.database.db import engine
from app.services.embedding_service import create_embedding

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)

    return np.dot(a, b) / (
        np.linalg.norm(a)
        * np.linalg.norm(b)
    )

def semantic_search(query: str):
    query_embedding = create_embedding(query)

    with engine.connect() as conn:
        result = conn.execute(
            text(
                '''
                SELECT *
                FROM events
                WHERE embedding IS NOT NULL
                '''
            )
        )

        rows = result.fetchall()

        similarities = []

        for row in rows:
            embedding = json.loads(row.embedding)

            score = cosine_similarity(
                query_embedding,
                embedding
            )

            similarities.append(
                {
                    'score': float(score),
                    'actor': row.actor,
                    'action': row.action,
                    'target': row.target,
                    'source': row.source
                }
            )

        similarities.sort(
            key=lambda x: x['score'],
            reverse=True
        )

        return similarities[:5]