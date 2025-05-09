import os
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
from flask import (
    Flask,
    request,
    make_response,
    redirect,
    render_template,
    g,
    flash,
)
from datetime import datetime
from user_service import get_user_with_credentials, logged_in
from account_service import get_balance, do_transfer, get_user_accounts
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET")
csrf = CSRFProtect(app)


def authenticated(f):
    @wraps(f)
    def w(*args, **kwargs):
        if not logged_in():
            # return render_template("login.html")
            return redirect("/login")
        return f(*args, **kwargs)

    return w


@app.context_processor
def inject_now():
    return {"now": datetime.now()}


@app.route("/", methods=["GET"])
@authenticated
def home():
    return redirect("/dashboard")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email")
    password = request.form.get("password")
    user = get_user_with_credentials(email, password)

    if not user:
        return render_template("login.html", error="Invalid email or password")

    response = make_response(redirect("/dashboard"))
    response.set_cookie("auth_token", user["token"])
    return response, 303


@app.route("/dashboard", methods=["GET"])
@authenticated
def dashboard():
    return render_template("dashboard.html", email=g.user)


@app.route("/details", methods=["GET", "POST"])
@authenticated
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
        # Get all accounts for the current user
        user_accounts = get_user_accounts(g.user)
        return render_template(
            "transfer.html", user=g.user, user_accounts=user_accounts
        )

    source = request.form.get("from")
    target = request.form.get("to")
    amount_str = request.form.get("amount")

    # Validate input
    if not source or not target or not amount_str:
        flash("All fields are required", "error")
        user_accounts = get_user_accounts(g.user)
        return render_template(
            "transfer.html", user=g.user, user_accounts=user_accounts
        )

    try:
        amount = int(amount_str)
    except ValueError:
        flash("Amount must be a valid number", "error")
        user_accounts = get_user_accounts(g.user)
        return render_template(
            "transfer.html", user=g.user, user_accounts=user_accounts
        )

    # Validate amount
    if amount < 0:
        flash("No stealing allowed! Amount must be positive", "error")
        user_accounts = get_user_accounts(g.user)
        return render_template(
            "transfer.html", user=g.user, user_accounts=user_accounts
        )
    if amount > 1000:
        flash("Worker ants can only carry 1,000 crumbs at a time", "error")
        user_accounts = get_user_accounts(g.user)
        return render_template(
            "transfer.html", user=g.user, user_accounts=user_accounts
        )

    # Verify source account belongs to user and has sufficient funds
    available_balance = get_balance(source, g.user)
    if available_balance is None:
        flash("Source storage unit not found or doesn't belong to you", "error")
        user_accounts = get_user_accounts(g.user)
        return render_template(
            "transfer.html", user=g.user, user_accounts=user_accounts
        )

    if amount > available_balance:
        flash(
            f"Insufficient crumbs! You only have {available_balance} available", "error"
        )
        user_accounts = get_user_accounts(g.user)
        return render_template(
            "transfer.html", user=g.user, user_accounts=user_accounts
        )

    try:
        result = do_transfer(source, target, amount)
        if result:
            flash(
                f"Successfully transported {amount} crumbs to storage unit {target}",
                "success",
            )
        else:
            flash(
                "Transport failed. The destination storage unit may not exist.", "error"
            )
            user_accounts = get_user_accounts(g.user)
            return render_template(
                "transfer.html", user=g.user, user_accounts=user_accounts
            )
    except Exception as e:
        flash(f"An error occurred during transport: {str(e)}", "error")
        user_accounts = get_user_accounts(g.user)
        return render_template(
            "transfer.html", user=g.user, user_accounts=user_accounts
        )

    return redirect("/dashboard")


@app.route("/logout", methods=["GET"])
def logout():
    response = make_response(redirect("/dashboard"))
    response.delete_cookie("auth_token")
    return response, 303
