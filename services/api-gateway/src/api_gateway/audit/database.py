import sqlite3
from pathlib import Path


# 数据库文件位置
BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "audit.db"



def get_connection():
    """
    Get sqlite connection.
    """

    conn = sqlite3.connect(
        DB_PATH
    )

    conn.row_factory = sqlite3.Row

    return conn



def init_database():
    """
    Initialize audit table.
    """

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_events
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            trace_id TEXT NOT NULL,

            business_id TEXT NOT NULL,

            stage TEXT NOT NULL,

            service TEXT NOT NULL,

            action TEXT NOT NULL,

            status TEXT NOT NULL,

            timestamp TEXT NOT NULL,

            detail TEXT,

            previous_hash TEXT,

            event_hash TEXT
        )
        """
    )


    conn.commit()

    conn.close()



def insert_event(event: dict):
    """
    Insert audit event.
    """

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute(
        """
        INSERT INTO audit_events
        (
            trace_id,
            business_id,
            stage,
            service,
            action,
            status,
            timestamp,
            detail,
            previous_hash,
            event_hash
        )
        VALUES
        (
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?
        )
        """,
        (
            event["traceId"],
            event["businessId"],
            event["stage"],
            event["service"],
            event["action"],
            event["status"],
            event["timestamp"],
            str(event.get("detail", {})),
            event.get("previousHash"),
            event.get("eventHash"),
        )
    )


    conn.commit()

    conn.close()



def query_events(
    business_id: str
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT *
        FROM audit_events
        WHERE business_id=?
        ORDER BY id ASC
        """,
        (
            business_id,
        )
    )


    rows = cursor.fetchall()


    conn.close()


    return [
        dict(row)
        for row in rows
    ]