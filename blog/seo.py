from __future__ import annotations

from datetime import datetime
from email.utils import format_datetime
from html import escape
from typing import Iterable

from flask import Blueprint, Response, current_app, request, url_for

from .db import get_database_connection


bp = Blueprint("seo", __name__)


def absolute_url(path: str) -> str:
    root = request.url_root.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return f"{root}{path}"


def iter_posts(limit: int | None = None) -> Iterable[dict]:
    db = get_database_connection()
    sql = (
        "SELECT p.id, p.title, p.body, p.created_at, p.updated_at, u.username "
        "FROM post p JOIN user u ON p.author_id = u.id ORDER BY p.created_at DESC"
    )
    if limit is not None:
        sql += " LIMIT ?"
        rows = db.execute(sql, (limit,)).fetchall()
    else:
        rows = db.execute(sql).fetchall()
    return [dict(r) for r in rows]


@bp.get("/rss.xml")
def feed() -> Response:
    site_title = current_app.config.get("SITE_TITLE", "My Blog")
    site_desc = current_app.config.get("SITE_DESC", "Latest posts")
    site_link = absolute_url(url_for("index"))
    items = []
    for post in iter_posts(limit=30):
        link = absolute_url(url_for("blog.detail", id=post["id"]))
        created_at = post.get("created_at")
        if isinstance(created_at, str):
            try:
                created_dt = datetime.fromisoformat(created_at)
            except Exception:
                created_dt = datetime.utcnow()
        else:
            created_dt = created_at or datetime.utcnow()
        pub_date = format_datetime(created_dt)
        description = escape(post.get("body") or "")
        items.append(
            f"""
      <item>
        <title>{escape(post['title'])}</title>
        <link>{link}</link>
        <guid>{link}</guid>
        <pubDate>{pub_date}</pubDate>
        <description><![CDATA[{description}]]></description>
      </item>
            """
        )
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{escape(site_title)}</title>
    <link>{site_link}</link>
    <description>{escape(site_desc)}</description>
    {''.join(items)}
  </channel>
</rss>
"""
    return Response(xml, mimetype="application/rss+xml; charset=utf-8")


@bp.get("/sitemap.xml")
def sitemap() -> Response:
    urls = [
        {
            "loc": absolute_url(url_for("index")),
            "lastmod": datetime.utcnow().date().isoformat(),
        }
    ]
    for post in iter_posts():
        last = post.get("updated_at") or post.get("created_at")
        if isinstance(last, datetime):
            lastmod = last.date().isoformat()
        elif isinstance(last, str):
            try:
                lastmod = datetime.fromisoformat(last).date().isoformat()
            except Exception:
                lastmod = datetime.utcnow().date().isoformat()
        else:
            lastmod = datetime.utcnow().date().isoformat()
        urls.append(
            {
                "loc": absolute_url(url_for("blog.detail", id=post["id"])),
                "lastmod": lastmod,
            }
        )
    xml_urls = "".join(
        f"<url><loc>{escape(u['loc'])}</loc><lastmod>{u['lastmod']}</lastmod></url>" for u in urls
    )
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{xml_urls}
</urlset>
"""
    return Response(xml, mimetype="application/xml; charset=utf-8")


@bp.get("/robots.txt")
def robots() -> Response:
    text = f"""User-agent: *
Allow: /
Sitemap: {absolute_url(url_for('seo.sitemap'))}
"""
    return Response(text, mimetype="text/plain; charset=utf-8")

