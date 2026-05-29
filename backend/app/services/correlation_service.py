from app.services.timeline_service import get_timeline

def correlate_events():
    timeline = get_timeline()

    correlations = []

    for i in range(len(timeline) - 1):
        current_event = timeline[i]
        next_event = timeline[i + 1]

        if (
            current_event['source'] == 'github'
            and next_event['source'] == 'slack'
        ):
            correlations.append({
                'cause': current_event,
                'effect': next_event
            })

    return correlations