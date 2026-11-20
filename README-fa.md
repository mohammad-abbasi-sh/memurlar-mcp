# memurlar-mcp 🇹🇷

mcp-name: io.github.mohammad-abbasi-sh/memurlar-mcp

سرور MCP غیررسمی و **فقط‌خواندنی** برای **Memurlar.Net** (www.memurlar.net) — بزرگ‌ترین پورتال کارمندان دولت ترکیه (تأسیس ۱۹۹۹/۲۰۰۰، حدود ۲۱٫۹ میلیون بازدید در ماه، رتبهٔ ۲ آموزش در ترکیه): **اخبار کارمندان دولت** (تیترهای تازه، جست‌وجو با کلیدواژه، متن کامل خبر) و **آگهی‌های استخدام بخش دولتی** در ilan.memurlar.net (تازه‌ترین آگهی‌ها، جست‌وجو با کلیدواژه، ۲۱ دسته‌بندی، متن کامل آگهی همراه با مهلت ثبت‌نام).

> بخشی از «کارخانهٔ MCP ترکیه». وابسته به Memurlar.Net نیست. داده‌ها از نقشه‌های سایت عمومی و صفحات سرور-رندرشدهٔ خود Memurlar.Net می‌آیند — بدون ورود، بدون کلید API، فقط‌خواندنی. مهلت‌های ثبت‌نام از صفحات آگهی گرفته می‌شوند؛ پیش از اقدام، همیشه آگهی رسمی را بررسی کنید.

## برای ایجنت‌های هوش مصنوعی

- **اخبار**: `memurlar_latest_news` تازه‌ترین تیترها را از نقشهٔ سایت Google News برمی‌گرداند (۱۴۱ خبر اخیر با شناسه، عنوان، URL، تاریخ انتشار، کلیدواژه‌ها و تصویر). `memurlar_search_news` همان نقشه را با کلیدواژه می‌گردد — `"öğretmen"`، `"maaş zammı"` — با حساسیت به ترکی (I نقطه‌دار/بی‌نقطه رعایت می‌شود، پس `"ÖĞRETMEN"` با `"öğretmen"` مطابقت دارد)؛ هر واژه باید در عنوان یا کلیدواژه‌ها باشد.
- **متن خبر**: `memurlar_get_article` شناسهٔ عددی (`"1184613"`) یا URL کامل می‌گیرد و عنوان، دسته‌بندی‌های مسیر، خلاصه، زمان انتشار/به‌روزرسانی، تعداد نظرات، تصویر تیتر و متن کامل خبر (پاراگراف‌ها + نقل‌قول‌ها به ترتیب) را برمی‌گرداند.
- **آگهی‌ها**: `memurlar_latest_jobs` شانزده آگهی اخیر را از نقشهٔ سایت مشاغل برمی‌گرداند (عنوان، تاریخ، کلیدواژه‌ها — که اغلب مهلت را دارند، مثلاً «Son başvuru tarihi 4 Aralık 2026»)؛ با پارامتر `category` (مثلاً `"kpss-a-ilanlari"`) آگهی‌های باز همان دسته فهرست می‌شوند. `memurlar_search_jobs` نقشهٔ سایت مشاغل + صفحهٔ اصلی ilan (۳۵ آگهی اخیر) را می‌گردد و بر اساس شناسه یکتاسازی می‌کند.
- **جزئیات آگهی**: `memurlar_get_job` شناسهٔ عددی (`"87027"`) یا URL کامل می‌گیرد و دادهٔ JobPosting از schema.org صفحه را برمی‌گرداند — عنوان، خلاصه، تاریخ انتشار، مهلت ثبت‌نام (`validThrough`)، دسته، نوع استخدام، ساعات کاری و متن کامل آگهی (شرایط، ضوابط، مراحل ثبت‌نام).
- **دسته‌ها**: `memurlar_list_job_categories` بیست‌ویک دستهٔ ilan را (اسلاگ ← برچسب ترکی) برمی‌گرداند، مثلاً `"kpss-a-ilanlari"` (KPSS-A)، `"daimi-isci-ilanlari"` (کارگران دائمی)، `"akademik-ilanlar-devlet"` (پست‌های دانشگاهی دولتی).
- هر پاسخ شامل `fetched_at` (UTC) و `source: www.memurlar.net` است.

## نصب

```bash
uvx memurlar-mcp
```

یا به پیکربندی کلاینت MCP خود اضافه کنید (مثلاً Claude Desktop):

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

## ابزارها

| ابزار | کارکرد |
| --- | --- |
| `memurlar_latest_news` | تازه‌ترین اخبار کارمندان دولت (از تازه‌ترین، از نقشهٔ خبر) |
| `memurlar_search_news` | جست‌وجوی کلیدواژه در ۱۴۱ خبر اخیر |
| `memurlar_get_article` | متن کامل یک خبر (شناسه یا URL) |
| `memurlar_latest_jobs` | تازه‌ترین آگهی‌های استخدام، با فیلتر اختیاری دسته |
| `memurlar_search_jobs` | جست‌وجوی کلیدواژه در آگهی‌های اخیر |
| `memurlar_get_job` | متن کامل یک آگهی با مهلت ثبت‌نام (شناسه یا URL) |
| `memurlar_list_job_categories` | ۲۱ دستهٔ ilan (اسلاگ ← برچسب ترکی) |
| `memurlar_health` | آیا Memurlar.Net در حال حاضر در دسترس است؟ |

## نمونه

تازه‌ترین اخبار، ۲۰ نوامبر ۲۰۲۶:

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

جزئیات آگهی `"87027"` (وزارت کشور، ۶۰ داوطلب فرمانداری):

```json
{ "id": 87027, "title": "İçişleri Bakanlığı 60 Kaymakam Adayı Alacak",
  "posted_at": "2026-11-19T00:05:00Z", "deadline": "2026-12-19T00:05:00Z",
  "category": "KPSS-A İlanları", "employment_type": "FULL_TIME",
  "summary": "İçişleri Bakanlığı, Mülki İdare Amirliği Hizmetleri Sınıfında görevlendirilmek üzere 60 kaymakam adayı alımı yapacağını duyurdu. Adayların 2025 veya 2026 KPSSP32 puan türünden en az 70 puan almış olmaları gerekiyor. …",
  "details": [ "İçişleri Bakanlığından:", "KAYMAKAM ADAYLIĞI SINAV İLANI",
    "T.C. İçişleri Bakanlığı Mülki İdare Amirliği Hizmetleri Sınıfı'na 60 (altmış) Kaymakam Adayı alınacaktır.", "…" ] }
```

## نکات مهم

- کل سایت با کدگذاری **iso-8859-9** (ترکی) سرو می‌شود؛ پاسخ‌ها با استفاده از کاراکترست اعلام‌شده از بایت‌های خام دیکد می‌شوند — هرگز `resp.text` استفاده نمی‌شود.
- جست‌وجو **اسکن نقشه‌های سایت** است (۱۴۱ خبر / ۱۶ شغل + ۳۵ آگهی صفحهٔ اصلی ilan)، نه جست‌وجوی کامل آرشیو: جست‌وجوی خود سایت (`/arama/`) یک فرم POST است که در robots.txt ممنوع شده؛ هیچ API جست‌وجویی برای فراخوانی وجود ندارد.
- بدنهٔ خبرها، جای تبلیغات و بخش اخبار مرتبط را شامل نمی‌شود؛ جزئیات آگهی‌ها از JSON-LD از نوع JobPosting صفحه می‌آید (فیلد `qualifications`).
- نتایج شخصی و صفحات مخصوص اعضا (ورود به uye.memurlar.net) **پوشش داده نمی‌شوند** — این سرور فقط محتوای عمومی را به‌صورت فقط‌خواندنی ارائه می‌کند.
- انتقال داده با جعل TLS کروم و پشتیبان requests ساده انجام می‌شود؛ درخواست‌ها با فاصلهٔ حدود ۰٫۵ ثانیه فرستاده می‌شوند.

## توسعه

```bash
python -m venv .venv && .venv/bin/pip install -e . pytest
.venv/bin/python -m pytest tests/test_parse.py -v   # آفلاین، با نمونه‌های ضبط‌شده
.venv/bin/python -m pytest tests/test_live.py -v    # زنده، در برابر www.memurlar.net
.venv/bin/python tests/smoke_live.py                # بررسی روزانهٔ CI
```

## مجوز

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/) — برای استفادهٔ شخصی و غیرتجاری رایگان است؛ استفادهٔ تجاری نیازمند مجوز جداگانه است.

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
