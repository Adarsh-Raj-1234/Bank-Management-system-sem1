from flask import Flask, render_template, request, redirect, url_for, session, Response
import sqlite3

app = Flask(__name__)
app.secret_key = "batman"

def init_db():
    conn = sqlite3.connect("bank.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            balance INTEGER DEFAULT 100000,
            pin INTEGER DEFAULT 1234
        )
    """)
    conn.commit()
    conn.close()
init_db()
@app.route("/")
def home():
    return render_template("project.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = sqlite3.connect("bank.db")
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return Response("Username already exists")
        conn.close()
        return redirect(url_for("home"))

    return render_template("signup.html")

@app.route("/hello", methods=["POST"])
def hello():
    username = request.form.get("username")
    password = request.form.get("password")

    conn = sqlite3.connect("bank.db")
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    )
    user = cur.fetchone()
    conn.close()

    if user:
        session["user"] = username
        return render_template("login.html")
    else:
        return Response("Invalid username or password")

@app.route("/login", methods=["POST"])
def login():
    action = request.form.get("action")
    if action == "with":
        return render_template("with.html")
    elif action == "depo":
        return render_template("depo.html")
    elif action == "chck":
        return render_template("pin.html")
    elif action == "acc":
        return redirect(url_for("acc"))

@app.route("/with", methods=["POST"])
def withdraw():
    amount = int(request.form.get("amount"))
    username = session.get("user")

    conn = sqlite3.connect("bank.db")
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE username=?", (username,))
    balance = cur.fetchone()[0]

    if amount <= 0 or amount > balance:
        conn.close()
        return Response("Invalid amount")

    # ✅ FIXED SESSION USAGE (NO LOGIC CHANGE)
    session["next_action"] = "with"
    session["balance1"] = amount

    conn.close()
    return render_template("pin.html")

@app.route("/depo", methods=["POST"])
def deposit():
    amount = int(request.form.get("amount"))
    username = session.get("user")

    if amount <= 0:
        return Response("Enter amount greater than zero")

    conn = sqlite3.connect("bank.db")
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE username=?", (username,))
    balance = cur.fetchone()[0]

    new_balance = balance + amount

    # ✅ FIXED SESSION USAGE
    session["next_action"] = "depo"
    session["balance2"] = new_balance

    conn.close()
    return render_template("pin.html")

@app.route("/pin", methods=["POST"])
def pin():
    entered_pin = int(request.form.get("pin"))
    username = session.get("user")

    conn = sqlite3.connect("bank.db")
    cur = conn.cursor()
    cur.execute("SELECT pin, balance FROM users WHERE username=?", (username,))
    pin, balance = cur.fetchone()

    if entered_pin == pin:
        if session.get("next_action") == "with":
            new_balance = balance - session.get("balance1")

        elif session.get("next_action") == "depo":
            new_balance = session.get("balance2")

        cur.execute(
            "UPDATE users SET balance=? WHERE username=?",
            (new_balance, username)
        )
        conn.commit()
        conn.close()

        return Response(f"Transaction successful. New balance: {new_balance}")
    else:
        conn.close()
        return Response("Incorrect PIN")

@app.route("/acc")
def acc():
    username = session.get("user")

    conn = sqlite3.connect("bank.db")
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE username=?", (username,))
    balance = cur.fetchone()[0]
    conn.close()

    return Response(f"Hi {username}! Your account balance is {balance}")

if __name__ == "__main__":
    app.run(debug=True)
