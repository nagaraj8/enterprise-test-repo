from typing import Any

from sqlalchemy import text

from app.database.db import engine


DEPLOYMENT_TERMS = {
    "deploy",
    "deployment",
    "release",
    "rollout",
    "merge",
    "push",
}


def _now_expr() -> str:
    return "datetime('now')" if engine.dialect.name == "sqlite" else "CURRENT_TIMESTAMP"


def _row_to_dict(row) -> dict[str, Any]:
    return {
        key: str(value) if key.endswith("_at") and value is not None else value
        for key, value in row._mapping.items()
    }


def upsert_service(
    name: str | None,
    owner: str | None = None,
    environment: str | None = None,
    health_score: int = 100,
) -> None:
    if not name:
        return

    now_expr = _now_expr()

    with engine.begin() as conn:
        conn.execute(
            text(
                f"""
                INSERT INTO services (
                    name,
                    owner,
                    environment,
                    health_score,
                    last_seen_at,
                    updated_at
                )
                VALUES (
                    :name,
                    :owner,
                    :environment,
                    :health_score,
                    {now_expr},
                    {now_expr}
                )
                ON CONFLICT(name) DO UPDATE SET
                    owner = COALESCE(excluded.owner, services.owner),
                    environment = COALESCE(excluded.environment, services.environment),
                    health_score = CASE
                        WHEN services.health_score < excluded.health_score
                        THEN services.health_score
                        ELSE excluded.health_score
                    END,
                    last_seen_at = {now_expr},
                    updated_at = {now_expr}
                """
            ),
            {
                "name": name,
                "owner": owner,
                "environment": environment,
                "health_score": health_score,
            },
        )


def record_deployment(
    service_name: str | None,
    environment: str | None,
    version: str | None,
    status: str,
    risk_score: int,
    actor: str | None,
    source: str | None,
    source_event_id: int | None,
    started_at: str | None = None,
    finished_at: str | None = None,
) -> None:
    if not service_name:
        return

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO deployments (
                    service_name,
                    environment,
                    version,
                    status,
                    risk_score,
                    actor,
                    source,
                    source_event_id,
                    started_at,
                    finished_at
                )
                VALUES (
                    :service_name,
                    :environment,
                    :version,
                    :status,
                    :risk_score,
                    :actor,
                    :source,
                    :source_event_id,
                    :started_at,
                    :finished_at
                )
                """
            ),
            {
                "service_name": service_name,
                "environment": environment,
                "version": version,
                "status": status,
                "risk_score": risk_score,
                "actor": actor,
                "source": source,
                "source_event_id": source_event_id,
                "started_at": started_at,
                "finished_at": finished_at,
            },
        )


def record_event_correlation(
    source_event_id: int,
    target_event_id: int,
    correlation_type: str,
    confidence: float,
    reason: str,
) -> None:
    if source_event_id == target_event_id:
        return

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO event_correlations (
                    source_event_id,
                    target_event_id,
                    correlation_type,
                    confidence,
                    reason
                )
                VALUES (
                    :source_event_id,
                    :target_event_id,
                    :correlation_type,
                    :confidence,
                    :reason
                )
                ON CONFLICT(source_event_id, target_event_id, correlation_type)
                DO UPDATE SET
                    confidence = excluded.confidence,
                    reason = excluded.reason
                """
            ),
            {
                "source_event_id": source_event_id,
                "target_event_id": target_event_id,
                "correlation_type": correlation_type,
                "confidence": confidence,
                "reason": reason,
            },
        )


def observe_event(event: dict[str, Any]) -> None:
    service_name = event.get("service_name") or event.get("target")
    action = (event.get("action") or "").lower()
    event_type = (event.get("event_type") or "").lower()
    event_id = event.get("id")

    health_score = 65 if event.get("severity") in {"critical", "high"} else 100
    upsert_service(
        service_name,
        environment=event.get("environment"),
        health_score=health_score,
    )

    if any(term in action or term in event_type for term in DEPLOYMENT_TERMS):
        status = "failed" if any(term in action for term in ("failed", "rollback", "error")) else "completed"
        record_deployment(
            service_name=service_name,
            environment=event.get("environment"),
            version=event.get("fingerprint"),
            status=status,
            risk_score=event.get("risk_score", 20),
            actor=event.get("actor"),
            source=event.get("source"),
            source_event_id=event_id,
            started_at=event.get("timestamp"),
            finished_at=event.get("timestamp"),
        )


def list_services(limit: int = 50) -> list[dict[str, Any]]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT *
                FROM services
                ORDER BY health_score ASC, last_seen_at DESC
                LIMIT :limit
                """
            ),
            {"limit": limit},
        ).fetchall()

    return [_row_to_dict(row) for row in rows]


def list_deployments(
    service_name: str | None = None,
    limit: int = 25,
) -> list[dict[str, Any]]:
    filters = []
    params: dict[str, Any] = {"limit": limit}

    if service_name:
        filters.append("LOWER(service_name) = LOWER(:service_name)")
        params["service_name"] = service_name

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                f"""
                SELECT *
                FROM deployments
                {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit
                """
            ),
            params,
        ).fetchall()

    return [_row_to_dict(row) for row in rows]


def get_incident_history(incident_id: int) -> list[dict[str, Any]]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT *
                FROM incident_status_history
                WHERE incident_id = :incident_id
                ORDER BY created_at DESC
                """
            ),
            {"incident_id": incident_id},
        ).fetchall()

    return [_row_to_dict(row) for row in rows]


def get_incident_notes(incident_id: int) -> list[dict[str, Any]]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT *
                FROM incident_notes
                WHERE incident_id = :incident_id
                ORDER BY created_at DESC
                """
            ),
            {"incident_id": incident_id},
        ).fetchall()

    return [_row_to_dict(row) for row in rows]
