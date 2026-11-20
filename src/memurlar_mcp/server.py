"""MCP server: unofficial read-only access to Memurlar.Net (Turkish civil-servant news + public-sector job announcements)."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

from . import http as _http
from . import parse as _P

mcp = FastMCP("memurlar-mcp")

INSTRUCTIONS = """\
Unofficial read-only MCP server for Memurlar.Net (www.memurlar.net) — \
Türkiye's biggest civil-servant portal (founded 1999/2000, ~21.9M \
visits/month, #2 education site in Turkey): civil-servant news \
(memurlar_latest_news, memurlar_search_news, memurlar_get_article) \
and public-sector job announcements on ilan.memurlar.net \
(memurlar_latest_jobs, memurlar_search_jobs, memurlar_get_job, \
memurlar_list_job_categories). News lists come from the site's Google \
News sitemap (141 recent articles with title, date and keywords); \
article pages are server-rendered (title, categories, summary, \
published/updated stamps, full body, comment count). Job announcements \
come from the job sitemap + the ilan home/category listings; each job \
detail is the page's schema.org JobPosting data (title, description, \
posted date, application deadline, category, full announcement text). \
Search is a Turkish-aware keyword scan of the sitemaps (the site's own \
/arama/ search is a POST form disallowed in robots.txt). No login, no \
API key. Read-only; transport uses Chrome TLS impersonation with a \
plain-requests fallback; requests are spaced ~0.5s apart. Built by \
Mohammad Abbasi (mohammad-abbasi-sh) — https://almanibama.ir · \
https://mabbasi.ir — Turkey MCP factory.\
"""

_SOURCE = "www.memurlar.net"
_DISCLAIMER = (
    "Unofficial read-only Memurlar.Net data from the site's public "
    "sitemaps and pages; verify on the official site before acting on "
    "it. Job deadlines come from the announcement pages — always check "
    "the official announcement for the current status."
)


def _envelope() -> dict:
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": _SOURCE,
        "disclaimer": _DISCLAIMER,
    }


def _ok(payload: dict) -> str:
    return json.dumps({**_envelope(), **payload}, ensure_ascii=False)


def _err(e: Exception) -> str:
    return _ok({"error": str(e)})


def _limit(limit: int) -> int:
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 10
    return max(1, min(limit, 50))


@mcp.tool()
def memurlar_latest_news(limit: int = 10) -> str:
    """Latest civil-servant news from Memurlar.Net (newest first).

    limit: how many items to return (1-50, default 10). Returns each
    article's id, title, URL, publication date, keywords and image —
    sourced from the site's Google News sitemap (141 recent articles).
    Use memurlar_get_article for the full text of one article."""
    try:
        items = _P.parse_news_sitemap(_http.fetch_news_sitemap())
        return _ok({"count": len(items[: _limit(limit)]), "news": items[: _limit(limit)]})
    except (ValueError, _http.MemurlarError) as e:
        return _err(e)


@mcp.tool()
def memurlar_search_news(query: str, limit: int = 10) -> str:
    """Search recent Memurlar.Net news by keyword (Turkish-aware).

    query: one or more words, e.g. "maaş zammı" or "öğretmen" — every
    word must appear in the title or keywords (Turkish dotted/dotless
    I handled). limit: max results (1-50, default 10). Searches the
    141 most recent articles in the site's news sitemap; the site's own
    search form is a POST endpoint, so this is a scan of the sitemap,
    not a full-archive search."""
    try:
        query = (query or "").strip()
        if not query:
            raise ValueError("query must not be empty")
        items = _P.parse_news_sitemap(_http.fetch_news_sitemap())
        found = _P.search_items(items, query)
        return _ok(
            {
                "query": query,
                "count": len(found[: _limit(limit)]),
                "total_matches": len(found),
                "news": found[: _limit(limit)],
            }
        )
    except (ValueError, _http.MemurlarError) as e:
        return _err(e)


@mcp.tool()
def memurlar_get_article(article: str) -> str:
    """Full text of one Memurlar.Net news article.

    article: a numeric article id (e.g. "1184613") or a full article
    URL (https://www.memurlar.net/haber/1184613/...). Returns title,
    URL, breadcrumb categories, summary, published/updated stamps,
    source, comment count, headline image and the full body text
    (paragraphs + quoted statements in order)."""
    try:
        url = _P.resolve_article_url(article)
        page = _http.fetch_article_page(url)
        return _ok(_P.parse_article_page(page, url))
    except (ValueError, _http.MemurlarError) as e:
        return _err(e)


@mcp.tool()
def memurlar_latest_jobs(limit: int = 10, category: str = "") -> str:
    """Latest public-sector job announcements from ilan.memurlar.net.

    limit: how many items to return (1-50, default 10). category: an
    optional ilan category slug (see memurlar_list_job_categories,
    e.g. "kpss-a-ilanlari", "daimi-isci-ilanlari") to list that
    category's open announcements instead. Without a category, returns
    the 16 most recent announcements from the job sitemap (title, date,
    keywords — which often carry the application deadline). Use
    memurlar_get_job for the full announcement text and deadline."""
    try:
        category = (category or "").strip()
        if category:
            page = _http.fetch_category_page(category)
            items = _P.parse_ilan_links(page)
            return _ok(
                {
                    "category": category,
                    "count": len(items[: _limit(limit)]),
                    "jobs": items[: _limit(limit)],
                }
            )
        items = _P.parse_job_sitemap(_http.fetch_job_sitemap())
        return _ok({"count": len(items[: _limit(limit)]), "jobs": items[: _limit(limit)]})
    except (ValueError, _http.MemurlarError) as e:
        return _err(e)


@mcp.tool()
def memurlar_search_jobs(query: str, limit: int = 10) -> str:
    """Search recent public-sector job announcements by keyword.

    query: one or more words, e.g. "zabıta" or "üniversite öğretim
    üyesi" — every word must appear in the title or keywords (Turkish
    dotted/dotless I handled). limit: max results (1-50, default 10).
    Scans the job sitemap (16 most recent) plus the ilan home page
    (35 latest listings), deduplicated by id — a scan of recent
    announcements, not a full-archive search."""
    try:
        query = (query or "").strip()
        if not query:
            raise ValueError("query must not be empty")
        items = _P.parse_job_sitemap(_http.fetch_job_sitemap())
        seen = {it["id"] for it in items}
        for it in _P.parse_ilan_links(_http.fetch_ilan_home()):
            if it["id"] not in seen:
                seen.add(it["id"])
                items.append(it)
        found = _P.search_items(items, query)
        return _ok(
            {
                "query": query,
                "count": len(found[: _limit(limit)]),
                "total_matches": len(found),
                "jobs": found[: _limit(limit)],
            }
        )
    except (ValueError, _http.MemurlarError) as e:
        return _err(e)


@mcp.tool()
def memurlar_get_job(job: str) -> str:
    """Full text of one public-sector job announcement.

    job: a numeric job id (e.g. "87027") or a full announcement URL
    (https://ilan.memurlar.net/ilan/87027/...). Returns title, URL,
    summary, posted date, application deadline (validThrough),
    category, organization, employment type, work hours and the full
    announcement text (requirements, conditions, application steps).
    Always check the official announcement for the current status."""
    try:
        url = _P.resolve_job_url(job)
        page = _http.fetch_job_page(url)
        return _ok(_P.parse_job_page(page, url))
    except (ValueError, _http.MemurlarError) as e:
        return _err(e)


@mcp.tool()
def memurlar_list_job_categories() -> str:
    """The 21 ilan.memurlar.net job categories (slug -> Turkish label).

    Use a slug with memurlar_latest_jobs(category=...) to list that
    category's open announcements, e.g. "kpss-a-ilanlari" (KPSS-A),
    "daimi-isci-ilanlari" (permanent workers), "akademik-ilanlar-devlet"
    (state university academic posts)."""
    try:
        cats = _P.parse_categories(_http.fetch_ilan_home())
        return _ok(
            {
                "count": len(cats),
                "categories": [{"slug": k, "label": v} for k, v in cats.items()],
            }
        )
    except (ValueError, _http.MemurlarError) as e:
        return _err(e)


@mcp.tool()
def memurlar_health() -> str:
    """Check whether Memurlar.Net is reachable right now.

    Returns status ok (HTTP 200), blocked (HTTP 403/429 — bot wall or
    rate limit) or error, plus the HTTP status and the probed URL.
    Two polite requests (home page + news sitemap); it fetches no
    article or job content."""
    return _ok(_http.health_check())


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    import sys

    sys.exit(main())
