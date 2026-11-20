# memurlar-mcp 🇹🇷

mcp-name: io.github.mohammad-abbasi-sh/memurlar-mcp

**Memurlar.Net** (www.memurlar.net) için resmi olmayan, **salt okunur** MCP sunucusu — Türkiye'nin en büyük memur portalı (1999/2000'de kuruldu, ayda ~21,9 milyon ziyaret, Türkiye'de eğitim kategorisinde 2. sırada): **memur haberleri** (son dakika başlıkları, anahtar kelime araması, haberin tam metni) ve ilan.memurlar.net üzerindeki **kamu personeli alım ilanları** (son ilanlar, anahtar kelime araması, 21 kategori, başvuru tarihiyle birlikte ilanın tam metni).

> "Turkey MCP factory" projesinin bir parçasıdır. Memurlar.Net ile bağlantısı yoktur. Veriler Memurlar.Net'in kendi herkese açık site haritalarından ve sunucu taraflı sayfalarından gelir — giriş yok, API anahtarı yok, salt okunur. İlanlardaki son başvuru tarihleri ilan sayfalarından alınır; güncel durum için her zaman resmî ilanı kontrol edin.

## Yapay zekâ ajanları için

- **Haberler**: `memurlar_latest_news`, sitenin Google Haberler site haritasından en yeni başlıkları döndürür (141 güncel haber; kimlik, başlık, URL, yayın tarihi, anahtar kelimeler ve görsel). `memurlar_search_news` aynı site haritasında anahtar kelimeyle arar — `"öğretmen"`, `"maaş zammı"` — Türkçe duyarlıdır (noktalı/noktasız I ayırt edilir, yani `"ÖĞRETMEN"` ile `"öğretmen"` eşleşir); her kelime başlıkta veya anahtar kelimelerde geçmelidir.
- **Haber detayı**: `memurlar_get_article` sayısal kimlik (`"1184613"`) veya tam URL alır; başlık, kırıntı kategorileri, özet, yayın/güncelleme zamanları, yorum sayısı, manşet görseli ve haberin tam metnini (sırasıyla paragraflar + alıntılar) döndürür.
- **İlanlar**: `memurlar_latest_jobs`, iş site haritasındaki en yeni 16 ilanı döndürür (başlık, tarih, anahtar kelimeler — anahtar kelimeler genellikle son başvuru tarihini içerir, örn. "Son başvuru tarihi 4 Aralık 2026"); `category` parametresi (örn. `"kpss-a-ilanlari"`) verilirse o kategorinin açık ilanları listelenir. `memurlar_search_jobs`, iş site haritası + ilan ana sayfasındaki (35 güncel ilan) listeyi tarar, kimliğe göre tekilleştirir.
- **İlan detayı**: `memurlar_get_job` sayısal kimlik (`"87027"`) veya tam URL alır; sayfadaki schema.org JobPosting verisini döndürür — başlık, özet, ilan tarihi, son başvuru tarihi (`validThrough`), kategori, istihdam türü, çalışma saatleri ve ilanın tam metni (şartlar, koşullar, başvuru adımları).
- **Kategoriler**: `memurlar_list_job_categories`, 21 ilan kategorisini (kısa ad → Türkçe etiket) döndürür; örn. `"kpss-a-ilanlari"` (KPSS-A), `"daimi-isci-ilanlari"` (Daimi İşçi), `"akademik-ilanlar-devlet"` (Devlet Akademik).
- Her yanıt `fetched_at` (UTC) ve `source: www.memurlar.net` taşır.

## Kurulum

```bash
uvx memurlar-mcp
```

Veya MCP istemci yapılandırmanıza ekleyin (örn. Claude Desktop):

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

## Araçlar

| Araç | Ne yapar |
| --- | --- |
| `memurlar_latest_news` | En yeni memur haberleri (en yeniden, haber site haritasından) |
| `memurlar_search_news` | Son 141 haberde anahtar kelime araması |
| `memurlar_get_article` | Bir haberin tam metni (kimlik veya URL) |
| `memurlar_latest_jobs` | En yeni iş ilanları, isteğe bağlı kategori filtresiyle |
| `memurlar_search_jobs` | Güncel iş ilanlarında anahtar kelime araması |
| `memurlar_get_job` | Bir ilanın tam metni ve son başvuru tarihi (kimlik veya URL) |
| `memurlar_list_job_categories` | 21 ilan kategorisi (kısa ad → Türkçe etiket) |
| `memurlar_health` | Memurlar.Net şu an erişilebilir mi? |

## Örnek

20 Kasım 2026 tarihli en yeni haberler:

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

`"87027"` numaralı ilan detayı (İçişleri Bakanlığı, 60 kaymakam adayı):

```json
{ "id": 87027, "title": "İçişleri Bakanlığı 60 Kaymakam Adayı Alacak",
  "posted_at": "2026-11-19T00:05:00Z", "deadline": "2026-12-19T00:05:00Z",
  "category": "KPSS-A İlanları", "employment_type": "FULL_TIME",
  "summary": "İçişleri Bakanlığı, Mülki İdare Amirliği Hizmetleri Sınıfında görevlendirilmek üzere 60 kaymakam adayı alımı yapacağını duyurdu. Adayların 2025 veya 2026 KPSSP32 puan türünden en az 70 puan almış olmaları gerekiyor. …",
  "details": [ "İçişleri Bakanlığından:", "KAYMAKAM ADAYLIĞI SINAV İLANI",
    "T.C. İçişleri Bakanlığı Mülki İdare Amirliği Hizmetleri Sınıfı'na 60 (altmış) Kaymakam Adayı alınacaktır.", "…" ] }
```

## Dikkat edilecekler

- Sitenin tamamı **iso-8859-9** (Türkçe) kodlamayla sunulur; yanıtlar bildirilen karakter kümesine göre ham baytlardan çözülür — asla `resp.text` kullanılmaz.
- Arama, **site haritalarının taranmasıdır** (141 haber / 16 iş + 35 ilan ana sayfa kaydı), tam arşiv araması değildir: sitenin kendi araması (`/arama/`), robots.txt'de yasaklanmış bir POST formudur; çağrılacak bir arama API'si yoktur.
- Haber gövdeleri reklam yer tutucusunu ve ilgili haberler bölümünü içermez; ilan detayları sayfadaki JobPosting JSON-LD'sinden (`qualifications` alanı) gelir.
- Kişisel sonuçlar ve üyelere özel sayfalar (uye.memurlar.net girişi) **kapsanmaz** — bu sunucu yalnızca herkese açık içeriği salt okunur olarak sunar.
- Aktarım, Chrome TLS taklidi ve düz requests yedeği kullanır; istekler ~0,5 sn arayla gönderilir.

## Geliştirme

```bash
python -m venv .venv && .venv/bin/pip install -e . pytest
.venv/bin/python -m pytest tests/test_parse.py -v   # çevrimdışı, kayıtlı örnekler
.venv/bin/python -m pytest tests/test_live.py -v    # canlı, www.memurlar.net karşısında
.venv/bin/python tests/smoke_live.py                # günlük CI denetimi
```

## Lisans

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/) — kişisel ve ticari olmayan kullanım için ücretsizdir; ticari kullanım ayrı bir lisans gerektirir.

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
