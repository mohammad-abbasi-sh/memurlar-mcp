"""Live tests: hit the real Memurlar.Net site (no key, read-only).

Kept small and polite (~0.5s between requests, one call per tool).
Assertions are date-independent (counts and shapes, not frozen data).

Run with:  python -m pytest tests/test_live.py -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from memurlar_mcp.server import (  # noqa: E402
    memurlar_get_article,
    memurlar_get_job,
    memurlar_health,
    memurlar_latest_jobs,
    memurlar_latest_news,
    memurlar_list_job_categories,
    memurlar_search_jobs,
    memurlar_search_news,
)


def _parse(out: str) -> dict:
    return json.loads(out)


def test_live_latest_news():
    out = _parse(memurlar_latest_news(10))
    assert "error" not in out, out.get("error")
    assert out["count"] == 10
    assert len(out["news"]) == 10
    first = out["news"][0]
    assert first["id"] and first["title"]
    assert first["url"].startswith("https://www.memurlar.net/haber/")
    assert first["published_at"]
    # newest first
    assert out["news"][0]["published_at"] >= out["news"][-1]["published_at"]


def test_live_search_news():
    out = _parse(memurlar_search_news("öğretmen", 10))
    assert "error" not in out, out.get("error")
    assert out["total_matches"] >= 1
    assert all(
        "öğretmen" in (n["title"] + " " + n["keywords"]).lower()
        for n in out["news"]
    )
    empty = _parse(memurlar_search_news("zzzzzqqqx", 10))
    assert "error" not in empty, empty.get("error")
    assert empty["total_matches"] == 0


def test_live_get_article():
    out = _parse(memurlar_get_article("1184613"))
    assert "error" not in out, out.get("error")
    assert out["id"] == 1184613
    assert out["title"] == "Erdoğan: Eleştiri maskesi altında hakareti asla kabullenemeyiz"
    assert "Siyasi" in out["categories"]
    assert out["published_at"] == "2026-11-19T14:34"
    assert len(out["body"]) >= 20
    assert "Cumhurbaşkanı" in out["body_text"]


def test_live_latest_jobs():
    out = _parse(memurlar_latest_jobs(10))
    assert "error" not in out, out.get("error")
    assert out["count"] == 10
    assert len(out["jobs"]) == 10
    first = out["jobs"][0]
    assert first["id"] and first["title"]
    assert first["url"].startswith("https://ilan.memurlar.net/ilan/")
    assert first["published_at"]


def test_live_latest_jobs_category():
    out = _parse(memurlar_latest_jobs(10, category="kpss-a-ilanlari"))
    assert "error" not in out, out.get("error")
    assert out["category"] == "kpss-a-ilanlari"
    assert out["count"] >= 5
    assert all(j["url"].startswith("https://ilan.memurlar.net/ilan/") for j in out["jobs"])


def test_live_search_jobs():
    out = _parse(memurlar_search_jobs("üniversite", 10))
    assert "error" not in out, out.get("error")
    assert out["total_matches"] >= 1
    assert all(
        "üniversite" in (j["title"] + " " + j["keywords"]).lower()
        for j in out["jobs"]
    )


def test_live_get_job():
    out = _parse(memurlar_get_job("87027"))
    assert "error" not in out, out.get("error")
    assert out["id"] == 87027
    assert out["title"] == "İçişleri Bakanlığı 60 Kaymakam Adayı Alacak"
    assert out["category"] == "KPSS-A İlanları"
    assert out["deadline"] == "2026-12-19T00:05:00Z"
    assert len(out["details"]) >= 40
    assert "KPSSP32" in out["details_text"]


def test_live_list_categories():
    out = _parse(memurlar_list_job_categories())
    assert "error" not in out, out.get("error")
    assert out["count"] == 21
    slugs = {c["slug"] for c in out["categories"]}
    assert "kpss-a-ilanlari" in slugs
    assert "daimi-isci-ilanlari" in slugs
    assert "akademik-ilanlar-devlet" in slugs


def test_live_health():
    out = _parse(memurlar_health())
    assert out["status"] == "ok", out
    assert out["http_status"] == 200
