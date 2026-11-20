# memurlar-mcp 🇹🇷

mcp-name: io.github.mohammad-abbasi-sh/memurlar-mcp

Unofficial **read-only** MCP server for **Memurlar.Net** (www.memurlar.net) — Türkiye's biggest civil-servant portal (founded 1999/2000, ~21.9M visits/month, #2 education site in Turkey): **civil-servant news** (latest headlines, keyword search, full article text) and **public-sector job announcements** on ilan.memurlar.net (latest announcements, keyword search, 21 categories, full announcement text with the application deadline).

> Part of the "Turkey MCP factory". Not affiliated with Memurlar.Net. Data comes from Memurlar.Net's own public sitemaps and server-rendered pages — no login, no API key, read-only. Job deadlines come from the announcement pages; always check the official announcement for the current status.

## For AI agents

- **News**: `memurlar_latest_news` returns the newest headlines from the site's Google News sitemap (141 recent articles with id, title, URL, publication date, keywords and image). `memurlar_search_news` scans the same sitemap by keyword — `"öğretmen"`, `"maaş zammı"` — Turkish-aware (dotted/dotless I handled, so `"ÖĞRETMEN"` matches `"öğretmen"`); every word must match the title or keywords.
- **Article**: `memurlar_get_article` takes a numeric id (`"1184613"`) or a full URL and returns title, breadcrumb categories, summary, published/updated stamps, comment count, headline image and the full body (paragraphs + quoted statements in order).
- **Jobs**: `memurlar_latest_jobs` returns the 16 most recent announcements from the job sitemap (title, date, keywords — which often carry the deadline, e.g. "Son başvuru tarihi 4 Aralık 2026"); pass `category` (e.g. `"kpss-a-ilanlari"`) to list that category's open announcements instead. `memurlar_search_jobs` scans the job sitemap plus the ilan home page (35 latest listings), deduplicated by id.
- **Job detail**: `memurlar_get_job` takes a numeric id (`"87027"`) or a full URL and returns the page's schema.org JobPosting data — title, summary, posted date, application deadline (`validThrough`), category, employment type, work hours and the full announcement text (requirements, conditions, application steps).
- **Categories**: `memurlar_list_job_categories` returns the 21 ilan categories (slug → Turkish label), e.g. `"kpss-a-ilanlari"` (KPSS-A), `"daimi-isci-ilanlari"` (permanent workers), `"akademik-ilanlar-devlet"` (state university academic posts).
- Every response carries `fetched_at` (UTC) and `source: www.memurlar.net`.

## Install

```bash
uvx memurlar-mcp
```

Or add to your MCP client config (e.g. Claude Desktop):

```json
{
  "mcpServers": {
    "memurlar": {
      "command": "uvx",
      "args": ["memurlar-mcp"]
    }
  }
}
```

## Tools

| Tool | What it does |
| --- | --- |
| `memurlar_latest_news` | Latest civil-servant news (newest first, from the news sitemap) |
| `memurlar_search_news` | Keyword search over the 141 most recent news articles |
| `memurlar_get_article` | Full text of one news article (id or URL) |
| `memurlar_latest_jobs` | Latest job announcements, optionally filtered by category |
| `memurlar_search_jobs` | Keyword search over recent job announcements |
| `memurlar_get_job` | Full text of one job announcement with deadline (id or URL) |
| `memurlar_list_job_categories` | The 21 ilan categories (slug → Turkish label) |
| `memurlar_health` | Is Memurlar.Net reachable right now? |

## Example

Latest news, 20 November 2026:

```json
{ "count": 2,
  "news": [
    { "id": 1184701, "title": "Acar: Kamu bütçesinden hiçbir kaynak kullanılmadı",
      "url": "https://www.memurlar.net/haber/1184701/",
      "published_at": "2026-11-20T12:05+03:00", "keywords": "fon soruşturması",
      "image": "https://www.memurlar.net/common/news/images/1184701/headline.jpg" },
    { "id": 1184700, "title": "Sahte faturalarla 100 milyon liralık dolandırıcılık",
      "url": "https://www.memurlar.net/haber/1184700/",
      "published_at": "2026-11-20T12:03+03:00", "keywords": "sahte faturalar,Yemek şirketi" } ] }
```

Job detail for `"87027"` (İçişleri Bakanlığı, 60 kaymakam adayı):

```json
{ "id": 87027, "title": "İçişleri Bakanlığı 60 Kaymakam Adayı Alacak",
  "posted_at": "2026-11-19T00:05:00Z", "deadline": "2026-12-19T00:05:00Z",
  "category": "KPSS-A İlanları", "employment_type": "FULL_TIME",
  "summary": "İçişleri Bakanlığı, Mülki İdare Amirliği Hizmetleri Sınıfında görevlendirilmek üzere 60 kaymakam adayı alımı yapacağını duyurdu. Adayların 2025 veya 2026 KPSSP32 puan türünden en az 70 puan almış olmaları gerekiyor. …",
  "details": [ "İçişleri Bakanlığından:", "KAYMAKAM ADAYLIĞI SINAV İLANI",
    "T.C. İçişleri Bakanlığı Mülki İdare Amirliği Hizmetleri Sınıfı'na 60 (altmış) Kaymakam Adayı alınacaktır.", "…" ] }
```

## Caveats

- The whole site serves **iso-8859-9** (Turkish); responses are decoded from raw bytes using the declared charset — never `resp.text`.
- Search is a **scan of the sitemaps** (141 news / 16 jobs + 35 ilan-home listings), not a full-archive search: the site's own search (`/arama/`) is a POST form disallowed in robots.txt, so there is no search API to call.
- Article bodies exclude the ad-widget placeholder and the related-news block; job details come from the page's JobPosting JSON-LD (`qualifications` field).
- Personal results and member-only pages (sonuc/ais.osym.gov.tr is a different site; uye.memurlar.net login) are **not** covered — this server is read-only public content only.
- Transport uses Chrome TLS impersonation with a plain-requests fallback; requests are spaced ~0.5s apart.

## Development

```bash
python -m venv .venv && .venv/bin/pip install -e . pytest
.venv/bin/python -m pytest tests/test_parse.py -v   # offline, recorded fixtures
.venv/bin/python -m pytest tests/test_live.py -v    # live, against www.memurlar.net
.venv/bin/python tests/smoke_live.py                # daily CI probe
```

## License

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/) — free for personal and non-commercial use; commercial use needs a separate license.

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
