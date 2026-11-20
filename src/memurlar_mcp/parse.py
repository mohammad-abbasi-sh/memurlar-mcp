"""Parsers for Memurlar.Net's server-rendered pages (stdlib only).

All markup shapes were verified against live pages fetched 2026-11-20;
offline tests run against recorded fixtures in tests/fixtures/.

Sources:
- sitemap-news.xml / sitemap-job.xml: Google News sitemaps (news: namespace)
- /haber/<id>/<slug>.html: article page
- /ilan/<id>/<slug>.html: job page (schema.org JobPosting JSON-LD)
- ilan home / category pages: /ilan/ link lists + /kategori/ links
"""
from __future__ import annotations

import html as _html
import json
import re
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------------
# Turkish-aware text helpers
# ---------------------------------------------------------------------------

_TR_LOWER_MAP = str.maketrans({"I": "ı", "İ": "i"})


def tr_lower(s: str) -> str:
    """Lowercase that respects Turkish dotted/dotless I.

    Python's str.lower() maps "I" -> "i" (English); Turkish needs
    "I" -> "ı" and "İ" -> "i". Without this, searching for "işçi"
    would miss "İŞÇİ" and vice versa.
    """
    return (s or "").translate(_TR_LOWER_MAP).lower()


def clean_text(s: str) -> str:
    """Unescape HTML entities, strip tags, collapse whitespace."""
    s = _html.unescape(s or "")
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _abs_url(url: str, base: str) -> str:
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("/"):
        return base.rstrip("/") + url
    return url


# ---------------------------------------------------------------------------
# Sitemaps (news + jobs)
# ---------------------------------------------------------------------------

_NS = {
    "s": "http://www.sitemaps.org/schemas/sitemap/0.9",
    "news": "http://www.google.com/schemas/sitemap-news/0.9",
    "image": "http://www.google.com/schemas/sitemap-image/1.1",
}

_ID_RE = re.compile(r"/(?:haber|ilan)/(\d+)/")


def _sitemap_items(xml_text: str) -> list[dict]:
    """Parse a Google News sitemap into item dicts (newest first)."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        raise ValueError(f"could not parse sitemap XML: {e}") from e
    items: list[dict] = []
    for url_el in root.findall("s:url", _NS):
        loc_el = url_el.find("s:loc", _NS)
        news_el = url_el.find("news:news", _NS)
        if loc_el is None or loc_el.text is None or news_el is None:
            continue
        loc = loc_el.text.strip()
        title_el = news_el.find("news:title", _NS)
        date_el = news_el.find("news:publication_date", _NS)
        kw_el = news_el.find("news:keywords", _NS)
        img_el = url_el.find("image:image/image:loc", _NS)
        m = _ID_RE.search(loc)
        items.append(
            {
                "id": int(m.group(1)) if m else None,
                "title": (title_el.text or "").strip() if title_el is not None else "",
                "url": loc,
                "published_at": (date_el.text or "").strip() if date_el is not None else "",
                "keywords": (kw_el.text or "").strip() if kw_el is not None else "",
                "image": (img_el.text or "").strip() if img_el is not None else "",
            }
        )
    return items


def parse_news_sitemap(xml_text: str) -> list[dict]:
    """141 recent articles from sitemap-news.xml (newest first)."""
    return _sitemap_items(xml_text)


def parse_job_sitemap(xml_text: str) -> list[dict]:
    """16 most recent announcements from sitemap-job.xml (newest first)."""
    return _sitemap_items(xml_text)


def search_items(items: list[dict], query: str) -> list[dict]:
    """Turkish-aware substring filter over title + keywords.

    The query is split on whitespace; every word must appear (in title
    or keywords). Returns matches in the original (newest-first) order.
    """
    words = [tr_lower(w) for w in (query or "").split() if w.strip()]
    if not words:
        return list(items)
    out = []
    for it in items:
        hay = tr_lower(f"{it.get('title', '')} {it.get('keywords', '')}")
        if all(w in hay for w in words):
            out.append(it)
    return out


# ---------------------------------------------------------------------------
# Article page (/haber/<id>/<slug>.html)
# ---------------------------------------------------------------------------

_BODY_END_MARKERS = (
    '<div class="spc:4x"',
    '<section class="content-items',
    '<div class="spc:8x"',
)


def _extract_body(html_text: str) -> list[str]:
    """Body paragraphs + blockquotes from #article-detail-container.

    The container holds the article <p>/<blockquote> blocks, one ad
    widget (<div id="zone-pharagraphsN"> wrapped in an empty <p>) and
    then a <div class="spc:4x"> spacer that marks the end of the body.
    Everything after that spacer (related news, comments) is excluded.
    """
    start = html_text.find('id="article-detail-container"')
    if start < 0:
        return []
    end = len(html_text)
    for marker in _BODY_END_MARKERS:
        j = html_text.find(marker, start)
        if 0 <= j < end:
            end = j
    seg = html_text[start:end]
    blocks: list[str] = []
    for m in re.finditer(r"<(p|blockquote)\b[^>]*>(.*?)</\1>", seg, re.S):
        txt = clean_text(m.group(2))
        if not txt:
            continue
        # skip the ad-widget placeholder paragraphs (empty after cleaning)
        if "widget-article" in m.group(0) and len(txt) < 5:
            continue
        blocks.append(txt)
    return blocks


def parse_article_page(html_text: str, url: str = "") -> dict:
    """Parse one article page.

    Raises ValueError when the page has no recognizable article (e.g. a
    404 page or a changed layout).
    """
    title_m = re.search(r'<h1 class="title">(.*?)</h1>', html_text, re.S)
    if not title_m:
        raise ValueError("no article title found — page layout may have changed")
    title = clean_text(title_m.group(1))

    # Breadcrumb categories, e.g. ["Ana sayfa", "Haberler", "Siyasi"].
    categories: list[str] = []
    bc = re.search(r'<div class="breadcrumb">(.*?)</div>', html_text, re.S)
    if bc:
        categories = [
            clean_text(a)
            for a in re.findall(r"<a[^>]*>(.*?)</a>", bc.group(1), re.S)
            if clean_text(a)
        ]

    summary = ""
    desc = re.search(r'<p class="description">(.*?)</p>', html_text, re.S)
    if desc:
        summary = clean_text(desc.group(1))

    published_at = ""
    pub = re.search(r"Haber Giriş\s*:<time[^>]*datetime=\"([^\"]+)\"", html_text)
    if pub:
        published_at = pub.group(1)
    updated_at = ""
    upd = re.search(r"Son Güncelleme\s*:<time[^>]*datetime=\"([^\"]+)\"", html_text)
    if upd:
        updated_at = upd.group(1)

    comments = None
    cm = re.search(r'id="news-total-comments-(\d+)">(\d+)<', html_text)
    if cm:
        comments = int(cm.group(2))

    image = ""
    hi = re.search(
        r'<div class="headline-image">.*?<img[^>]*src="([^"]+)"', html_text, re.S
    )
    if hi:
        image = _abs_url(_html.unescape(hi.group(1)), "https://www.memurlar.net")

    article_id = None
    m = _ID_RE.search(url or "")
    if m:
        article_id = int(m.group(1))
    elif cm:
        article_id = int(cm.group(1))

    body = _extract_body(html_text)
    return {
        "id": article_id,
        "title": title,
        "url": url,
        "categories": categories,
        "summary": summary,
        "published_at": published_at,
        "updated_at": updated_at,
        "source": "Memurlar.Net",
        "comments_count": comments,
        "image": image,
        "body": body,
        "body_text": "\n\n".join(body),
    }


# ---------------------------------------------------------------------------
# Job page (/ilan/<id>/<slug>.html) — JobPosting JSON-LD
# ---------------------------------------------------------------------------

def _html_to_paragraphs(fragment: str) -> list[str]:
    """The qualifications field is escaped HTML: <p>/<li> blocks."""
    out: list[str] = []
    for m in re.finditer(r"<(p|li|h[1-4])\b[^>]*>(.*?)</\1>", fragment, re.S):
        txt = clean_text(m.group(2))
        if txt:
            out.append(("• " + txt) if m.group(1) == "li" else txt)
    if not out:
        txt = clean_text(fragment)
        if txt:
            out = [txt]
    return out


def parse_job_page(html_text: str, url: str = "") -> dict:
    """Parse one job announcement via its JobPosting JSON-LD block.

    Raises ValueError when no JobPosting block is found.
    """
    posting = None
    for m in re.finditer(
        r'<script type="application/ld\+json">(.*?)</script>', html_text, re.S
    ):
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("@type") == "JobPosting":
            posting = data
            break
    if posting is None:
        raise ValueError("no JobPosting JSON-LD found — page layout may have changed")

    qualifications_html = _html.unescape(posting.get("qualifications") or "")
    details = _html_to_paragraphs(qualifications_html)

    job_id = None
    m = _ID_RE.search(url or posting.get("url") or "")
    if m:
        job_id = int(m.group(1))

    org = posting.get("hiringOrganization") or {}
    return {
        "id": job_id,
        "title": posting.get("title", ""),
        "url": posting.get("url") or url,
        "summary": posting.get("description", ""),
        "posted_at": posting.get("datePosted", ""),
        "deadline": posting.get("validThrough", ""),
        "category": posting.get("occupationalCategory", "")
        or posting.get("industry", ""),
        "organization": org.get("name", "") if isinstance(org, dict) else "",
        "employment_type": posting.get("employmentType", ""),
        "work_hours": posting.get("workHours", ""),
        "details": details,
        "details_text": "\n\n".join(details),
    }


# ---------------------------------------------------------------------------
# Ilan listings (home + category pages)
# ---------------------------------------------------------------------------

_ILAN_LINK_RE = re.compile(
    r'href="(/ilan/(\d+)/([^"]*?)\.html)"[^>]*>(.*?)</a>', re.S
)


def parse_ilan_links(html_text: str) -> list[dict]:
    """All /ilan/<id>/<slug>.html links on a listing page, deduped by id.

    Anchor text is the announcement title; the first occurrence wins
    (listings repeat some links in sidebars).
    """
    out: list[dict] = []
    seen: set[int] = set()
    for m in _ILAN_LINK_RE.finditer(html_text):
        job_id = int(m.group(2))
        if job_id in seen:
            continue
        seen.add(job_id)
        out.append(
            {
                "id": job_id,
                "title": clean_text(m.group(4)),
                "url": f"https://ilan.memurlar.net{m.group(1)}",
                "keywords": "",
                "published_at": "",
                "image": "",
            }
        )
    return out


_CAT_LINK_RE = re.compile(
    r'href="/kategori/([^"/]+)/\?Expire=false"[^>]*>(.*?)</a>', re.S
)


def parse_categories(html_text: str) -> dict[str, str]:
    """The 21 ilan category slugs -> Turkish labels (from the ilan home)."""
    cats: dict[str, str] = {}
    for m in _CAT_LINK_RE.finditer(html_text):
        label = clean_text(m.group(2))
        if label:
            cats[m.group(1)] = label
    return cats


# ---------------------------------------------------------------------------
# URL resolution for tool inputs
# ---------------------------------------------------------------------------

def resolve_article_url(value: str) -> str:
    """Accept a bare numeric id, a /haber/... path or a full article URL."""
    value = (value or "").strip()
    if value.isdigit():
        # The slug is cosmetic — /haber/<id>/ alone resolves.
        return f"https://www.memurlar.net/haber/{int(value)}/"
    if value.startswith("/haber/"):
        return "https://www.memurlar.net" + value
    if value.startswith("http"):
        return value
    raise ValueError(
        f"cannot resolve article from {value!r}: pass a numeric id or a memurlar.net article URL"
    )


def resolve_job_url(value: str) -> str:
    """Accept a bare numeric id, a /ilan/... path or a full job URL."""
    value = (value or "").strip()
    if value.isdigit():
        # The slug is cosmetic — /ilan/<id>/ alone resolves.
        return f"https://ilan.memurlar.net/ilan/{int(value)}/"
    if value.startswith("/ilan/"):
        return "https://ilan.memurlar.net" + value
    if value.startswith("http"):
        return value
    raise ValueError(
        f"cannot resolve job from {value!r}: pass a numeric id or an ilan.memurlar.net job URL"
    )
