from __future__ import annotations

from typing import cast

from flask import Blueprint, Response, abort, flash, g, redirect, render_template, request, url_for

from .auth import login_required
from .db import get_database_connection


bp = Blueprint("blog", __name__)


@bp.route("/")
def index() -> str:
    db_conn = get_database_connection()
    query_text = (request.args.get("q") or "").strip()
    try:
        page = max(int(request.args.get("page", 1)), 1)
    except Exception:
        page = 1
    per_page = 10
    offset = (page - 1) * per_page

    where_clause = ""
    params: list[object] = []
    if query_text:
        where_clause = "WHERE p.title LIKE ? OR p.body LIKE ?"
        like = f"%{query_text}%"
        params.extend([like, like])

    posts = db_conn.execute(
        f"""
        SELECT p.id, p.title, p.body, p.created_at, p.updated_at, p.author_id, u.username
        FROM post p JOIN user u ON p.author_id = u.id
        {where_clause}
        ORDER BY p.created_at DESC
        LIMIT ? OFFSET ?
        """,
        (*params, per_page, offset),
    ).fetchall()

    total_row = db_conn.execute(
        f"SELECT COUNT(*) AS count FROM post p {where_clause}", (*params,)
    ).fetchone()
    total = int(total_row["count"]) if total_row else 0
    total_pages = max((total + per_page - 1) // per_page, 1)

    return cast(
        str,
        render_template(
            "blog/index.html",
            posts=posts,
            q=query_text,
            page=page,
            total_pages=total_pages,
        ),
    )


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


@bp.route("/<int:id>")
def detail(id: int) -> str:
    post = get_post(id, check_author=False)
    return cast(str, render_template("blog/detail.html", post=post))