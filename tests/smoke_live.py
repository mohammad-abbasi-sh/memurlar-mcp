"""Daily smoke probe (CI): latest news + one article + one job + health.

Run with:  python tests/smoke_live.py
Exit 0 = site reachable, exit 1 = blocked/error (visible in CI).
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
    memurlar_latest_news,
)


def main() -> int:
    try:
        news = json.loads(memurlar_latest_news(5))
        assert "error" not in news, news.get("error")
        assert news["count"] == 5
        assert news["news"][0]["title"]
        art = json.loads(memurlar_get_article("1184613"))
        assert "error" not in art, art.get("error")
        assert art["title"].startswith("Erdoğan:")
        assert len(art["body"]) >= 20
        job = json.loads(memurlar_get_job("87027"))
        assert "error" not in job, job.get("error")
        assert job["category"] == "KPSS-A İlanları"
        assert job["deadline"] == "2026-12-19T00:05:00Z"
        health = json.loads(memurlar_health())
        assert health["status"] == "ok", health
        print(
            f"SMOKE OK: news[0]={news['news'][0]['title'][:60]} | "
            f"article body={len(art['body'])} blocks | "
            f"job={job['title'][:50]}"
        )
        return 0
    except Exception as e:  # noqa: BLE001 — smoke must report, not crash
        print(f"SMOKE FAIL: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
