from sqlalchemy import text

from app.database.db import engine


def _column_exists(conn, table_name: str, column_name: str, dialect: str) -> bool:
    if dialect == 'sqlite':
        rows = conn.execute(text(f'PRAGMA table_info({table_name})')).fetchall()

        return any(row._mapping.get('name') == column_name for row in rows)

    return bool(
        conn.execute(
            text(
                '''
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = :table_name
                    AND column_name = :column_name
                LIMIT 1
                '''
            ),
            {
                'table_name': table_name,
                'column_name': column_name,
            },
        ).fetchone()
    )


def _add_column_if_missing(
    conn,
    table_name: str,
    column_name: str,
    column_definition: str,
    dialect: str,
) -> None:
    if _column_exists(conn, table_name, column_name, dialect):
        return

    conn.execute(
        text(
            f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}'
        )
    )


def _backfill_operational_records(conn) -> None:
    conn.execute(
        text(
            """
            UPDATE events
            SET service_name = target
            WHERE (service_name IS NULL OR service_name = '')
                AND target IS NOT NULL
                AND target != ''
            """
        )
    )
    conn.execute(
        text(
            """
            INSERT INTO services (
                name,
                environment,
                health_score,
                last_seen_at,
                updated_at
            )
            SELECT
                service_name,
                MAX(environment),
                100,
                MAX(timestamp),
                MAX(timestamp)
            FROM events
            WHERE service_name IS NOT NULL
                AND service_name != ''
            GROUP BY service_name
            ON CONFLICT(name) DO UPDATE SET
                environment = COALESCE(excluded.environment, services.environment),
                last_seen_at = COALESCE(excluded.last_seen_at, services.last_seen_at),
                updated_at = COALESCE(excluded.updated_at, services.updated_at)
            """
        )
    )
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
            SELECT
                service_name,
                environment,
                fingerprint,
                CASE
                    WHEN LOWER(COALESCE(action, '')) LIKE '%failed%'
                        OR LOWER(COALESCE(action, '')) LIKE '%rollback%'
                        OR LOWER(COALESCE(action, '')) LIKE '%error%'
                    THEN 'failed'
                    ELSE 'completed'
                END,
                CASE
                    WHEN LOWER(COALESCE(action, '')) LIKE '%failed%'
                        OR LOWER(COALESCE(action, '')) LIKE '%rollback%'
                    THEN 80
                    ELSE 30
                END,
                actor,
                source,
                id,
                timestamp,
                timestamp
            FROM events
            WHERE service_name IS NOT NULL
                AND service_name != ''
                AND (
                    LOWER(COALESCE(action, '')) LIKE '%deploy%'
                    OR LOWER(COALESCE(action, '')) LIKE '%release%'
                    OR LOWER(COALESCE(action, '')) LIKE '%rollout%'
                    OR LOWER(COALESCE(event_type, '')) LIKE '%deploy%'
                    OR LOWER(COALESCE(event_type, '')) LIKE '%release%'
                )
            ON CONFLICT(source_event_id) DO NOTHING
            """
        )
    )
    conn.execute(
        text(
            """
            UPDATE incidents
            SET service_name = (
                    SELECT events.service_name
                    FROM incident_events
                    JOIN events ON events.id = incident_events.event_id
                    WHERE incident_events.incident_id = incidents.id
                        AND events.service_name IS NOT NULL
                    ORDER BY events.timestamp DESC
                    LIMIT 1
                ),
                environment = (
                    SELECT events.environment
                    FROM incident_events
                    JOIN events ON events.id = incident_events.event_id
                    WHERE incident_events.incident_id = incidents.id
                        AND events.environment IS NOT NULL
                    ORDER BY events.timestamp DESC
                    LIMIT 1
                )
            WHERE service_name IS NULL OR service_name = ''
            """
        )
    )


def _primary_key_type(dialect: str) -> str:
    return 'INTEGER PRIMARY KEY AUTOINCREMENT' if dialect == 'sqlite' else 'SERIAL PRIMARY KEY'


def _timestamp_type(dialect: str) -> str:
    return 'DATETIME' if dialect == 'sqlite' else 'TIMESTAMPTZ'


def ensure_local_schema() -> None:
    dialect = engine.dialect.name
    primary_key_type = _primary_key_type(dialect)
    timestamp_type = _timestamp_type(dialect)
    timestamp_add_type = timestamp_type if dialect == 'sqlite' else f'{timestamp_type} DEFAULT CURRENT_TIMESTAMP'

    with engine.begin() as conn:
        if dialect == 'sqlite':
            conn.execute(
                text(
                    '''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    actor TEXT,
                    action TEXT,
                    target TEXT,
                    event_type TEXT,
                    raw_data TEXT,
                    embedding TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                '''
                )
            )
            conn.execute(
                text(
                    '''
                CREATE INDEX IF NOT EXISTS idx_events_timestamp
                ON events(timestamp DESC)
                '''
                )
            )
            conn.execute(
                text(
                    '''
                CREATE INDEX IF NOT EXISTS idx_events_source
                ON events(source)
                '''
                )
            )
            conn.execute(
                text(
                    '''
                    CREATE TABLE IF NOT EXISTS incidents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        summary TEXT,
                        severity TEXT NOT NULL DEFAULT 'medium',
                        status TEXT NOT NULL DEFAULT 'open',
                        priority TEXT NOT NULL DEFAULT 'p3',
                        service_name TEXT,
                        owner TEXT,
                        environment TEXT,
                        impact TEXT,
                        correlation_key TEXT,
                        ai_summary TEXT,
                        risk_score INTEGER NOT NULL DEFAULT 50,
                        detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        acknowledged_at DATETIME,
                        resolved_at DATETIME,
                        last_seen_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                    '''
                )
            )
            conn.execute(
                text(
                    '''
                    CREATE TABLE IF NOT EXISTS incident_events (
                        incident_id INTEGER NOT NULL,
                        event_id INTEGER NOT NULL,
                        PRIMARY KEY (incident_id, event_id),
                        FOREIGN KEY (incident_id) REFERENCES incidents(id),
                        FOREIGN KEY (event_id) REFERENCES events(id)
                    )
                    '''
                )
            )
        else:
            conn.execute(
                text(
                    '''
                    CREATE TABLE IF NOT EXISTS events (
                        id SERIAL PRIMARY KEY,
                        source TEXT NOT NULL,
                        actor TEXT,
                        action TEXT,
                        target TEXT,
                        event_type TEXT,
                        raw_data TEXT,
                        embedding TEXT,
                        timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    )
                    '''
                )
            )
            conn.execute(
                text(
                    '''
                    CREATE INDEX IF NOT EXISTS idx_events_timestamp
                    ON events(timestamp DESC)
                    '''
                )
            )
            conn.execute(
                text(
                    '''
                    CREATE INDEX IF NOT EXISTS idx_events_source
                    ON events(source)
                    '''
                )
            )
            conn.execute(
                text(
                    '''
                    CREATE TABLE IF NOT EXISTS incidents (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        summary TEXT,
                        severity TEXT NOT NULL DEFAULT 'medium',
                        status TEXT NOT NULL DEFAULT 'open',
                        priority TEXT NOT NULL DEFAULT 'p3',
                        service_name TEXT,
                        owner TEXT,
                        environment TEXT,
                        impact TEXT,
                        correlation_key TEXT,
                        ai_summary TEXT,
                        risk_score INTEGER NOT NULL DEFAULT 50,
                        detected_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        acknowledged_at TIMESTAMPTZ,
                        resolved_at TIMESTAMPTZ,
                        last_seen_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    )
                    '''
                )
            )
            conn.execute(
                text(
                    '''
                    CREATE TABLE IF NOT EXISTS incident_events (
                        incident_id INTEGER NOT NULL REFERENCES incidents(id),
                        event_id INTEGER NOT NULL REFERENCES events(id),
                        PRIMARY KEY (incident_id, event_id)
                    )
                    '''
                )
            )

        _add_column_if_missing(conn, 'events', 'service_name', 'TEXT', dialect)
        _add_column_if_missing(conn, 'events', 'environment', 'TEXT', dialect)
        _add_column_if_missing(conn, 'events', 'severity', 'TEXT', dialect)
        _add_column_if_missing(conn, 'events', 'fingerprint', 'TEXT', dialect)
        _add_column_if_missing(
            conn,
            'events',
            'ingested_at',
            timestamp_add_type,
            dialect,
        )
        _add_column_if_missing(
            conn,
            'incidents',
            'status',
            "TEXT NOT NULL DEFAULT 'open'",
            dialect,
        )
        _add_column_if_missing(
            conn,
            'incidents',
            'ai_summary',
            'TEXT',
            dialect,
        )
        _add_column_if_missing(
            conn,
            'incidents',
            'risk_score',
            'INTEGER NOT NULL DEFAULT 50',
            dialect,
        )
        _add_column_if_missing(conn, 'incidents', 'priority', "TEXT NOT NULL DEFAULT 'p3'", dialect)
        _add_column_if_missing(conn, 'incidents', 'service_name', 'TEXT', dialect)
        _add_column_if_missing(conn, 'incidents', 'owner', 'TEXT', dialect)
        _add_column_if_missing(conn, 'incidents', 'environment', 'TEXT', dialect)
        _add_column_if_missing(conn, 'incidents', 'impact', 'TEXT', dialect)
        _add_column_if_missing(conn, 'incidents', 'correlation_key', 'TEXT', dialect)
        _add_column_if_missing(
            conn,
            'incidents',
            'detected_at',
            timestamp_add_type,
            dialect,
        )
        _add_column_if_missing(conn, 'incidents', 'acknowledged_at', timestamp_type, dialect)
        _add_column_if_missing(conn, 'incidents', 'resolved_at', timestamp_type, dialect)
        _add_column_if_missing(
            conn,
            'incidents',
            'last_seen_at',
            timestamp_add_type,
            dialect,
        )
        _add_column_if_missing(
            conn,
            'incidents',
            'updated_at',
            timestamp_add_type,
            dialect,
        )
        conn.execute(
            text(
                '''
                CREATE INDEX IF NOT EXISTS idx_incidents_created_at
                ON incidents(created_at DESC)
                '''
            )
        )
        conn.execute(
            text(
                '''
                CREATE UNIQUE INDEX IF NOT EXISTS idx_incidents_correlation_key
                ON incidents(correlation_key)
                '''
            )
        )
        conn.execute(
            text(
                '''
                CREATE INDEX IF NOT EXISTS idx_incidents_service_status
                ON incidents(service_name, status)
                '''
            )
        )
        conn.execute(
            text(
                f'''
                CREATE TABLE IF NOT EXISTS services (
                    id {primary_key_type},
                    name TEXT NOT NULL UNIQUE,
                    owner TEXT,
                    tier TEXT NOT NULL DEFAULT 'tier-3',
                    environment TEXT,
                    health_score INTEGER NOT NULL DEFAULT 100,
                    last_seen_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
                    created_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
                    updated_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP
                )
                '''
            )
        )
        conn.execute(
            text(
                f'''
                CREATE TABLE IF NOT EXISTS deployments (
                    id {primary_key_type},
                    service_name TEXT,
                    environment TEXT,
                    version TEXT,
                    status TEXT NOT NULL DEFAULT 'unknown',
                    risk_score INTEGER NOT NULL DEFAULT 20,
                    actor TEXT,
                    source TEXT,
                    source_event_id INTEGER,
                    started_at {timestamp_type},
                    finished_at {timestamp_type},
                    created_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP
                )
                '''
            )
        )
        conn.execute(
            text(
                f'''
                CREATE TABLE IF NOT EXISTS incident_status_history (
                    id {primary_key_type},
                    incident_id INTEGER NOT NULL,
                    from_status TEXT,
                    to_status TEXT NOT NULL,
                    actor TEXT,
                    reason TEXT,
                    created_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP
                )
                '''
            )
        )
        conn.execute(
            text(
                f'''
                CREATE TABLE IF NOT EXISTS incident_notes (
                    id {primary_key_type},
                    incident_id INTEGER NOT NULL,
                    note TEXT NOT NULL,
                    author TEXT,
                    note_type TEXT NOT NULL DEFAULT 'manual',
                    created_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP
                )
                '''
            )
        )
        conn.execute(
            text(
                f'''
                CREATE TABLE IF NOT EXISTS event_correlations (
                    id {primary_key_type},
                    source_event_id INTEGER NOT NULL,
                    target_event_id INTEGER NOT NULL,
                    correlation_type TEXT NOT NULL,
                    confidence REAL NOT NULL DEFAULT 0.5,
                    reason TEXT,
                    created_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP
                )
                '''
            )
        )
        conn.execute(
            text(
                '''
                CREATE INDEX IF NOT EXISTS idx_services_name
                ON services(name)
                '''
            )
        )
        conn.execute(
            text(
                '''
                CREATE INDEX IF NOT EXISTS idx_deployments_service_created
                ON deployments(service_name, created_at DESC)
                '''
            )
        )
        conn.execute(
            text(
                '''
                CREATE UNIQUE INDEX IF NOT EXISTS idx_deployments_source_event
                ON deployments(source_event_id)
                '''
            )
        )
        conn.execute(
            text(
                '''
                CREATE INDEX IF NOT EXISTS idx_status_history_incident
                ON incident_status_history(incident_id, created_at DESC)
                '''
            )
        )
        _backfill_operational_records(conn)
        conn.execute(
            text(
                '''
                CREATE UNIQUE INDEX IF NOT EXISTS idx_event_correlations_unique
                ON event_correlations(source_event_id, target_event_id, correlation_type)
                '''
            )
        )
