from database import get_connection


def get_attendance(month):
    conn = get_connection()
    cursor = conn.cursor()

    # ✅ JOIN with employees to get name
    cursor.execute("""
        SELECT e.name, a.date, a.status
        FROM attendance a
        JOIN employees e ON a.employee_id = e.id
        WHERE LOWER(a.date) LIKE ?
    """, (f"%{month.lower()}%",))

    rows = cursor.fetchall()
    conn.close()

    data = {}

    for name, date, status in rows:
        # extract day from date (format: "january-5")
        day = int(date.split("-")[1])

        if name not in data:
            data[name] = [""] * 31  # max days

        data[name][day - 1] = status

    return data


def save_attendance(month, employees, form_data):
    conn = get_connection()
    cursor = conn.cursor()

    # ❌ REMOVE old delete (wrong structure)
    cursor.execute("DELETE FROM attendance")

    for emp in employees:
        emp_id = emp["id"]
        name = emp["name"]

        days = form_data.getlist(name + "[]")

        for i, status in enumerate(days):
            if status in ["P", "L"]:
                date = f"{month.lower()}-{i+1}"

                cursor.execute("""
                    INSERT OR REPLACE INTO attendance (employee_id, date, status)
                    VALUES (?, ?, ?)
                """, (emp_id, date, status))

    conn.commit()
    conn.close()