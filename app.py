import os
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
from flask import Flask, request, make_response, redirect, render_template, g, abort
from user_service import get_user_with_credentials, logged_in
from account_service import get_balance, do_transfer

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET")
csrf = CSRFProtect(app)


@app.route("/", methods=["GET"])
def home():
    if not logged_in():
        return render_template("login.html")
    return redirect("/dashboard")


@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    user = get_user_with_credentials(email, password)

    if not user:
        return render_template("login.html", error="Invalid email or password")

    response = make_response(redirect("/dashboard"))
    response.set_cookie("auth_token", user["token"])
    return response, 303


@app.route("/dashboard", methods=["GET"])
def dashboard():
    if not logged_in():
        return render_template("login.html")
    return render_template("dashboard.html", email=g.user)


@app.route("/details", methods=["GET", "POST"])
def details():
    if not logged_in():
        return render_template("login.html")

    if request.method == "GET":
        account_number = request.args["account"]
        return render_template(
            "details.html",
            user=g.user,
            account_number=account_number,
            balance=get_balance(account_number, g.user),
        )


@app.route("/transfer", methods=["GET", "POST"])
def transfer():
    if not logged_in():
        return render_template("login.html")

    if request.method == "GET":
        # print("----------------> GETing")
        return render_template("transfer.html", user=g.user)

    print("----------------> POSTing")
    source = request.form.get("from")
    target = request.form.get("to")
    amount = int(request.form.get("amount"))

    if amount < 0:
        abort(400, "NO STEALING")
    if amount > 1000:
        abort(400, "WOAH THERE TAKE IT EASY")

    available_balance = get_balance(source, g.user)
    if available_balance is None:
        abort(404, "Account not found")
    if amount > available_balance:
        abort(400, "You don't have that much")

    if do_transfer(source, target, amount):
        pass  # TODO GIVE FEEDBACK
    else:
        abort(400, "Something bad happened")

    response = make_response(redirect("/dashboard"))
    return response, 303


@app.route("/logout", methods=["GET"])
def logout():
    response = make_response(redirect("/dashboard"))
    response.delete_cookie("auth_token")
    return response, 303
