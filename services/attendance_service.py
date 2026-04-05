from database import get_connection
from datetime import datetime, timedelta


def get_attendance(month):
    conn = get_connection()
    cursor = conn.cursor()

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
                date = f"{month}-{i+1:02d}"
                cursor.execute("""
                    INSERT INTO attendance (employee_id, date, status)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (employee_id, date) DO UPDATE SET status = EXCLUDED.status
                """, (emp_id, date, status))

    conn.commit()
    cursor.close()
    conn.close()


def get_weekly_attendance(employees, week_start, week_end):
    """Get attendance for each employee for a Mon-Sat week (skip Sunday)"""
    conn = get_connection()
    cursor = conn.cursor()

    result = []

    for emp in employees:
        emp_id = emp["id"]
        name = emp["name"]
        days_present = 0
        daily_breakdown = []

        current = week_start
        while current <= week_end:
            # Skip Sunday (weekday 6)
            if current.weekday() == 6:
                current += timedelta(days=1)
                continue

            date_str = current.strftime("%Y-%m-%d")

            cursor.execute("""
                SELECT status FROM attendance
                WHERE employee_id = %s AND date = %s
            """, (emp_id, date_str))

            row = cursor.fetchone()
            status = row[0] if row else ""

            daily_breakdown.append({
                "date": date_str,
                "day": current.strftime("%a"),  # Mon, Tue etc
                "status": status
            })

            if status == "P":
                days_present += 1

            current += timedelta(days=1)

        result.append({
            "name": name,
            "days": days_present,
            "amount": days_present * 100,  # ₹100 per day
            "breakdown": daily_breakdown
        })

    cursor.close()
    conn.close()

    return result