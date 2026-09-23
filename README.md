# YZ Radar — otonom yapay zeka haber sistemi

Dünyadaki yapay zeka gelişmelerini toplar, Türkçe ve kaynak gösteren haberler yazar,
Telegram'dan onayını alır ve web sitesinde yayınlar. Kararlarından öğrenir: güvendiği
kaynaklardan gelen net haberleri zamanla kendisi yayınlamaya başlar.

**Kurulum için:** `KURULUM.md` dosyasına bak (yaklaşık 25–35 dakika, kod bilgisi gerekmez).

## Nasıl çalışır?

```
Her 10 dk (GitHub Actions)
 ├─ Telegram: butonlarını ve komutlarını işle
 ├─ Saatte bir: 14 kaynağı tara (RSS + Anthropic haber sayfası)
 │    ├─ Claude Haiku: aynı haberleri birleştir, 1–10 önem puanı ver, önemsizleri ele
 │    ├─ Tam metni kaynaktan oku (robots.txt'ye uyarak)
 │    ├─ Claude Sonnet: özgün Türkçe haber + "Neden önemli?" + risk işaretleri
 │    ├─ Claude habere özel bir görsel sahne kurgular → Google görsel modeli üretir
 │    │   (anahtar yoksa habere özgü 3D stüdyo görseli; kaynak fotoğrafı asla kullanılmaz)
 │    ├─ Kartlar: Instagram post 1080×1350, story 1080×1920, paylaşım kapağı 1200×630
 │    │   (3 düzen: ürün, buzlu cam, dev rakam — habere göre otomatik seçilir)
 │    └─ Karar: sana sor  |  otomatik yayınla (öğrenen mod)
 ├─ Onaylananları siteye ekle, GitHub Pages'e yayınla
 └─ Akşam: günlük özet
```

## Klasörler

| Yol | Ne var? |
|---|---|
| `config.yaml` | **Tüm ayarlar** — site adı, kaynaklar, otonomi eşikleri, modeller |
| `haberbot/` | Python kodu |
| `templates/`, `static/` | Site tasarımı (apple.com esintili, açık tema) |
| `templates/cards/` | Instagram post/story ve paylaşım kapağı şablonları |
| `content/posts/` | Yayınlanan haberler (JSON) |
| `content/images/` | Haber görselleri (`.webp`) ve paylaşım kapakları (`-og.jpg`) |
| `data/` | Bot durumu, taslaklar, kaynak güven istatistikleri, arşiv |

## Telegram komutları

`/durum` · `/bekleyen` · `/mod manuel|ogrenen|tam` · `/topla` · `/duraklat` · `/devam` · `/kaynaklar` · `/yardim`

Bir haberi düzeltmek için o haberin Telegram mesajını **yanıtla** ve talimatını yaz
(ör. "başlığı kısalt", "son paragrafı çıkar").

## Yerel test (isteğe bağlı)

```bash
pip install -r requirements.txt
python tests/test_core.py
python tests/make_fixtures.py
HABERBOT_ROOT=/tmp/yz HABERBOT_MOCK=1 HABERBOT_FIXTURES=tests/fixtures python -m haberbot run
```

## Sonraki aşama

Instagram'a otomatik paylaşım (post, story, reels). Görsel kartlar ve `/api/latest.json` bu aşama için hazır.

Kartlardaki yazı tipi Instrument Sans'tır (SIL Open Font License, `assets/fonts/OFL-InstrumentSans.txt`).
