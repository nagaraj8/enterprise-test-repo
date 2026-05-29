from sqlalchemy import text

from app.database.db import engine


def ensure_local_schema() -> None:
    if engine.dialect.name != 'sqlite':
        return

    with engine.begin() as conn:
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
