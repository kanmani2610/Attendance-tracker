from database import get_connection


def get_attendance(month):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name, day, status FROM attendance WHERE month = ?",
        (month,)
    )

    rows = cursor.fetchall()
    conn.close()

    data = {}

    for name, day, status in rows:
        if name not in data:
            data[name] = [""] * 30
        data[name][day - 1] = status

    return data


def save_attendance(month, employees, form_data):
    conn = get_connection()
    cursor = conn.cursor()

    # delete old month data
    cursor.execute("DELETE FROM attendance WHERE month = ?", (month,))

    for emp in employees:
        name = emp["name"]

        # 🔥 IMPORTANT: matches HTML input name
        days = form_data.getlist(name + "[]")

        for i, status in enumerate(days):
            # ✅ only save valid values
            if status in ["P", "L"]:
                cursor.execute(
                    "INSERT INTO attendance (name, month, day, status) VALUES (?, ?, ?, ?)",
                    (name, month, i + 1, status)
                )

    conn.commit()
    conn.close()