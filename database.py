import sqlite3

DB_NAME = "database.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # ✅ allows dict-like access
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # ✅ EMPLOYEES TABLE (with constraints)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            salary INTEGER NOT NULL CHECK(salary > 0)
        )
    """)

    # ✅ ATTENDANCE TABLE (IMPROVED DESIGN)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT CHECK(status IN ('P', 'L')),

            FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE,
            UNIQUE(employee_id, date)
        )
    """)

    conn.commit()
    conn.close()