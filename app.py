import sqlite3
import os
from flask import Flask, render_template, session, request, redirect
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "dev-secret-key"
)

conn = sqlite3.connect("database.db")
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS expenses(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount INTEGER,
    category TEXT,
    note TEXT,
    date TEXT)
""")
conn.commit()
conn.close()


@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form.get("name")
        password = request.form.get("password")

        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        try:
            cur.execute(
            "INSERT INTO users(username, password) VALUES(?, ?)",
            (username, hashed_password)
        )

            conn.commit()
            conn.close()

            return redirect("/login")
            
        except sqlite3.IntegrityError:
            conn.close()
            return render_template("signup.html", error="User already exists")
    return render_template("signup.html")
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("name")
        password = request.form.get("password")

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        )

        user = cur.fetchone()

        conn.close()

        if user:

            stored_password = user[2]

            if check_password_hash(
                stored_password,
                password
            ):

                session["user_id"] = user[0]
                session["username"] = user[1]

                return redirect("/dashboard")
        return render_template(
    "login.html",
    error="Invalid username or password"
) 

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # Search feature
    search = request.args.get("search")

    if search:

        cur.execute(
            """
            SELECT * FROM expenses
            WHERE user_id=? AND category=?
            """,
            (user_id, search)
        )

    else:

        cur.execute(
            """
            SELECT * FROM expenses
            WHERE user_id=?
            """
            ,
            (user_id,)
        )

    expenses = cur.fetchall()

    # Total spent
    cur.execute(
        """
        SELECT SUM(amount)
        FROM expenses
        WHERE user_id=?
        """,
        (user_id,)
    )

    total = cur.fetchone()[0] or 0

    # Total expense count
    cur.execute(
        """
        SELECT COUNT(*)
        FROM expenses
        WHERE user_id=?
        """,
        (user_id,)
    )

    count = cur.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        username=session["username"],
        expenses=expenses,
        total=total,
        count=count
    )
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")
@app.route("/add_expense", methods=["GET", "POST"])
def add_expense():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        amount = request.form.get("amount")
        category = request.form.get("category")
        note = request.form.get("note")
        date = request.form.get("date")

        user_id = session["user_id"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO expenses(
            user_id,
            amount,
            category,
            note,
            date
        )
        VALUES(?, ?, ?, ?, ?)
        """, (user_id, amount, category, note, date))

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("add_expense.html")
@app.route("/delete_expense/<int:id>")
def delete_expense(id):

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM expenses WHERE id=? AND user_id=?",
        (id, user_id)
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")
@app.route("/edit_expense/<int:id>", methods=["GET", "POST"])
def edit_expense(id):

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    if request.method == "POST":

        amount = request.form.get("amount")
        category = request.form.get("category")
        note = request.form.get("note")
        date = request.form.get("date")

        cur.execute("""
        UPDATE expenses
        SET amount=?,
            category=?,
            note=?,
            date=?
        WHERE id=? AND user_id=?
        """, (
            amount,
            category,
            note,
            date,
            id,
            user_id
        ))

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    cur.execute(
        "SELECT * FROM expenses WHERE id=? AND user_id=?",
        (id, user_id)
    )

    expense = cur.fetchone()

    conn.close()

    return render_template(
        "edit_expense.html",
        expense=expense
    )
if __name__ == "__main__":
    app.run(debug=True)  
     
