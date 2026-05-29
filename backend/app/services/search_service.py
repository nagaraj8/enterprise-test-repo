import math

from app.services.embedding_service import create_embedding
from app.services.event_repository import list_events

def cosine_similarity(a, b):
    if not a or not b or len(a) != len(b):
        return 0

    try:
        left = [float(item) for item in a]
        right = [float(item) for item in b]
    except (TypeError, ValueError):
        return 0

    denominator = math.sqrt(sum(item * item for item in left)) * math.sqrt(
        sum(item * item for item in right)
    )

    if denominator == 0:
        return 0

    return sum(
        left_item * right_item
        for left_item, right_item in zip(left, right)
    ) / denominator


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
