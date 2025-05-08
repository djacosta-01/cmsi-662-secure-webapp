import sqlite3
from datetime import datetime, timezone, timedelta
from passlib.hash import pbkdf2_sha256
from flask import request, g
import jwt
import os
from dotenv import load_dotenv

load_dotenv()

SECRET = os.getenv("SECRET")


def get_user_with_credentials(email, password):
    try:
        con = sqlite3.connect("bank.db")
        cur = con.cursor()
        cur.execute(
            """
            SELECT email, name, password FROM users where email=?""",
            (email,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        email, name, hash = row
        if not pbkdf2_sha256.verify(password, hash):
            return None
        return {"email": email, "name": name, "token": create_token(email)}
    finally:
        con.close()


def logged_in():
    token = request.cookies.get("auth_token")
    try:
        data = jwt.decode(token, SECRET, algorithms=["HS256"])
        g.user = data["sub"]
        return True
    except jwt.InvalidTokenError:
        return False


def create_token(email):
    now = datetime.now(timezone.utc)
    payload = {"sub": email, "iat": now, "exp": now + timedelta(minutes=60)}
    token = jwt.encode(payload, SECRET, algorithm="HS256")
    return token
