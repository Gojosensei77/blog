from __future__ import annotations

from functools import wraps
from typing import Callable, cast

from flask import (
    Blueprint,
    Response,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_database_connection


bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=("GET", "POST"))
def register() -> str | Response:
    if request.method == "POST":
        username: str = request.form.get("username", "").strip()
        password: str = request.form.get("password", "")

        error_message: str | None = None
        if not username:
            error_message = "Username is required."
        elif not password:
            error_message = "Password is required."

        if error_message is None:
            db_conn = get_database_connection()
            try:
                db_conn.execute(
                    "INSERT INTO user (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db_conn.commit()
            except Exception:
                error_message = "User is already registered."

        if error_message is None:
            flash("Registration successful. Please log in.")
            return redirect(url_for("auth.login"))

        flash(error_message)

    return cast(str, render_template("auth/register.html"))


@bp.route("/login", methods=("GET", "POST"))
def login() -> str | Response:
    if request.method == "POST":
        username: str = request.form.get("username", "").strip()
        password: str = request.form.get("password", "")

        error_message: str | None = None
        db_conn = get_database_connection()
        user_row = db_conn.execute(
            "SELECT * FROM user WHERE username = ?", (username,)
        ).fetchone()

        if user_row is None:
            error_message = "Incorrect username."
        elif not check_password_hash(user_row["password"], password):
            error_message = "Incorrect password."

        if error_message is None:
            session.clear()
            session["user_id"] = int(user_row["id"])  # type: ignore[index]
            return redirect(url_for("index"))

        flash(error_message)

    return cast(str, render_template("auth/login.html"))


@bp.before_app_request
def load_logged_in_user() -> None:
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        db_conn = get_database_connection()
        g.user = db_conn.execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()


@bp.route("/logout")
def logout() -> Response:
    session.clear()
    return redirect(url_for("index"))


def login_required(view_func: Callable[..., Response | str]):
    @wraps(view_func)
    def wrapped_view(**kwargs):
        if g.get("user") is None:
            return redirect(url_for("auth.login"))
        return view_func(**kwargs)

    return wrapped_view

