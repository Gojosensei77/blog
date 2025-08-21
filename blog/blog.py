from __future__ import annotations

from typing import cast

from flask import Blueprint, Response, abort, flash, g, redirect, render_template, request, url_for

from .auth import login_required
from .db import get_database_connection


bp = Blueprint("blog", __name__)


@bp.route("/")
def index() -> str:
    db_conn = get_database_connection()
    posts = db_conn.execute(
        """
        SELECT p.id, p.title, p.body, p.created_at, p.updated_at, p.author_id, u.username
        FROM post p JOIN user u ON p.author_id = u.id
        ORDER BY p.created_at DESC
        """
    ).fetchall()
    return cast(str, render_template("blog/index.html", posts=posts))


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create() -> str | Response:
    if request.method == "POST":
        title: str = request.form.get("title", "").strip()
        body: str = request.form.get("body", "").strip()
        error_message: str | None = None
        if not title:
            error_message = "Title is required."
        if error_message is None:
            db_conn = get_database_connection()
            db_conn.execute(
                "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
                (title, body, g.user["id"]),
            )
            db_conn.commit()
            return redirect(url_for("blog.index"))
        flash(error_message)
    return cast(str, render_template("blog/create.html"))


def get_post(post_id: int, check_author: bool = True):
    db_conn = get_database_connection()
    post = db_conn.execute(
        """
        SELECT p.id, p.title, p.body, p.created_at, p.updated_at, p.author_id, u.username
        FROM post p JOIN user u ON p.author_id = u.id
        WHERE p.id = ?
        """,
        (post_id,),
    ).fetchone()

    if post is None:
        abort(404, f"Post id {post_id} does not exist.")

    if check_author and post["author_id"] != g.user["id"]:
        abort(403)

    return post


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id: int) -> str | Response:
    post = get_post(id)

    if request.method == "POST":
        title: str = request.form.get("title", "").strip()
        body: str = request.form.get("body", "").strip()
        error_message: str | None = None
        if not title:
            error_message = "Title is required."

        if error_message is None:
            db_conn = get_database_connection()
            db_conn.execute(
                "UPDATE post SET title = ?, body = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (title, body, id),
            )
            db_conn.commit()
            return redirect(url_for("blog.index"))

        flash(error_message)

    return cast(str, render_template("blog/update.html", post=post))


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id: int) -> Response:
    get_post(id)
    db_conn = get_database_connection()
    db_conn.execute("DELETE FROM post WHERE id = ?", (id,))
    db_conn.commit()
    return redirect(url_for("blog.index"))

