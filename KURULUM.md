# Kurulum rehberi (yaklaşık 25–35 dakika)

Kod yazmana gerek yok. Sırayla 7 adım var. Takılırsan bir sonraki adıma geçme, bana yaz.

---

## 1) Telegram botunu oluştur (2 dk)

1. Telegram'da **@BotFather**'ı aç (mavi tikli olan).
2. `/newbot` yaz.
3. Bota bir ad ver, örneğin `YZ Radar Onay`.
4. Bir kullanıcı adı ver; sonu `bot` ile bitmeli. Örneğin `yzradar_onay_bot`.
5. BotFather sana uzun bir **token** verir (`123456789:AA...` gibi). Bir yere kopyala. → Bu **TELEGRAM_BOT_TOKEN**.
6. Oluşan botu aç ve **Başlat**'a (/start) bas.

## 2) Claude API anahtarını al (5 dk)

1. <https://platform.claude.com> adresinden hesap aç.
2. **Settings → Billing** bölümünden kredi yükle (başlangıç için 10–20 $ yeterli).
3. **Settings → API keys** → **Create key**. Süre (expiration) olarak en uzun seçeneği seç.
4. `sk-ant-` ile başlayan anahtarı kopyala (bir kez gösterilir). → Bu **ANTHROPIC_API_KEY**.

> Tahmini maliyet: Günde ~15–20 haber için ayda yaklaşık 30–50 $. Bot her akşam o günün tahmini maliyetini Telegram'dan bildirir. `config.yaml` içindeki `max_drafts_per_day` ile üst sınır koyabilirsin.

## 3) Google görsel anahtarını al (5 dk)

Her habere özel görseli Google'ın görsel modeli üretir.

1. <https://aistudio.google.com/apikey> adresine Google hesabınla gir.
2. **Create API key** ile anahtar oluştur ve kopyala. → Bu **GEMINI_API_KEY**.
3. Görsel modelleri ücretsiz katmanda yok. Aynı sayfadan **Set up billing** ile ödeme yöntemini bağla.

> Tahmini maliyet: Görsel başına yaklaşık 0,035 $. Günde 20 haberle ayda yaklaşık 20 $. Bu anahtarı eklemezsen sistem yine çalışır; o zaman her habere özgü, ücretsiz 3D görseller üretilir.

## 4) GitHub deposunu oluştur ve dosyaları yükle (5 dk)

1. <https://github.com/signup> ile ücretsiz hesap aç (varsa giriş yap).
2. <https://github.com/new> adresine git.
   - **Repository name:** `yz-radar`
   - **Public** seçili olsun (ücretsiz site ve sınırsız otomasyon süresi için gerekli)
   - **Create repository**'ye bas.
3. Açılan sayfada **"uploading an existing file"** bağlantısına tıkla.
4. Sana verdiğim zip'i bilgisayarında aç. `yz-radar` klasörünün **içindekilerin hepsini** seçip sayfaya sürükle.
   - **Mac kullanıyorsan:** `.github` klasörü gizlidir. Finder'da **Cmd + Shift + .** (nokta) tuşlarına bas, gizli dosyalar görünür. Sonra hepsini seç (Cmd + A) ve sürükle.
   - Yükleme listesinde `.github/workflows/bot.yml` dosyasını gördüğünden emin ol. Bu dosya sistemin motorudur.
5. Aşağıdaki **Commit changes** düğmesine bas.

> Yüklemeden hemen sonra "Actions" sekmesinde kırmızı bir çarpı görebilirsin. Anahtarlar henüz girilmediği için bu normal.

## 5) Siteyi aç (1 dk)

1. Depoda **Settings → Pages** menüsüne git.
2. **Build and deployment → Source** kısmında **GitHub Actions**'ı seç.

## 6) Gizli anahtarları gir (3 dk)

**Settings → Secrets and variables → Actions → New repository secret**. Dört anahtarı tek tek ekle:

| Name (birebir böyle yaz) | Secret (değer) |
|---|---|
| `ANTHROPIC_API_KEY` | 2. adımdaki `sk-ant-...` anahtarı |
| `TELEGRAM_BOT_TOKEN` | 1. adımdaki BotFather token'ı |
| `TELEGRAM_CHAT_ID` | Senin Telegram numaran (aşağıya bak) |
| `GEMINI_API_KEY` | 3. adımdaki Google anahtarı |

**TELEGRAM_CHAT_ID'yi öğrenmenin en kolay yolu:** Telegram'da **@userinfobot**'a `/start` yaz. Sana verdiği **Id** numarasını kopyala.
(Diğer yol: İlk ikisini girip 7. adımı çalıştır, sonra kendi botuna `/start` yaz. Bot sana numaranı söyler.)

## 7) İlk çalıştırma (2 dk + bekleme)

1. Depoda **Actions** sekmesine git.
2. Soldan **Haber botu**'nu seç → sağdaki **Run workflow** → **"Kaynakları hemen tara"** kutusunu işaretle → **Run workflow**.
3. 5–8 dakika içinde Telegram'a onay bekleyen haberler, Instagram formatındaki görselleriyle birlikte gelmeye başlar.
4. Siten şu adreste açılır: `https://KULLANICI-ADIN.github.io/yz-radar/`
   (Adresi ayrıca **Settings → Pages** sayfasında görürsün.)

Bundan sonra her şey kendiliğinden çalışır. Sistem her 10 dakikada bir uyanır ve saatte bir kaynakları tarar.

---

## Günlük kullanım

- Telegram'a gelen her haberde: **✅ Yayınla**, **❌ Reddet**, **📄 Tam metin**, **🔁 Yeniden yaz**, **🎨 Yeni görsel** düğmeleri var.
- **Görseli sen yönet:** Haber mesajını yanıtlayıp `görsel: cam bir satranç tahtası üzerinde parlayan piyonlar` gibi yazarsan görsel bu sahneye göre yeniden üretilir.
- **Instagram:** Yayınlanan her haberin post (1080×1350) ve story (1080×1920) görseli Telegram'a gelir. Otomatik paylaşım 2. aşamada eklenecek; o zamana kadar bunları indirip elle paylaşabilirsin. Instagram, yapay zeka ile üretilmiş görseller için "AI info" etiketi isteyebilir.
- **Düzeltme:** Haber mesajını yanıtla ve talimat yaz (ör. "başlığı kısalt").
- Butona bastıktan sonra işlem genellikle birkaç dakikada, en geç ~15 dakikada gerçekleşir; mesaj güncellenir.
- **Öğrenen mod:** Önce 30 karar vermen gerekir. Ardından en az 10 kararda %90 onay verdiğin kaynaklardan gelen net haberler otomatik yayınlanır. Bunlar sana sessiz bildirim olarak gelir ve **🗑 Kaldır** düğmesiyle geri alınabilir.
- Komutlar: `/durum`, `/bekleyen`, `/mod`, `/topla`, `/duraklat`, `/devam`, `/kaynaklar`.

## Ayar değiştirmek

GitHub'da `config.yaml` dosyasını aç → kalem simgesi → değiştir → **Commit changes**. Burada şunları değiştirebilirsin:
- Site adı ve sloganı (`site:`)
- Kaynak ekleme/çıkarma (`sources:`)
- Önem eşiği (`min_importance`) ve günlük sınır
- Otonomi eşikleri

## Bilmende fayda var

- **Depo herkese açık.** Bekleyen taslaklar da depoda görünür, ama anahtarların GitHub'ın gizli kasasında durur ve görünmez.
- **Kendi alan adın:** İleride `yzradar.com` gibi bir alan adı bağlamak istersen `config.yaml` içindeki `site.url` alanını değiştirip Settings → Pages'den alan adını eklemen yeterli.
- **GitHub kuralları:** GitHub Actions, depodaki projeyi derleyip yayınlamak içindir. Bu sistem bir web sitesini düzenli güncelleyip yayınladığı için bu kullanıma uyuyor. Ama sistem büyürse ya da GitHub itiraz ederse, aynı kod değişmeden küçük bir sunucuda da çalışır (`python -m haberbot run` komutunu 10 dakikada bir çalıştırmak yeterli).
