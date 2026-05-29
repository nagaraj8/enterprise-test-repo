from sqlalchemy import text

from app.database.db import engine


INCIDENT_FIELDS = """
    id,
    title,
    summary,
    severity,
    status,
    priority,
    service_name,
    owner,
    environment,
    impact,
    correlation_key,
    ai_summary,
    risk_score,
    detected_at,
    acknowledged_at,
    resolved_at,
    last_seen_at,
    created_at,
    updated_at
"""


def _row_to_incident(row) -> dict:
    mapping = row._mapping

    return {
        "id": mapping.get("id"),
        "title": mapping.get("title"),
        "summary": mapping.get("summary"),
        "severity": mapping.get("severity"),
        "status": mapping.get("status") or "open",
        "priority": mapping.get("priority") or "p3",
        "service_name": mapping.get("service_name"),
        "owner": mapping.get("owner"),
        "environment": mapping.get("environment"),
        "impact": mapping.get("impact"),
        "correlation_key": mapping.get("correlation_key"),
        "ai_summary": mapping.get("ai_summary"),
        "risk_score": mapping.get("risk_score") or 50,
        "detected_at": str(mapping.get("detected_at")) if mapping.get("detected_at") else None,
        "acknowledged_at": str(mapping.get("acknowledged_at")) if mapping.get("acknowledged_at") else None,
        "resolved_at": str(mapping.get("resolved_at")) if mapping.get("resolved_at") else None,
        "last_seen_at": str(mapping.get("last_seen_at")) if mapping.get("last_seen_at") else None,
        "created_at": str(mapping.get("created_at")) if mapping.get("created_at") else None,
        "updated_at": str(mapping.get("updated_at")) if mapping.get("updated_at") else None,
        "event_count": mapping.get("event_count", 0),
    }


def create_incident(
    title: str,
    summary: str,
    severity: str = "medium",
    status: str = "open",
    ai_summary: str | None = None,
    risk_score: int = 50,
    priority: str = "p3",
    service_name: str | None = None,
    owner: str | None = None,
    environment: str | None = None,
    impact: str | None = None,
    correlation_key: str | None = None,
):

    with engine.begin() as conn:

        result = conn.execute(
            text(
                """
                INSERT INTO incidents (
                    title,
                    summary,
                    severity,
                    status,
                    priority,
                    service_name,
                    owner,
                    environment,
                    impact,
                    correlation_key,
                    ai_summary,
                    risk_score
                )
                VALUES (
                    :title,
                    :summary,
                    :severity,
                    :status,
                    :priority,
                    :service_name,
                    :owner,
                    :environment,
                    :impact,
                    :correlation_key,
                    :ai_summary,
                    :risk_score
                )
                RETURNING id
                """
            ),
            {
                "title": title,
                "summary": summary,
                "severity": severity,
                "status": status,
                "priority": priority,
                "service_name": service_name,
                "owner": owner,
                "environment": environment,
                "impact": impact,
                "correlation_key": correlation_key,
                "ai_summary": ai_summary,
                "risk_score": risk_score,
            },
        )

        row = result.fetchone()

        incident_id = row[0]

        conn.execute(
            text(
                """
                INSERT INTO incident_status_history (
                    incident_id,
                    from_status,
                    to_status,
                    actor,
                    reason
                )
                VALUES (
                    :incident_id,
                    NULL,
                    :status,
                    'system',
                    'Incident created'
                )
                """
            ),
            {
                "incident_id": incident_id,
                "status": status,
            },
        )

        return incident_id


def find_incident_for_event(event_id: int) -> int | None:
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT incident_id
                FROM incident_events
                WHERE event_id = :event_id
                LIMIT 1
                """
            ),
            {"event_id": event_id},
        ).fetchone()

    return row[0] if row else None


def find_incident_by_correlation_key(correlation_key: str | None) -> int | None:
    if not correlation_key:
        return None

    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT id
                FROM incidents
                WHERE correlation_key = :correlation_key
                LIMIT 1
                """
            ),
            {"correlation_key": correlation_key},
        ).fetchone()

    return row[0] if row else None


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
                SELECT
                    incidents.*,
                    COUNT(incident_events.event_id) AS event_count
                FROM incidents
                LEFT JOIN incident_events
                    ON incident_events.incident_id = incidents.id
                GROUP BY incidents.id
                ORDER BY created_at DESC
                """
            )
        )

        return [
            _row_to_incident(row)
            for row in result.fetchall()
        ]


def get_incident(incident_id: int) -> dict | None:
    with engine.connect() as conn:
        row = conn.execute(
            text(
                f"""
                SELECT
                    incidents.*,
                    COUNT(incident_events.event_id) AS event_count
                FROM incidents
                LEFT JOIN incident_events
                    ON incident_events.incident_id = incidents.id
                WHERE incidents.id = :incident_id
                GROUP BY incidents.id
                """
            ),
            {"incident_id": incident_id},
        ).fetchone()

    return _row_to_incident(row) if row else None


def get_incident_events(incident_id: int) -> list[dict]:
    from app.services.event_repository import _row_to_event

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT events.*
                FROM events
                JOIN incident_events
                    ON incident_events.event_id = events.id
                WHERE incident_events.incident_id = :incident_id
                ORDER BY events.timestamp DESC, events.id DESC
                """
            ),
            {"incident_id": incident_id},
        ).fetchall()

    return [_row_to_event(row) for row in rows]


def update_incident_summary(incident_id: int, ai_summary: str, risk_score: int) -> None:
    updated_at_expr = "datetime('now')" if engine.dialect.name == "sqlite" else "CURRENT_TIMESTAMP"

    with engine.begin() as conn:
        conn.execute(
            text(
                f"""
                UPDATE incidents
                SET ai_summary = :ai_summary,
                    risk_score = :risk_score,
                    last_seen_at = {updated_at_expr},
                    updated_at = {updated_at_expr}
                WHERE id = :incident_id
                """
            ),
            {
                "incident_id": incident_id,
                "ai_summary": ai_summary,
                "risk_score": risk_score,
            },
        )


def touch_incident(
    incident_id: int,
    risk_score: int | None = None,
    severity: str | None = None,
) -> None:
    updated_at_expr = "datetime('now')" if engine.dialect.name == "sqlite" else "CURRENT_TIMESTAMP"

    with engine.begin() as conn:
        conn.execute(
            text(
                f"""
                UPDATE incidents
                SET risk_score = CASE
                        WHEN :risk_score IS NULL THEN risk_score
                        WHEN risk_score > :risk_score THEN risk_score
                        ELSE :risk_score
                    END,
                    severity = COALESCE(:severity, severity),
                    last_seen_at = {updated_at_expr},
                    updated_at = {updated_at_expr}
                WHERE id = :incident_id
                """
            ),
            {
                "incident_id": incident_id,
                "risk_score": risk_score,
                "severity": severity,
            },
        )
