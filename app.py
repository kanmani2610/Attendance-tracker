from flask import Flask, render_template, request, redirect, session, send_file, flash
import os
import pandas as pd
from werkzeug.security import check_password_hash
from functools import wraps
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# DB
from database import init_db, get_connection

# SERVICES
from services.employee_service import load_employees, add_employee, delete_employee
from services.attendance_service import get_attendance, save_attendance, get_weekly_attendance

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback-secret")


init_db()


SENDER_EMAIL = "jkanmani691@gmail.com"
SENDER_PASSWORD = os.environ.get("EMAIL_PASSWORD", "ljbt rhow gmmk oucb")
RECEIVER_EMAILS = ["jaikumar.197306@gmail.com", "kanmanijayakumar26022007@gmail.com"]
DAILY_RATE = 100  # ₹100 per day



def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect("/")
        return f(*args, **kwargs)
    return wrapper



ADMIN_USER = os.getenv("ADMIN_USER", "Kanmani")
ADMIN_PASS_HASH = os.getenv(
    "ADMIN_PASS_HASH",
    "scrypt:32768:8:1$CAEBIKjycQofVpfR$225a63ebe8c8571ad0c85f6ff9c4a37461c0bae456b0a6edbb64540cc035715f6863cce641b3292f083b507d2c488be8f6cfb2b0ef6912e650ddf0c706a13be5"
)



def send_weekly_email(week_data, week_label):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"BK Agencies — Saturday Payment Summary ({week_label})"
        msg["From"] = SENDER_EMAIL
        msg["To"] = ", ".join(RECEIVER_EMAILS)

        total = sum(d["amount"] for d in week_data)

        rows = ""
        for d in week_data:
            rows += f"""
            <tr>
                <td style="padding:10px 16px; border-bottom:1px solid #4a1a38;">{d['name']}</td>
                <td style="padding:10px 16px; border-bottom:1px solid #4a1a38; text-align:center;">{d['days']}</td>
                <td style="padding:10px 16px; border-bottom:1px solid #4a1a38; text-align:center;">₹{d['amount']}</td>
            </tr>
            """

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background:#1a0a14; color:#fdf0f5; padding:20px;">
            <div style="max-width:500px; margin:0 auto; background:#251020; border-radius:16px; padding:32px; border:1px solid #4a1a38;">
                <h2 style="color:#ff4d8d; margin-bottom:4px;">BK Agencies</h2>
                <p style="color:#b06080; margin-bottom:24px;">Saturday Payment Summary — {week_label}</p>
                <table style="width:100%; border-collapse:collapse;">
                    <thead>
                        <tr style="background:#2e1428;">
                            <th style="padding:10px 16px; text-align:left; color:#b06080; font-size:12px;">Employee</th>
                            <th style="padding:10px 16px; text-align:center; color:#b06080; font-size:12px;">Days Present</th>
                            <th style="padding:10px 16px; text-align:center; color:#b06080; font-size:12px;">Amount</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
                <div style="margin-top:20px; padding:16px; background:#2e1428; border-radius:10px; text-align:right;">
                    <span style="color:#b06080; font-size:14px;">Total to Pay Today:</span>
                    <span style="color:#ff4d8d; font-size:22px; font-weight:bold; margin-left:12px;">₹{total}</span>
                </div>
                <p style="color:#b06080; font-size:12px; margin-top:20px; text-align:center;">
                    This is an automated message from BK Agencies Attendance System.
                </p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAILS, msg.as_string())

        print(" Weekly email sent!")
        return True

    except Exception as e:
        print(f" Email error: {e}")
        return False



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



@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")



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



@app.route("/add", methods=["POST"])
@login_required
def add_employee_route():
    name = request.form["name"]
    try:
        salary = int(request.form["salary"])
    except Exception as e:
        flash("Invalid salary input!", "error")
        return redirect("/dashboard")

    try:
        add_employee(name, salary)
        flash(f"Employee '{name}' added successfully!", "success")
    except ValueError:
        
        flash(f"'{name}' already exists! Please use a different name.", "error")

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
            month = request.form.get("month", "").strip()
            deduction = float(request.form.get("deduction", 0))

            conn = get_connection()
            cursor = conn.cursor()

            results = []

            for emp in employees:
                emp_id = emp["id"]
                name = emp["name"]

                cursor.execute("""
                    SELECT status, date FROM attendance
                    WHERE employee_id = %s AND date LIKE %s
                """, (emp_id, f"{month}%"))

                rows = cursor.fetchall()

                leaves = 0
                present = 0
                for status, date in rows:
                    date_obj = datetime.strptime(date, "%Y-%m-%d")
                    if date_obj.weekday() == 6:  # Skip Sunday
                        continue
                    if status == "L":
                        leaves += 1
                    elif status == "P":
                        present += 1

                salary = float(emp["salary"])
                total_deduction = leaves * deduction
                final_salary = salary - total_deduction

                results.append([name, salary, present, leaves, total_deduction, final_salary])

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



@app.route("/weekly", methods=["GET", "POST"])
@login_required
def weekly():
    employees = load_employees()
    today = datetime.today()

    monday = today - timedelta(days=today.weekday())
    saturday = monday + timedelta(days=5)

    week_start_str = request.args.get("week_start", monday.strftime("%Y-%m-%d"))
    week_start = datetime.strptime(week_start_str, "%Y-%m-%d")
    week_end = week_start + timedelta(days=5)

    week_label = f"{week_start.strftime('%d %b')} – {week_end.strftime('%d %b %Y')}"

    week_data = get_weekly_attendance(employees, week_start, week_end)

    is_saturday = today.weekday() == 5
    email_sent = session.get("email_sent_date") == today.strftime("%Y-%m-%d")

    if request.method == "POST":
        success = send_weekly_email(week_data, week_label)
        if success:
            session["email_sent_date"] = today.strftime("%Y-%m-%d")
            return redirect("/weekly?week_start=" + week_start_str + "&email=sent")

    email_status = request.args.get("email")

    prev_week = (week_start - timedelta(days=7)).strftime("%Y-%m-%d")
    next_week = (week_start + timedelta(days=7)).strftime("%Y-%m-%d")

    return render_template(
        "weekly.html",
        employees=employees,
        week_data=week_data,
        week_label=week_label,
        week_start=week_start_str,
        prev_week=prev_week,
        next_week=next_week,
        is_saturday=is_saturday,
        email_sent=email_sent,
        email_status=email_status,
        daily_rate=DAILY_RATE,
        total=sum(d["amount"] for d in week_data)
    )