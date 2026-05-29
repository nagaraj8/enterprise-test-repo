import hashlib
import math

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

model = None


def get_model():
    global model
    if SentenceTransformer is None:
        return None

    if model is None:
        model = SentenceTransformer(
            'all-MiniLM-L6-v2'
        )

    return model


def _fallback_embedding(text: str, dimensions: int = 96) -> list[float]:
    vector = [0.0] * dimensions

    for token in text.lower().split():
        digest = hashlib.sha256(token.encode('utf-8')).digest()
        index = int.from_bytes(digest[:4], 'big') % dimensions
        direction = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += direction

    norm = math.sqrt(sum(value * value for value in vector))

    if norm == 0:
        return vector

    return [value / norm for value in vector]


def create_embedding(text: str):
    current_model = get_model()

    if current_model is None:
        return _fallback_embedding(text)

    embedding = current_model.encode(text)

    return embedding.tolist()
