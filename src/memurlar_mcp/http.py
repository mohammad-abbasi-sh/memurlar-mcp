"""HTTP layer for memurlar_mcp.

Data source: Memurlar.Net (https://www.memurlar.net) — Türkiye's biggest
civil-servant portal (founded 1999/2000; ~21.9M visits/month, #2 education
site in Turkey per SEMrush Sep 2026): civil-servant news, public-sector
job announcements (ilan.memurlar.net), KPSS guidance and salary tools.
No login, no API key. Everything used here was verified live 2026-11-20:

- GET https://www.memurlar.net/sitemap-news.xml — Google News sitemap,
  141 recent articles with <loc> (/haber/<id>/), <news:title>,
  <news:publication_date> and <news:keywords>. This is the source for
  latest_news and (keyword scan) search_news. The site's own search
  (/arama/) is disallowed in robots.txt and is a POST form, so search is
  a scan of this sitemap — same honest approach as trthaber-mcp.
- GET https://www.memurlar.net/haber/<id>/<slug>.html — server-rendered
  article: breadcrumb categories, <h1 class="title">,
  <p class="description"> summary, "Haber Giriş" / "Son Güncelleme"
  <time datetime="..."> stamps, <div id="article-detail-container">
  body (<p> + <blockquote> in order; one ad widget div is skipped) and
  the comment count in #news-total-comments-<id>.
- GET https://www.memurlar.net/sitemap-job.xml — Google News sitemap,
  16 most recent job announcements with <loc> (/ilan/<id>/),
  <news:title>, <news:publication_date> and <news:keywords> (which often
  carry the application deadline, e.g. "Son başvuru tarihi 4 Aralık 2026").
- GET https://ilan.memurlar.net/ — job home page: 35 latest /ilan/ links
  plus the 21 category links (/kategori/<slug>/?Expire=false).
- GET https://ilan.memurlar.net/kategori/<slug>/?Expire=false — one
  category listing (15 /ilan/ links on the KPSS-A page, verified live).
- GET https://ilan.memurlar.net/ilan/<id>/<slug>.html — server-rendered
  job page carrying a full schema.org JobPosting JSON-LD block: title,
  description, datePosted, validThrough (deadline), occupationalCategory
  (= the ilan category), hiringOrganization, employmentType and
  qualifications (the full announcement text as escaped HTML).

Encoding: the whole site serves iso-8859-9 (declared in the meta
content-type and in the sitemap XML declarations). Responses are decoded
from raw bytes using the declared charset — never trust resp.text here.

Transport uses curl-cffi Chrome impersonation with a plain-requests
fallback (the proven Turkey-factory pattern), even though the site
currently answers plain HTTP 200. Requests are kept gentle (one at a
time, ~0.5s apart) and read-only.
"""
from __future__ import annotations

import re
import time

from curl_cffi import requests as _creq
import requests as _plain

BASE = "https://www.memurlar.net"
ILAN_BASE = "https://ilan.memurlar.net"
TIMEOUT = 30.0
MIN_INTERVAL = 0.5  # seconds between requests — be polite

_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

_last_fetch = 0.0


class MemurlarError(RuntimeError):
    pass


def _throttle() -> None:
    global _last_fetch
    wait = MIN_INTERVAL - (time.monotonic() - _last_fetch)
    if wait > 0:
        time.sleep(wait)
    _last_fetch = time.monotonic()


_PROFILES = ("chrome120", "chrome131", "safari17_0")
_MAX_ATTEMPTS = 2  # one retry with the next profile
_RETRY_BACKOFF = 1.0  # seconds between attempts
_profile_idx = 0  # sticky: profile that last succeeded


def _request(url: str, headers: dict, timeout: float = TIMEOUT):
    """GET with fingerprint rotation.

    Starts at the sticky profile (chrome120 on a fresh process), retries
    once with the next profile on HTTP 403/429 or a transport error, then
    returns the last response (so the caller raises the specific 403/429
    error) or raises a network error if every attempt failed at the
    transport.
    """
    global _profile_idx
    last_exc: Exception | None = None
    for k in range(_MAX_ATTEMPTS):
        profile = _PROFILES[(_profile_idx + k) % len(_PROFILES)]
        try:
            resp = _creq.get(url, impersonate=profile, headers=headers, timeout=timeout)
        except Exception as e:
            last_exc = e
            if k + 1 < _MAX_ATTEMPTS:
                time.sleep(_RETRY_BACKOFF)
                continue
            raise MemurlarError(f"network error fetching {url}: {e}") from e
        if resp.status_code in (403, 429):
            if k + 1 < _MAX_ATTEMPTS:
                time.sleep(_RETRY_BACKOFF)
                continue
            return resp
        _profile_idx = (_profile_idx + k) % len(_PROFILES)
        return resp
    raise MemurlarError(f"network error fetching {url}: {last_exc}") from last_exc


_CHARSET_RE = re.compile(
    r'charset\s*=\s*["\']?\s*([A-Za-z0-9_.-]+)', re.IGNORECASE
)


def _decode(raw: bytes, content_type: str = "") -> str:
    """Decode raw bytes using the charset the site declares.

    Memurlar.Net serves iso-8859-9 everywhere (meta content-type and the
    XML declarations); the Content-Type header may or may not carry it,
    so sniff the first bytes for a charset declaration first.
    """
    head = raw[:4096].decode("ascii", errors="ignore")
    m = _CHARSET_RE.search(content_type) or _CHARSET_RE.search(head)
    charset = (m.group(1) if m else "utf-8").lower().replace("_", "-")
    if charset in ("iso-8859-9", "iso8859-9", "latin5"):
        return raw.decode("iso-8859-9", errors="replace")
    try:
        return raw.decode(charset, errors="strict")
    except (LookupError, UnicodeDecodeError):
        return raw.decode("iso-8859-9", errors="replace")


def _get_text(url: str) -> str:
    """GET a URL, return the decoded text body.

    Raises MemurlarError with a human-readable message for HTTP errors.
    """
    _throttle()
    headers = dict(_HEADERS)
    try:
        resp = _request(url, headers)
        status, ctype, raw = resp.status_code, resp.headers.get("content-type", ""), resp.content
    except Exception:
        # Fallback transport: plain requests with a browser UA.
        try:
            resp = _plain.get(url, headers={**headers, "User-Agent": _UA}, timeout=TIMEOUT)
            status, ctype, raw = resp.status_code, resp.headers.get("content-type", ""), resp.content
        except MemurlarError:
            raise
        except Exception as e:
            raise MemurlarError(f"network error fetching {url}: {e}") from e
    if status == 403:
        raise MemurlarError(
            "www.memurlar.net refused the request (HTTP 403, bot wall)"
            " — try again later"
        )
    if status == 429:
        raise MemurlarError(
            "www.memurlar.net rate-limited the request (HTTP 429)"
            " — try again later"
        )
    if status == 404:
        raise MemurlarError(f"www.memurlar.net has no page at {url} (HTTP 404)")
    if status != 200:
        raise MemurlarError(
            f"www.memurlar.net returned HTTP {status} for {url}"
        )
    return _decode(raw, ctype)


def article_url(article_id: int | str) -> str:
    """Canonical article URL from a bare numeric id.

    The slug is cosmetic — /haber/<id>/ alone resolves — so a bare id is
    enough; a full URL is passed through unchanged (see parse.resolve_url).
    """
    return f"{BASE}/haber/{int(article_id)}/"


def job_url(job_id: int | str) -> str:
    """Canonical job URL from a bare numeric id (slug is cosmetic)."""
    return f"{ILAN_BASE}/ilan/{int(job_id)}/"


def category_url(slug: str) -> str:
    """One ilan category listing (open announcements only)."""
    return f"{ILAN_BASE}/kategori/{slug}/?Expire=false"


def fetch_news_sitemap() -> str:
    """The Google News sitemap (141 recent articles)."""
    return _get_text(f"{BASE}/sitemap-news.xml")


def fetch_job_sitemap() -> str:
    """The Google News sitemap for jobs (16 most recent announcements)."""
    return _get_text(f"{BASE}/sitemap-job.xml")


def fetch_article_page(url: str) -> str:
    """One server-rendered article page."""
    return _get_text(url)


def fetch_job_page(url: str) -> str:
    """One server-rendered job announcement page."""
    return _get_text(url)


def fetch_ilan_home() -> str:
    """The ilan home page (latest jobs + the 21 category links)."""
    return _get_text(f"{ILAN_BASE}/")


def fetch_category_page(slug: str) -> str:
    """One ilan category listing page."""
    return _get_text(category_url(slug))


def fetch_home_page() -> str:
    """The Memurlar.Net home page (used by the health check)."""
    return _get_text(f"{BASE}/")


def health_check() -> dict:
    """Two polite probes: the home page and the news sitemap.

    Returns {"status": "ok"|"blocked"|"error", "http_status": int|None,
    "url": ..., "detail": ...}. Used by the `memurlar_health` tool and
    the daily smoke CI.
    """
    url = f"{BASE}/"
    try:
        home = fetch_home_page()
        if "Memurlar.Net" not in home:
            return {
                "status": "error",
                "http_status": 200,
                "url": url,
                "detail": "home page returned 200 but no Memurlar.Net content",
            }
        news = fetch_news_sitemap()
        if "<news:title>" not in news and "<news:news>" not in news:
            return {
                "status": "error",
                "http_status": 200,
                "url": f"{BASE}/sitemap-news.xml",
                "detail": "news sitemap returned 200 but no news entries",
            }
    except MemurlarError as e:
        msg = str(e)
        if "403" in msg:
            return {"status": "blocked", "http_status": 403, "url": url, "detail": msg}
        if "429" in msg:
            return {"status": "blocked", "http_status": 429, "url": url, "detail": msg}
        return {"status": "error", "http_status": None, "url": url, "detail": msg}
    return {"status": "ok", "http_status": 200, "url": url}
