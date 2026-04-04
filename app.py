from flask import Flask, render_template, request, redirect, session, send_file
import os
import pandas as pd
from werkzeug.security import check_password_hash
from functools import wraps
import io

# DB
from database import init_db, get_connection

# SERVICES
from services.employee_service import load_employees, add_employee, delete_employee
from services.attendance_service import get_attendance, save_attendance

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback-secret")

# ✅ IMPORTANT
init_db()


# 🔐 LOGIN DECORATOR
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect("/")
        return f(*args, **kwargs)
    return wrapper


# 🔐 ADMIN CONFIG
ADMIN_USER = os.getenv("ADMIN_USER", "kanmani")
ADMIN_PASS_HASH = os.getenv(
    "ADMIN_PASS_HASH",
    "scrypt:32768:8:1$CAEBIKjycQofVpfR$225a63ebe8c8571ad0c85f6ff9c4a37461c0bae456b0a6edbb64540cc035715f6863cce641b3292f083b507d2c488be8f6cfb2b0ef6912e650ddf0c706a13be5"
)


# 🔐 LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USER and check_password_hash(ADMIN_PASS_HASH, password):
            session["user"] = username
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")


# 🚪 LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# 📅 DASHBOARD
@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    employees = load_employees()

    month = request.args.get("month") or session.get("month", "")
    attendance_data = {}

    if month:
        attendance_data = get_attendance(month)

    if request.method == "POST":
        month = request.form["month"]
        session["month"] = month

        save_attendance(month, employees, request.form)

        return redirect(f"/dashboard?month={month}")

    return render_template(
        "dashboard.html",
        employees=employees,
        attendance_data=attendance_data,
        selected_month=month
    )


# ➕ ADD EMPLOYEE
@app.route("/add", methods=["POST"])
@login_required
def add_employee_route():
    name = request.form["name"]

    try:
        salary = int(request.form["salary"])
    except:
        return "Invalid salary input"

    add_employee(name, salary)
    return redirect("/dashboard")


# ❌ DELETE EMPLOYEE
@app.route("/delete/<int:id>")
@login_required
def delete_employee_route(id):
    delete_employee(id)
    return redirect("/dashboard")


@app.route("/report", methods=["GET", "POST"])
@login_required
def report():
    try:
        employees = load_employees()

        if request.method == "POST":
            month = request.form.get("month", "").lower()
            deduction = float(request.form.get("deduction", 0))

            conn = get_connection()
            cursor = conn.cursor()

            results = []

            for emp in employees:
                name = emp["name"]

                cursor.execute(
                    "SELECT status FROM attendance WHERE name=? AND month=?",
                    (name, month)
                )

                rows = cursor.fetchall()
                attendance = [r[0] for r in rows]

                leaves = attendance.count("L")
                present = attendance.count("P")

                salary = float(emp["salary"])  # FIX
                total_deduction = leaves * deduction
                final_salary = salary - total_deduction

                results.append([
                    name,
                    salary,
                    present,
                    leaves,
                    total_deduction,
                    final_salary
                ])

            conn.close()

            report_df = pd.DataFrame(results, columns=[
                "Name", "Salary", "Present", "Leaves", "Deduction", "Final Salary"
            ])

            output = io.BytesIO()
            report_df.to_excel(output, index=False)
            output.seek(0)

            return send_file(output, download_name="attendance_report.xlsx", as_attachment=True)

        return render_template("report.html")

    except Exception as e:
        print("ERROR:", e)
        return str(e), 500