from app.services.timeline_service import get_timeline

def analyze_incident(question: str):
    timeline = get_timeline()

    findings = []

    for event in timeline:
        if (
            event['source'] == 'github'
            and event['action']
        ):
            findings.append(
                f"Recent GitHub action: {event['action']} by {event['actor']}"
            )

    return {
        'question': question,
        'possible_root_cause': findings[:5],
        'confidence': 'medium'
    }