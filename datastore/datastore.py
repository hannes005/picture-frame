import sqlite3

DB_PATH = "./datastore/datastore.db"

def get_db_conn() -> sqlite3.Connection:
    """Create configured SQLite connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database():

    print("DB initialization")
    print("DB Path" + DB_PATH)

    with get_db_conn() as conn:
        cur = conn.cursor()

        # Create photos table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY,
            path_original TEXT NOT NULL,
            path_display TEXT NOT NULL,
            path_thumb TEXT NOT NULL,
            processed INTEGER NOT NULL
        )
        """)

        # Create events table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL
        )
        """)

        # Create linking tables photos -> events
        cur.execute("""
        CREATE TABLE IF NOT EXISTS event_photos (
            event_id INTEGER NOT NULL,
            photo_id INTEGER NOT NULL,

            PRIMARY KEY (event_id, photo_id),

            FOREIGN KEY (event_id) REFERENCES events(id),
            FOREIGN KEY (photo_id) REFERENCES photos(id)
        );
        """)

initialize_database()

