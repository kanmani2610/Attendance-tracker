from database import get_connection


def load_employees():
    conn = get_connection()
    cursor = conn.cursor()

    
    cursor.execute("SELECT id, name, salary FROM employees")
    rows = cursor.fetchall()

    cursor.close()
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
            "INSERT INTO employees (name, salary) VALUES (%s, %s)",
            (name.strip(), int(salary))
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise ValueError(f"Employee already exists or invalid data: {e}")
    finally:
        cursor.close()
        conn.close()


def delete_employee(emp_id):
    conn = get_connection()
    cursor = conn.cursor()

    
    cursor.execute("DELETE FROM employees WHERE id = %s", (emp_id,))
    conn.commit()
    cursor.close()
    conn.close()