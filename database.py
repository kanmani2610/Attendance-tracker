import psycopg2
import os

# ✅ Use PostgreSQL on Render via DATABASE_URL environment variable
DATABASE_URL = os.environ.get("DATABASE_URL")


def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # EMPLOYEES
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            salary INTEGER NOT NULL CHECK(salary > 0)
        )
    """)

    # ATTENDANCE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id SERIAL PRIMARY KEY,
            employee_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT CHECK(status IN ('P', 'L')),
            FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE,
            UNIQUE(employee_id, date)
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()