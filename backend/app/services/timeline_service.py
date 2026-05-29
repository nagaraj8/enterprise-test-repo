from sqlalchemy import text
from app.database.db import engine

def get_timeline():
    with engine.connect() as conn:
        result = conn.execute(
            text(
                '''
                SELECT *
                FROM events
                ORDER BY timestamp DESC
                LIMIT 50
                '''
            )
        )

        rows = result.fetchall()

        timeline = []

        for row in rows:
            timeline.append(
                {
                    'source': row.source,
                    'actor': row.actor,
                    'action': row.action,
                    'target': row.target,
                    'timestamp': str(row.timestamp)
                }
            )

        return timeline