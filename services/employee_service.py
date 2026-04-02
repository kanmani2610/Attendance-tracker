from database import get_connection


def load_employees():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, salary FROM employees")
    rows = cursor.fetchall()

    conn.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "salary": row[2]
        }
        for row in rows
    ]


def add_employee(name, salary):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO employees (name, salary) VALUES (?, ?)",
            (name.strip(), int(salary))
        )
        conn.commit()
    except:
        conn.rollback()
        raise ValueError("Employee already exists or invalid data")
    finally:
        conn.close()


def delete_employee(emp_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM employees WHERE id = ?", (emp_id,))
    conn.commit()
    conn.close()