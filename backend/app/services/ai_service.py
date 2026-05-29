import os

from dotenv import load_dotenv
from openai import OpenAI

from app.services.timeline_service import get_timeline

load_dotenv()

client = None


def get_client():
    global client
    api_key = os.getenv('OPENAI_API_KEY')

    if not api_key:
        return None

    if client is None:
        client = OpenAI(
            api_key=api_key
        )

    return client


def build_context(limit: int = 12) -> str:
    events = get_timeline(limit=limit)

    if not events:
        return 'No operational events are currently stored.'

    lines = []

    for event in events:
        lines.append(
            (
                f"- time={event.get('timestamp')}; "
                f"source={event.get('source')}; "
                f"actor={event.get('actor')}; "
                f"action={event.get('action')}; "
                f"target={event.get('target')}; "
                f"type={event.get('event_type')}"
            )
        )

    return '\n'.join(lines)

def ask_ai(question: str):
    context = build_context()
    openai_client = get_client()

    if openai_client is None:
        return (
            "AI provider is not configured because OPENAI_API_KEY is missing. "
            "Recent activity context is still available for manual review:\n\n"
            f"{context}"
        )

    response = openai_client.chat.completions.create(
        model=os.getenv('OPENAI_MODEL', 'gpt-4.1-mini'),
        messages=[
            {
                'role': 'system',
                'content': (
                    'You are an enterprise operational intelligence AI. '
                    'Answer from the provided activity context first. '
                    'Call out uncertainty and recommend the next concrete checks.'
                )
            },
            {
                'role': 'user',
                'content': (
                    f'Question: {question}\n\n'
                    f'Recent activity context:\n{context}'
                )
            }
        ]
    )

    return response.choices[0].message.content
