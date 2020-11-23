from __future__ import print_function
import os
import csv
import sys
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///project.db")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register User"""
    if request.method == "POST":

        if not request.form.get("username"):
            return apology("must provide username", 403)

        elif not request.form.get("password"):
            return apology("must provide password", 403)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords don't match", 403)

        if request.form.get("username") in db.execute("SELECT username FROM users"):
            return apology("username taken", 403)

        else:
            db.execute("INSERT INTO users(username, hash, user_type) VALUES(?,?,?)",
                    request.form.get("username"), generate_password_hash(request.form.get("password")), request.form.get("type"))

            return redirect("/login")

    else:
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]

        # Redirect user to home page
        return redirect("/sapp")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/sapp", methods=["GET"])
@login_required
def sapp():
    if request.method == "GET":
        if not db.execute("SELECT squat, bench, deadlift, chins, time_date FROM testing WHERE user_id = ?", session['user_id']):
            dict1 = {'squat': 0, 'bench': 0, 'deadlift': 0, 'chins': 0, 'test_date': 0}
            testing = []
            testing.append(dict1)
        else:
            testing = db.execute("SELECT squat, bench, deadlift, chins, time_date FROM testing WHERE user_id = ? ORDER BY time_date DESC", session['user_id'])
        if not db.execute("SELECT squat, bench, deadlift, chins FROM best_lifts WHERE user_id =?", session['user_id']):
            dict2 = {'squat': 0, 'bench': 0, 'deadlift': 0, 'chins': 0}
            best = []
            best.append(dict2)
        else:
            best = db.execute("SELECT squat, bench, deadlift, chins FROM best_lifts WHERE user_id =?", session['user_id'])

        return render_template("app.html",testing=testing, best=best)

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")
# TESTING
@app.route("/testing", methods=["POST", "GET"])
@login_required
def testing():

    if request.method == "POST":
        """Log user out"""
        if not request.form.get('squat_weight') and not request.form.get('bench_weight') and not request.form.get('deadlift_weight') and not request.form.get('chins_weight'):
                    return apology("must add one exercise", 400)
        else:
            with open('weights_calc.csv', newline='') as file:
                weights = csv.DictReader(file)
                if weights is None:
                    return apology("file is empty", 400)
                # squat

                if not request.form.get("squat_weight") and not request.form.get("squat_reps"):
                    squated = 0
                else:
                    s_rep = int(request.form.get("squat_reps"))
                    squat = float(request.form.get("squat_weight"))
                    for rows in weights:
                        if int(rows['reps']) is s_rep:
                            code = float(rows['estimate'])
                    squated = round(code * squat, 1)

                # bench
                if not request.form.get("bench_weight")and not request.form.get("bench_reps"):
                    benched = 0
                else:
                    b_rep = int(request.form.get("bench_reps"))
                    bench = float(request.form.get("bench_weight"))
                    for rows in weights:
                        if int(rows['reps']) is b_rep:
                            code = float(rows['estimate'])
                    benched = round(code * bench, 1)

                # deadlift
                if not request.form.get("deadlift_weight") and not request.form.get("deadlift_reps"):
                    deadlifted = 0
                else:
                    d_rep = int(request.form.get("deadlift_reps"))
                    deadlift = float(request.form.get("deadlift_weight"))
                    for rows in weights:
                        if int(rows['reps']) is d_rep:
                            code = float(rows['estimate'])
                    deadlifted = round(code * deadlift, 1)
                # chins
                if not request.form.get("chins_weight") and not request.form.get("chins_reps"):
                    chined = 0
                else:
                    c_rep = int(request.form.get("chins_reps"))
                    chins = float(request.form.get("chins_weight"))
                    for rows in weights:
                        if int(rows['reps']) is c_rep:
                            code = float(rows['estimate'])
                    chined = round(code * chins, 1)
                # db query
                db.execute("INSERT INTO testing(user_id, squat, bench, chins, deadlift) VALUES(?,?,?,?,?)",
                            session['user_id'], squated, benched, chined, deadlifted)
                rows = db.execute("SELECT * FROM best_lifts WHERE user_id = ?",
                            session["user_id"])
                if len(rows) is 1:
                    # squat
                    squat = db.execute("SELECT squat FROM best_lifts WHERE user_id =?", session["user_id"])
                    if squated > squat[0]['squat']:
                        db.execute("UPDATE best_lifts SET squat = ? WHERE user_id =?", squated, session['user_id'])
                    # bench
                    bench = db.execute("SELECT bench FROM best_lifts WHERE user_id =?", session["user_id"])
                    if benched > bench[0]['bench']:
                        db.execute("UPDATE best_lifts SET bench = ? WHERE user_id =?", benched, session['user_id'])
                    # chins
                    dead = db.execute("SELECT deadlift FROM best_lifts WHERE user_id =?", session["user_id"])
                    if deadlifted > dead[0]['deadlift']:
                        db.execute("UPDATE best_lifts SET deadlift = ? WHERE user_id =?", deadlifted, session['user_id'])
                    #dead
                    chins = db.execute("SELECT chins FROM best_lifts WHERE user_id =?", session["user_id"])
                    if chined > chins[0]['chins']:
                        db.execute("UPDATE best_lifts SET chins = ? WHERE user_id =?", chined, session['user_id'])
                else:
                    db.execute("INSERT INTO best_lifts(user_id, squat, bench, chins, deadlift) VALUES(?,?,?,?,?)",
                                session['user_id'], squated, benched, chined, deadlifted)
        return redirect("/testing")

    if request.method == "GET":

        if not db.execute("SELECT squat, bench, deadlift, chins, time_date FROM testing WHERE user_id = ?", session['user_id']):
                dict1 = {'squat': 0, 'bench': 0, 'deadlift': 0, 'chins': 0, 'test_date': 0}
                testing = []
                testing.append(dict1)
        else:
            testing = db.execute("SELECT squat, bench, deadlift, chins, time_date FROM testing WHERE user_id = ? ORDER BY time_date DESC", session['user_id'])
            for test in testing:
                test["time_date"] = test["time_date"][0:10]

        return render_template("testing.html", testing=testing)

@app.route("/calculator", methods=["GET", "POST"])
@login_required
def calculator():

    if request.method == "POST":
        if not request.form.get("reps") and not request.form.get("percent") and not request.form.get("rir"):
            weight = 0
            return render_template("calculator.html", weight=weight)
        # reps only
        elif not request.form.get("percent") and not request.form.get("rir"):
            exercise = request.form.get("exercise")
            reps = int(request.form.get("reps"))
            if not db.execute("SELECT ? FROM best_lifts WHERE user_id = ?", exercise, session['user_id']):
                return apology("exercise not found", 400)
            best = db.execute("SELECT squat, bench, deadlift, chins FROM best_lifts WHERE user_id = ?", session['user_id'])
            w = best[0][exercise]
            with open('weights_calc.csv', newline='') as file:
                weights = csv.DictReader(file)
                if weights is None:
                    return apology("file is empty", 400)
                for rows in weights:
                        if int(rows['reps']) is reps:
                            code = float(rows['estimate'])
            weight = round(w / code)
            return render_template("calculator.html", weight=weight)
        # percent only
        elif not request.form.get("reps") and not request.form.get("rir"):
            exercise = request.form.get("exercise")
            percent = float(request.form.get("percent"))
            p = float(percent / 100)
            if not db.execute("SELECT ? FROM best_lifts WHERE user_id = ?", exercise, session['user_id']):
                return apology("exercise not found", 400)
            best = db.execute("SELECT squat, bench, deadlift, chins FROM best_lifts WHERE user_id = ?", session['user_id'])
            w = best[0][exercise]
            weight = round(p * w)
            return render_template("calculator.html", weight=weight)
        elif not request.form.get("reps") and not request.form.get("percent"):
            return apology("prescribed reps required for rir weight", 400)
        elif not request.form.get("percent"):
            exercise = request.form.get("exercise")
            rep = int(request.form.get("reps"))
            rir = int(request.form.get("rir"))
            reps = rep + rir
            if not db.execute("SELECT ? FROM best_lifts WHERE user_id = ?", exercise, session['user_id']):
                return apology("exercise not found", 400)
            best = db.execute("SELECT squat, bench, deadlift, chins FROM best_lifts WHERE user_id = ?", session['user_id'])
            w = best[0][exercise]
            with open('weights_calc.csv', newline='') as file:
                weights = csv.DictReader(file)
                if weights is None:
                    return apology("file is empty", 400)
                for rows in weights:
                        if int(rows['reps']) is reps:
                            code = float(rows['estimate'])
            weight = round(w / code)
            return render_template("calculator.html", weight=weight)
        elif not request.form.get("rir"):
            exercise = request.form.get("exercise")
            percent = float(request.form.get("percent"))
            reps = int(request.form.get("reps"))
            p = float(percent / 100)
            if not db.execute("SELECT ? FROM best_lifts WHERE user_id = ?", exercise, session['user_id']):
                return apology("exercise not found", 400)
            best = db.execute("SELECT squat, bench, deadlift, chins FROM best_lifts WHERE user_id = ?", session['user_id'])
            w = best[0][exercise]
            with open('weights_calc.csv', newline='') as file:
                weights = csv.DictReader(file)
                if weights is None:
                    return apology("file is empty", 400)
                for rows in weights:
                        if int(rows['reps']) is reps:
                            code = float(rows['estimate'])
            w2 = w / code
            weight = round(w2 * p)
            return render_template("calculator.html", weight=weight)
        elif not request.form.get("reps"):
            return apology("prescribed reps required for rir weight", 400)
        else:
            exercise = request.form.get("exercise")
            rep = int(request.form.get("reps"))
            percent = float(request.form.get("percent"))
            rir = int(request.form.get("rir"))
            reps = rep + rir
            p = float(percent / 100)
            if not db.execute("SELECT ? FROM best_lifts WHERE user_id = ?", exercise, session['user_id']):
                return apology("exercise not found", 400)
            best = db.execute("SELECT squat, bench, deadlift, chins FROM best_lifts WHERE user_id = ?", session['user_id'])
            w = best[0][exercise]
            with open('weights_calc.csv', newline='') as file:
                weights = csv.DictReader(file)
                if weights is None:
                    return apology("file is empty", 400)
                for rows in weights:
                        if int(rows['reps']) is reps:
                            code = float(rows['estimate'])
            w2 = w / code
            weight = round(w2 * p)
            return render_template("calculator.html", weight=weight)
    if request.method == "GET":
        weight = 0
        return render_template("calculator.html", weight=weight)

@app.route("/profile", methods=["GET"])
@login_required
def profile():
    if request.method == "GET":
        if not db.execute("SELECT squat, bench, deadlift, chins FROM best_lifts WHERE user_id =?", session['user_id']):
            dict2 = {'squat': 0, 'bench': 0, 'deadlift': 0, 'chins': 0}
            best = []
            best.append(dict2)
        else:
            best = db.execute("SELECT squat, bench, deadlift, chins FROM best_lifts WHERE user_id =?", session['user_id'])
        return render_template("profile.html", best=best)
