from sqlalchemy import text

from app.database.db import engine


def create_incident(
    title: str,
    summary: str,
    severity: str = "medium",
):

    with engine.begin() as conn:

        result = conn.execute(
            text(
                """
                INSERT INTO incidents (
                    title,
                    summary,
                    severity
                )
                VALUES (
                    :title,
                    :summary,
                    :severity
                )
                RETURNING id
                """
            ),
            {
                "title": title,
                "summary": summary,
                "severity": severity,
            },
        )

        row = result.fetchone()

        return row[0]


def link_event_to_incident(
    incident_id: int,
    event_id: int,
):

    with engine.begin() as conn:

        conn.execute(
            text(
                """
                INSERT INTO incident_events (
                    incident_id,
                    event_id
                )
                VALUES (
                    :incident_id,
                    :event_id
                )
                ON CONFLICT DO NOTHING
                """
            ),
            {
                "incident_id": incident_id,
                "event_id": event_id,
            },
        )


def list_incidents():

    with engine.connect() as conn:

        result = conn.execute(
            text(
                """
                SELECT *
                FROM incidents
                ORDER BY created_at DESC
                """
            )
        )

        return [
            dict(row._mapping)
            for row in result.fetchall()
        ]
