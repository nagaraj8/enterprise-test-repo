import json
import hashlib
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from app.database.db import engine


EVENT_FIELDS = '''
    id,
    source,
    actor,
    action,
    target,
    event_type,
    service_name,
    environment,
    severity,
    fingerprint,
    raw_data,
    embedding,
    timestamp,
    ingested_at
'''


def _clean_limit(limit: int, default: int = 50, maximum: int = 200) -> int:
    if limit <= 0:
        return default

    return min(limit, maximum)


def _row_to_event(row: Any, include_embedding: bool = False) -> dict[str, Any]:
    mapping = row._mapping
    raw_data = mapping.get('raw_data')
    parsed_raw_data = parse_raw_data(raw_data)

    event = {
        'id': mapping.get('id'),
        'source': mapping.get('source'),
        'actor': mapping.get('actor'),
        'action': mapping.get('action'),
        'target': mapping.get('target'),
        'event_type': mapping.get('event_type'),
        'service_name': mapping.get('service_name'),
        'environment': mapping.get('environment'),
        'severity': mapping.get('severity'),
        'fingerprint': mapping.get('fingerprint'),
        'timestamp': str(mapping.get('timestamp')) if mapping.get('timestamp') else None,
        'ingested_at': str(mapping.get('ingested_at')) if mapping.get('ingested_at') else None,
        'summary': summarize_event(mapping),
    }

    if include_embedding:
        event['embedding'] = parse_embedding(mapping.get('embedding'))

    if parsed_raw_data is not None:
        event['raw_data'] = parsed_raw_data

    return event


def parse_raw_data(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return None

        return parsed if isinstance(parsed, dict) else None

    return None


def summarize_event(row: Any) -> str:
    source = row.get('source') or 'unknown source'
    actor = row.get('actor') or 'unknown actor'
    action = row.get('action') or 'recorded activity'
    target = row.get('target') or 'unknown target'

    return f'{actor} {action} on {target} from {source}.'


def build_event_fingerprint(
    source: str,
    actor: str | None,
    action: str | None,
    target: str | None,
    event_type: str | None,
) -> str:
    normalized = '|'.join(
        (value or '').strip().lower()
        for value in (source, actor, action, target, event_type)
    )

    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:24]


def parse_embedding(value: Any) -> list[float] | None:
    if value is None:
        return None

    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return None

    if isinstance(value, tuple):
        value = list(value)

    if not isinstance(value, list):
        return None

    try:
        return [float(item) for item in value]
    except (TypeError, ValueError):
        return None


def normalize_event_timestamp(value: Any = None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)

    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)

    if isinstance(value, str):
        stripped = value.strip()

        if not stripped:
            return datetime.now(timezone.utc)

        try:
            return datetime.fromtimestamp(float(stripped), tz=timezone.utc)
        except ValueError:
            pass

        try:
            parsed = datetime.fromisoformat(stripped.replace('Z', '+00:00'))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return datetime.now(timezone.utc)

    return datetime.now(timezone.utc)


def list_events(
    limit: int = 50,
    source: str | None = None,
    query: str | None = None,
    include_embedding: bool = False,
) -> list[dict[str, Any]]:
    filters = []
    params: dict[str, Any] = {
        'limit': _clean_limit(limit),
    }

    if source:
        filters.append('LOWER(source) = LOWER(:source)')
        params['source'] = source

    if query:
        filters.append(
            '''
            (
                LOWER(COALESCE(source, '')) LIKE LOWER(:query)
                OR LOWER(COALESCE(actor, '')) LIKE LOWER(:query)
                OR LOWER(COALESCE(action, '')) LIKE LOWER(:query)
                OR LOWER(COALESCE(target, '')) LIKE LOWER(:query)
                OR LOWER(COALESCE(event_type, '')) LIKE LOWER(:query)
                OR LOWER(COALESCE(service_name, '')) LIKE LOWER(:query)
                OR LOWER(COALESCE(environment, '')) LIKE LOWER(:query)
                OR LOWER(COALESCE(severity, '')) LIKE LOWER(:query)
                OR LOWER(COALESCE(CAST(raw_data AS TEXT), '')) LIKE LOWER(:query)
            )
            '''
        )
        params['query'] = f'%{query}%'

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ''

    with engine.connect() as conn:
        result = conn.execute(
            text(
                f'''
                SELECT {EVENT_FIELDS}
                FROM events
                {where_clause}
                ORDER BY
                    CASE WHEN timestamp IS NULL THEN 1 ELSE 0 END ASC,
                    timestamp DESC,
                    id DESC
                LIMIT :limit
                '''
            ),
            params,
        )

        return [
            _row_to_event(row, include_embedding=include_embedding)
            for row in result.fetchall()
        ]


def insert_event(
    source: str,
    actor: str | None,
    action: str | None,
    target: str | None,
    event_type: str,
    raw_data: dict[str, Any],
    embedding: list[float] | None = None,
    timestamp: Any = None,
    service_name: str | None = None,
    environment: str | None = None,
    severity: str | None = None,
    fingerprint: str | None = None,
) -> int:
    event_timestamp = normalize_event_timestamp(timestamp)
    resolved_service_name = service_name or target
    resolved_fingerprint = fingerprint or build_event_fingerprint(
        source,
        actor,
        action,
        target,
        event_type,
    )

    with engine.begin() as conn:
        result = conn.execute(
            text(
                '''
                INSERT INTO events (
                    source,
                    actor,
                    action,
                    target,
                    event_type,
                    service_name,
                    environment,
                    severity,
                    fingerprint,
                    raw_data,
                    embedding,
                    timestamp
                )
                VALUES (
                    :source,
                    :actor,
                    :action,
                    :target,
                    :event_type,
                    :service_name,
                    :environment,
                    :severity,
                    :fingerprint,
                    :raw_data,
                    :embedding,
                    :timestamp
                )
                RETURNING id
                '''
            ),
            {
                'source': source,
                'actor': actor,
                'action': action,
                'target': target,
                'event_type': event_type,
                'service_name': resolved_service_name,
                'environment': environment,
                'severity': severity,
                'fingerprint': resolved_fingerprint,
                'raw_data': json.dumps(raw_data),
                'embedding': json.dumps(embedding) if embedding else None,
                'timestamp': event_timestamp,
            },
        )

        return result.fetchone()[0]


def get_event_stats() -> dict[str, Any]:
    with engine.connect() as conn:
        total = conn.execute(
            text('SELECT COUNT(*) FROM events')
        ).scalar_one()

        latest = conn.execute(
            text('SELECT MAX(timestamp) FROM events')
        ).scalar_one()

        sources = conn.execute(
            text(
                '''
                SELECT source, COUNT(*) AS count
                FROM events
                GROUP BY source
                ORDER BY count DESC, source ASC
                '''
            )
        ).fetchall()

        open_incidents = conn.execute(
            text(
                """
                SELECT COUNT(*)
                FROM incidents
                WHERE COALESCE(status, 'open') NOT IN ('resolved', 'closed')
                """
            )
        ).scalar_one()

        services = conn.execute(
            text('SELECT COUNT(*) FROM services')
        ).scalar_one()

        deployments_last_24h = conn.execute(
            text(
                '''
                SELECT COUNT(*)
                FROM deployments
                WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '1 day'
                '''
            )
        ).scalar_one() if engine.dialect.name != 'sqlite' else conn.execute(
            text(
                '''
                SELECT COUNT(*)
                FROM deployments
                WHERE created_at >= datetime('now', '-1 day')
                '''
            )
        ).scalar_one()

        last_24h = conn.execute(
            text(
                '''
                SELECT COUNT(*)
                FROM events
                WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '1 day'
                '''
            )
        ).scalar_one() if engine.dialect.name != 'sqlite' else conn.execute(
            text(
                '''
                SELECT COUNT(*)
                FROM events
                WHERE timestamp >= datetime('now', '-1 day')
                '''
            )
        ).scalar_one()

    return {
        'total_events': total,
        'events_last_24h': last_24h,
        'open_incidents': open_incidents,
        'services': services,
        'deployments_last_24h': deployments_last_24h,
        'latest_event_timestamp': str(latest) if latest else None,
        'sources': [
            {
                'source': row._mapping.get('source'),
                'count': row._mapping.get('count'),
            }
            for row in sources
        ],
    }


def list_sources() -> list[str]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                '''
                SELECT DISTINCT source
                FROM events
                WHERE source IS NOT NULL AND source != ''
                ORDER BY source ASC
                '''
            )
        ).fetchall()

    return [row._mapping.get('source') for row in rows if row._mapping.get('source')]
