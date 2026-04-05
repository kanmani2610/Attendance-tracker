from database import get_connection


def get_attendance(month):
    conn = get_connection()
    cursor = conn.cursor()

    # ✅ %s instead of ? for PostgreSQL
    cursor.execute("""
        SELECT e.name, a.date, a.status
        FROM attendance a
        JOIN employees e ON a.employee_id = e.id
        WHERE a.date LIKE %s
    """, (f"{month}%",))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    data = {}

    for name, date, status in rows:
        # date is "2025-01-05", day is the 3rd part
        parts = date.split("-")
        if len(parts) < 3:
            continue
        day = int(parts[2])

        if name not in data:
            data[name] = [""] * 31

        data[name][day - 1] = status

    return data


def save_attendance(month, employees, form_data):
    conn = get_connection()
    cursor = conn.cursor()

    # ✅ Delete only this month's records
    cursor.execute(
        "DELETE FROM attendance WHERE date LIKE %s",
        (f"{month}%",)
    )

    for emp in employees:
        emp_id = emp["id"]
        name = emp["name"]

        days = form_data.getlist(name + "[]")

        for i, status in enumerate(days):
            if status in ["P", "L"]:
                # Store as "2025-01-05" ISO format
                date = f"{month}-{i+1:02d}"

                # ✅ ON CONFLICT instead of INSERT OR REPLACE for PostgreSQL
                cursor.execute("""
                    INSERT INTO attendance (employee_id, date, status)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (employee_id, date) DO UPDATE SET status = EXCLUDED.status
                """, (emp_id, date, status))

    conn.commit()
    cursor.close()
    conn.close()