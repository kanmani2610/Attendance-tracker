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
        days = form_data.getlist(name + "[]")

        for i, status in enumerate(days):
            if status:
                cursor.execute(
                    "INSERT INTO attendance (name, month, day, status) VALUES (?, ?, ?, ?)",
                    (name, month, i + 1, status)
                )

    conn.commit()
<<<<<<< HEAD
    conn.close()
=======
    conn.close()
>>>>>>> 6308753b0c182742fd7eb5b09eef92abd1f6b596
