from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3, os, random
from datetime import datetime

app = Flask(__name__)
DB_FILE = "feedback.db"

# -----------------------------
# 1️⃣ INITIAL SETUP (Decomposition)
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # feedback table
    c.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            q1 INTEGER,
            q2 INTEGER,
            q3 INTEGER,
            q4 INTEGER,
            comment TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # monthly summary table (for display)
    c.execute("""
        CREATE TABLE IF NOT EXISTS monthly_summary (
            month TEXT PRIMARY KEY,
            avg_score REAL,
            feedback_count INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()


# helper to get DB connection
def get_conn():
    return sqlite3.connect(DB_FILE)


# -----------------------------
# 2️⃣ FORM INPUT
# -----------------------------
@app.route("/", methods=["GET"])
def form():
    return render_template("form.html")


@app.route("/submit", methods=["POST"])
def submit():
    try:
        q1 = int(request.form.get("q1"))
        q2 = int(request.form.get("q2"))
        q3 = int(request.form.get("q3"))
        q4 = int(request.form.get("q4"))
    except (TypeError, ValueError):
        return "Invalid input - please provide ratings 0-5", 400

    note = request.form.get("note", "").strip()

    conn = get_conn()
    c = conn.cursor()

    # Insert feedback
    c.execute("INSERT INTO feedback (q1,q2,q3,q4,comment) VALUES (?,?,?,?,?)",
              (q1, q2, q3, q4, note))

    # ✅ Update monthly summary
    current_month = datetime.now().strftime("%Y-%m")

    c.execute("""
        INSERT INTO monthly_summary (month, avg_score, feedback_count)
        VALUES (
            ?, 
            (SELECT AVG((q1+q2+q3+q4)/4.0) FROM feedback WHERE strftime('%Y-%m', created_at) = ?),
            (SELECT COUNT(*) FROM feedback WHERE strftime('%Y-%m', created_at) = ?)
        )
        ON CONFLICT(month) DO UPDATE SET
            avg_score = excluded.avg_score,
            feedback_count = excluded.feedback_count
    """, (current_month, current_month, current_month))

    conn.commit()
    conn.close()

    return redirect(url_for("thankyou"))


# -----------------------------
# 3️⃣ THANK YOU PAGE
# -----------------------------
@app.route("/thankyou")
def thankyou():
    return render_template("thankyou.html")


# -----------------------------
# 4️⃣ GENERATE TEST DATA
# -----------------------------
@app.route("/generate_test_data")
def generate_test_data():
    conn = get_conn()
    c = conn.cursor()
    for _ in range(20):
        q1 = random.randint(0, 5)
        q2 = random.randint(0, 5)
        q3 = random.randint(0, 5)
        q4 = random.randint(0, 5)
        comment = random.choice(["Good", "Okay", "Bad experience", "Loved it!", "Could be better"])
        c.execute("INSERT INTO feedback (q1,q2,q3,q4,comment) VALUES (?,?,?,?,?)",
                  (q1, q2, q3, q4, comment))
    conn.commit()
    conn.close()
    return "✅ 20 test feedbacks added!"


# -----------------------------
# 5️⃣ STATISTICS DASHBOARD
# -----------------------------
@app.route("/stats")
def stats():
    conn = get_conn()
    c = conn.cursor()

    # Current stats from feedback table
    c.execute("""
        SELECT strftime('%Y-%m', created_at) AS month,
               COALESCE(AVG((COALESCE(q1,0)+COALESCE(q2,0)+COALESCE(q3,0)+COALESCE(q4,0))/4.0), 0.0) AS avg_score,
               COUNT(*) AS cnt
        FROM feedback
        GROUP BY month
        ORDER BY month
    """)
    rows = c.fetchall()
    conn.close()

    months = [r[0] for r in rows]
    avg_scores = [round(r[1] or 0.0, 2) for r in rows]
    counts = [r[2] for r in rows]

    current_month = months[-1] if months else None
    avg_score = avg_scores[-1] if avg_scores else None

    trend = "stable"
    if len(avg_scores) >= 2:
        if avg_scores[-1] > avg_scores[-2]:
            trend = "up"
        elif avg_scores[-1] < avg_scores[-2]:
            trend = "down"

    # Positive rate for this month
    positive_rate = 0
    if current_month:
        conn = get_conn()
        c = conn.cursor()
        c.execute("""
            SELECT COUNT(*) FROM feedback
            WHERE strftime('%Y-%m', created_at) = ?
            AND ((COALESCE(q1,0)+COALESCE(q2,0)+COALESCE(q3,0)+COALESCE(q4,0))/4.0) >= 4.0
        """, (current_month,))
        positive_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM feedback WHERE strftime('%Y-%m', created_at) = ?", (current_month,))
        total_count = c.fetchone()[0] or 0
        conn.close()
        positive_rate = round(positive_count / total_count * 100, 1) if total_count > 0 else 0

    alert = None
    if avg_score is not None and avg_score < 3.0:
        alert = "⚠️ Warning: User experience needs improvement!"

    # ✅ Lấy thêm dữ liệu từ monthly_summary để hiển thị
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT month, avg_score, feedback_count FROM monthly_summary ORDER BY month")
    monthly_summary = c.fetchall()
    conn.close()

    return render_template(
        "stats.html",
        months=months,
        avg_scores=avg_scores,
        counts=counts,
        alert=alert,
        current_month=current_month,
        avg_score=avg_score,
        trend=trend,
        positive_rate=positive_rate,
        monthly_summary=monthly_summary   # ✅ gửi qua template
    )


# -----------------------------
# 6️⃣ DELETE ALL (optional)
# -----------------------------
@app.route("/delete_all")
def delete_all():
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM feedback")
    c.execute("DELETE FROM monthly_summary")  # ✅ clear luôn summary
    conn.commit()
    conn.close()
    return "🗑️ All feedback deleted!"


if __name__ == "__main__":
    app.run(debug=True)
