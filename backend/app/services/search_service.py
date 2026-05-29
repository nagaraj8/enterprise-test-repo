import numpy as np

from app.services.embedding_service import create_embedding
from app.services.event_repository import list_events

def cosine_similarity(a, b):
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)

    denominator = np.linalg.norm(a) * np.linalg.norm(b)

    if denominator == 0:
        return 0

    return np.dot(a, b) / denominator


def semantic_search(
    query: str,
    limit: int = 8,
    source: str | None = None,
):
    query_embedding = create_embedding(query)
    rows = list_events(
        limit=200,
        source=source,
        include_embedding=True,
    )

    similarities = []

    for row in rows:
        embedding = row.pop('embedding', None)

        if not embedding:
            continue

        score = cosine_similarity(
            query_embedding,
            embedding
        )

        similarities.append(
            {
                **row,
                'score': float(score),
            }
        )

    similarities.sort(
        key=lambda item: item['score'],
        reverse=True
    )

    return similarities[:limit]
