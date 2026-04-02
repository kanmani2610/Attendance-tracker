import sqlite3
import os

# ✅ FIXED PATH (works on Render + local)
DB_NAME = os.path.join(os.getcwd(), "database.db")


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # ✅ EMPLOYEES TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            salary INTEGER NOT NULL CHECK(salary > 0)
        )
    """)

    # ✅ ATTENDANCE TABLE (MATCHES YOUR APP)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            month TEXT,
            day INTEGER,
            status TEXT
        )
    """)

    conn.commit()
    conn.close()