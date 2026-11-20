"""Offline tests for memurlar_mcp parsers (recorded fixtures, no network).

Fixtures (recorded 2026-11-20 from www.memurlar.net / ilan.memurlar.net;
the site's Google site-verification token was scrubbed to REDACTED):
- sitemap-news.xml — news sitemap, 141 recent articles
- sitemap-job.xml — job sitemap, 16 most recent announcements
- article-1184613.html — "Erdoğan: Eleştiri maskesi altında hakareti asla
  kabullenemeyiz" (Siyasi, 19 Nov 2026, 23 comments, 25 body blocks)
- job-87027.html — "İçişleri Bakanlığı 60 Kaymakam Adayı Alacak"
  (KPSS-A, deadline 2026-12-19, 54 detail blocks)
- ilan-home.html — ilan home (32 unique /ilan/ links, 21 categories)
- category-kpss-a.html — KPSS-A listing (15 /ilan/ links)
- home.html — the home page (health-check probe)

Run with:  python -m pytest tests/test_parse.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from memurlar_mcp import parse as P  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures"


def _read(name: str) -> str:
    return (FIX / name).read_text(encoding="iso-8859-9")


# --- sitemaps ---------------------------------------------------------------

def test_news_sitemap_count_and_first():
    items = P.parse_news_sitemap(_read("sitemap-news.xml"))
    assert len(items) == 141
    first = items[0]
    assert first["id"] == 1184701
    assert first["title"] == "Acar: Kamu bütçesinden hiçbir kaynak kullanılmadı"
    assert first["url"] == "https://www.memurlar.net/haber/1184701/"
    assert first["published_at"] == "2026-11-20T12:05+03:00"
    assert first["keywords"] == "fon soruşturması"
    assert first["image"].endswith("/common/news/images/1184701/headline.jpg")
    # newest first, oldest last
    assert items[-1]["published_at"] == "2026-11-19T00:01+03:00"


def test_job_sitemap_count_and_first():
    items = P.parse_job_sitemap(_read("sitemap-job.xml"))
    assert len(items) == 16
    first = items[0]
    assert first["id"] == 87037
    assert first["title"] == "Atatürk Üniversitesi Öğretim Üyesi Alım İlanı"
    assert first["url"] == "https://ilan.memurlar.net/ilan/87037/"
    assert first["published_at"] == "2026-11-20T01:45+03:00"
    assert "Son başvuru tarihi 4 Aralık 2026" in first["keywords"]


def test_search_turkish_aware():
    news = P.parse_news_sitemap(_read("sitemap-news.xml"))
    # dotted/dotless I: "ÖĞRETMEN" (upper) must match "öğretmen" (lower)
    assert P.search_items(news, "öğretmen") == P.search_items(news, "ÖĞRETMEN")
    assert len(P.search_items(news, "öğretmen")) == 4
    assert P.tr_lower("İŞÇİ IĞDIR") == "işçi ığdır"
    # every word must match
    assert len(P.search_items(news, "öğretmen maaş")) <= len(
        P.search_items(news, "öğretmen")
    )
    assert P.search_items(news, "zzzzzqqqx") == []
    assert P.search_items(news, "") == news


# --- article page -----------------------------------------------------------

def test_article_page_fields():
    art = P.parse_article_page(
        _read("article-1184613.html"),
        "https://www.memurlar.net/haber/1184613/erdogan-elestiri-maskesi-altinda-hakareti-asla-kabullenemeyiz.html",
    )
    assert art["id"] == 1184613
    assert art["title"] == "Erdoğan: Eleştiri maskesi altında hakareti asla kabullenemeyiz"
    assert art["categories"] == ["Ana sayfa", "Haberler", "Siyasi"]
    assert art["published_at"] == "2026-11-19T14:34"
    assert art["updated_at"] == "2026-11-19T14:50"
    assert art["source"] == "Memurlar.Net"
    assert art["comments_count"] == 23
    assert art["image"].endswith(
        "/common/news/images/1184613/erdogan-elestiri-maskesi-altinda-hakareti-asla-kabullenemeyiz.jpg"
    )
    assert art["summary"].startswith(
        'Cumhurbaşkanı Recep Tayyip Erdoğan, "Eleştiri maskesi altında'
    )


def test_article_body_blocks():
    art = P.parse_article_page(
        _read("article-1184613.html"),
        "https://www.memurlar.net/haber/1184613/x.html",
    )
    assert len(art["body"]) == 25
    assert art["body"][0].startswith("Cumhurbaşkanı Recep Tayyip Erdoğan")
    assert art["body"][-1].startswith(
        "Cumhuriyet Halk Partisi'nden (CHP) istifa eden"
    )
    # quoted statements (blockquote) are kept in order
    assert any("Son dönemde puslu havayı" in b for b in art["body"])
    # ad-widget placeholders and related-news items are excluded
    assert not any("zone-pharagraphs" in b for b in art["body"])
    assert not any("Acar: Kamu bütçesinden" in b for b in art["body"])
    assert "Cumhurbaşkanı" in art["body_text"]
    assert "AK PARTİ" in art["body_text"]


def test_article_page_no_title_raises():
    try:
        P.parse_article_page("<html><body>no article here</body></html>", "")
    except ValueError as e:
        assert "no article title" in str(e)
    else:
        raise AssertionError("expected ValueError")


# --- job page ---------------------------------------------------------------

def test_job_page_fields():
    job = P.parse_job_page(
        _read("job-87027.html"),
        "https://ilan.memurlar.net/ilan/87027/icisleri-bakanligi-60-kaymakam-adayi-alacak.html",
    )
    assert job["id"] == 87027
    assert job["title"] == "İçişleri Bakanlığı 60 Kaymakam Adayı Alacak"
    assert job["posted_at"] == "2026-11-19T00:05:00Z"
    assert job["deadline"] == "2026-12-19T00:05:00Z"
    assert job["category"] == "KPSS-A İlanları"
    assert job["employment_type"] == "FULL_TIME"
    assert job["work_hours"] == "40 hours per week"
    assert "KPSSP32" in job["summary"]
    assert "1-7 Aralık 2026" in job["summary"]


def test_job_details_blocks():
    job = P.parse_job_page(
        _read("job-87027.html"),
        "https://ilan.memurlar.net/ilan/87027/x.html",
    )
    assert len(job["details"]) == 54
    assert job["details"][0] == "İçişleri Bakanlığından:"
    assert job["details"][1] == "KAYMAKAM ADAYLIĞI SINAV İLANI"
    assert any("KPSSP32" in d for d in job["details"])
    assert any("35 yaşını" in d for d in job["details"])
    assert "T.C. İçişleri Bakanlığı" in job["details_text"]


def test_job_page_no_posting_raises():
    try:
        P.parse_job_page("<html></html>", "")
    except ValueError as e:
        assert "no JobPosting" in str(e)
    else:
        raise AssertionError("expected ValueError")


# --- listings ---------------------------------------------------------------

def test_ilan_home_links_and_categories():
    home = _read("ilan-home.html")
    links = P.parse_ilan_links(home)
    assert len(links) == 32  # 35 raw links, 32 unique ids
    assert links[0]["id"] == 87018
    assert links[0]["title"] == "Tekirdağ Su ve Kanalizasyon İdaresi 16 İşçi Alacak"
    assert links[0]["url"].startswith("https://ilan.memurlar.net/ilan/87018/")
    cats = P.parse_categories(home)
    assert len(cats) == 21
    assert cats["kpss-a-ilanlari"] == "KPSS-A İlanları"
    assert cats["daimi-isci-ilanlari"] == "Daimi İşçi İlanları"
    assert cats["akademik-ilanlar-devlet"] == "Akademik İlanlar (Devlet)"


def test_category_page_links():
    links = P.parse_ilan_links(_read("category-kpss-a.html"))
    assert len(links) == 15
    assert links[0]["id"] == 87026
    assert any(l["id"] == 87027 for l in links)  # the kaymakam job
    assert all(l["url"].startswith("https://ilan.memurlar.net/ilan/") for l in links)


# --- URL resolution ---------------------------------------------------------

def test_resolve_urls():
    assert P.resolve_article_url("1184613") == "https://www.memurlar.net/haber/1184613/"
    assert P.resolve_job_url("87027") == "https://ilan.memurlar.net/ilan/87027/"
    assert (
        P.resolve_article_url("/haber/1184613/x.html")
        == "https://www.memurlar.net/haber/1184613/x.html"
    )
    assert (
        P.resolve_job_url("/ilan/87027/x.html")
        == "https://ilan.memurlar.net/ilan/87027/x.html"
    )
    assert (
        P.resolve_article_url("https://www.memurlar.net/haber/1184613/x.html")
        == "https://www.memurlar.net/haber/1184613/x.html"
    )
    try:
        P.resolve_article_url("not-an-id")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
