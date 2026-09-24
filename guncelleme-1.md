YZRADAR-BUNDLE v1 part 1/2
@@@YZ@@@ PATCH config.yaml
--- a/config.yaml
+++ b/config.yaml
@@ -55,6 +55,9 @@
   auto_min_importance: 6         # Otomatik yayın için en düşük önem puanı
 
 images:
+  # kapak: habere özel tipografik kapak (dev rakam / isim / manşet), ücretsiz (önerilen)
+  # 3d   : eski renkli 3D şekiller
+  style: kapak
   # Her habere yapay zeka ile özel görsel (Google "Nano Banana").
   # GEMINI_API_KEY gizli anahtarı yoksa ya da üretim başarısız olursa
   # habere özgü 3D stüdyo görseli (ücretsiz yedek) kullanılır.
@@@YZ@@@ PATCH haberbot/app.py
--- a/haberbot/app.py
+++ b/haberbot/app.py
@@ -11,6 +11,7 @@
 
 from . import policy
 from .config import CATEGORIES, Config, category_label, indexnow_key
+from .covers import COVER_VERSION
 from .extract import full_text
 from .llm import LLMError, MockLLM, estimate_cost, make_llm
 from .prompts import (FLAG_LABELS, FLAGS, SEO_SCHEMA, TRIAGE_SCHEMA, WRITE_SCHEMA, seo_system, seo_user,
@@ -278,6 +279,7 @@
             "meta_description": clip((out.get("meta_description") or "").strip(), 170),
             "seo_slug": slugify(out["slug"], 64) if (out.get("slug") or "").strip() else "",
             "image_alt": clip((out.get("image_alt") or "").strip(), 125),
+            "cover_text": clip((out.get("cover_text") or "").strip(), 24),
         }
 
     def create_draft(self, story: dict, its: list[dict]) -> dict:
@@ -359,7 +361,10 @@
         post.update({"slug": slug, "published_at": iso(now_utc()), "publish_mode": "auto" if auto else "manual"})
         self.queue_indexnow(self.cfg.post_url(slug))
         st.move_image_to_post(d["id"])
-        if not st.post_image(d["id"]).exists():
+        img = post.get("image") or {}
+        if img.get("source") in ("cover", "fallback") and img.get("cover_v") != COVER_VERSION:
+            post["image"] = self.vis.make_hero(post, st.post_image(d["id"]))
+        elif not st.post_image(d["id"]).exists():
             post["image"] = self.vis.make_hero(post, st.post_image(d["id"]))
         self.vis.render_card(post, "og", st.post_image(d["id"]), st.post_og(d["id"]))
         st.save_post(post)
@@ -651,8 +656,14 @@
         st = self.store
         new_visual = visual_only is not None
         if new_visual:
-            if visual_only.strip():
-                d["visual_scene"] = visual_only.strip()
+            text = visual_only.strip()
+            if text and len(text) <= 24:   # kısa ifade: kapaktaki büyük yazı olsun
+                d["cover_text"] = text
+                d["cover_variant"] = int(d.get("cover_variant", 0)) + 1
+            elif text:                      # uzun ifade: yapay zeka görseli sahnesi
+                d["visual_scene"] = text
+            else:                           # "Yeni görsel" düğmesi: yeni renk ve düzen
+                d["cover_variant"] = int(d.get("cover_variant", 0)) + 1
             d["rewrites"] = (d.get("rewrites") or 0) + 1
             old_kind = "pending" if where == "draft" else ("auto" if d.get("publish_mode") == "auto" else "published")
             d["image"] = self.vis.make_hero(d, self._hero(d))
@@ -830,6 +841,23 @@
             self.queue_indexnow(self.cfg.post_url(p["slug"]))
             log.info("SEO bilgisi eklendi: %s → %s", p["id"], p["seo_title"])
 
+    def refresh_covers(self, limit: int = 30) -> None:
+        """Kapak tasarımı değişince yayındaki haberlerin görsellerini yeniden üret (yapay zeka görsellerine dokunmaz)."""
+        if (self.cfg.get("images", "style", "kapak") or "kapak") != "kapak":
+            return
+        todo = [p for p in self.store.posts()
+                if (p.get("image") or {}).get("source") != "ai" and (p.get("image") or {}).get("cover_v") != COVER_VERSION][:limit]
+        for p in todo:
+            try:
+                p["image"] = {**self.vis.make_hero(p, self.store.post_image(p["id"])), "cover_v": COVER_VERSION}
+                self.vis.render_card(p, "og", self.store.post_image(p["id"]), self.store.post_og(p["id"]))
+                self.store.save_post(p)
+            except Exception as e:  # noqa: BLE001
+                log.warning("Kapak yenilenemedi (%s): %s", p["id"], e)
+                return
+        if todo:
+            log.info("Kapak yenilendi: %d haber", len(todo))
+
     def maybe_summary(self) -> None:
         now_l = local(now_utc(), self.cfg.tz)
         hour = self.cfg.get("schedule", "daily_summary_hour", 21)
@@ -885,6 +913,7 @@
                 self.notify_error(f"Toplama sırasında hata: {type(e).__name__}: {e}")
         if not self.state.get("paused"):
             self.backfill_seo()
+        self.refresh_covers()
         self.maybe_summary()
         self.listen(int(self.cfg.get("schedule", "listen_seconds", 120) or 0))
         self.store.save()
@@@YZ@@@ PATCH haberbot/prompts.py
--- a/haberbot/prompts.py
+++ b/haberbot/prompts.py
@@ -109,10 +109,11 @@
         "meta_description": {"type": "string"},
         "slug": {"type": "string"},
         "image_alt": {"type": "string"},
+        "cover_text": {"type": "string"},
     },
     "required": ["title", "summary", "body", "category", "tags", "confidence", "flags", "editor_note",
                  "short_title", "kicker", "hero_stat", "hero_stat_label", "visual_style", "visual_scene",
-                 "focus_keyword", "seo_title", "meta_description", "slug", "image_alt"],
+                 "focus_keyword", "seo_title", "meta_description", "slug", "image_alt", "cover_text"],
     "additionalProperties": False,
 }
 
@@ -161,7 +162,8 @@
 - hero_stat: if ONE number is the heart of the story and appears in the sources (money, parameter count, percentage, user count), write it compactly in Turkish format, ≤12 characters: "3,5 milyar $", "30 milyar", "%40", "1 milyon". Otherwise "". Never invent or round beyond the source.
 - hero_stat_label: ≤30 Turkish characters explaining the number ("yeni değerleme", "parametre", "daha hızlı"); "" if no hero_stat.
 - visual_style: pick the style that best fits AND varies from a generic look: studio (one sculptural object), macro (material close-up), diorama (tiny isometric world), sculpture (abstract glass/light forms), still_life (symbolic everyday objects).
-- visual_scene: ≤60 words in ENGLISH describing ONE concrete, original visual metaphor for the story for an image generator. Physical objects and materials only. Never depict real people, faces, logos, brand names, product UIs, text, letters or numbers. Avoid clichés (glowing brains, humanoid robots, binary code, circuit-board heads). Good example for a funding round in AI training data: "a tall stack of translucent frosted-glass cubes rising like a bar chart, the top cube glowing warm amber, tiny ceramic spheres rolling off the edge onto a soft surface"."""
+- cover_text: the single most striking name for a big typographic cover, ≤18 characters, exactly as written in the sources: usually the product/model name ("GPT-6 Astra", "Opus 5.5", "Gemini 4"), otherwise the company or organisation ("Snorkel AI", "YouTube"), otherwise a 1–3 word key term in Turkish ("Süper zeka yasağı"). Never a full sentence, never generic words like "Yapay zeka".
+- visual_scene: ≤60 words in ENGLISH describing ONE concrete, original visual metaphor for THIS story for an image generator. Invent a new metaphor every time; never reuse the example below. Physical objects and materials only. Never depict real people, faces, logos, brand names, product UIs, text, letters or numbers. Avoid clichés (glowing brains, humanoid robots, binary code, circuit-board heads). Good example for a funding round in AI training data: "a tall stack of translucent frosted-glass cubes rising like a bar chart, the top cube glowing warm amber, tiny ceramic spheres rolling off the edge onto a soft surface"."""
 
 
 def write_user(sources: list[dict], today: str, previous: dict | None = None,
@@@YZ@@@ PATCH haberbot/site.py
--- a/haberbot/site.py
+++ b/haberbot/site.py
@@ -138,6 +138,7 @@
             "hero_stat": (p.get("hero_stat") or "").strip(),
             "hero_stat_label": (p.get("hero_stat_label") or "").strip(),
             "ai_image": (p.get("image") or {}).get("source") == "ai",
+            "cover_image": (p.get("image") or {}).get("source") == "cover",
             "img_alt": clip(p.get("image_alt") or f"{short}: habere ait temsili görsel", 125),
             "seo_title": seo_title,
             "meta_description": clip(meta, 158),
@@@YZ@@@ PATCH haberbot/visuals.py
--- a/haberbot/visuals.py
+++ b/haberbot/visuals.py
@@ -15,6 +15,7 @@
 import requests
 from PIL import Image
 
+from . import covers
 from .config import Config, category_color, category_label
 from .render import Renderer
 from .util import clip, log, tr_date
@@ -204,6 +205,13 @@
         self.renderer.close()
 
     # ── kahraman görsel ─────────────────────────────────────
+    def cover_image(self, d: dict, size=HERO_SIZE, brand: bool = False, caption: bool = False) -> Image.Image:
+        """Tipografik kapak (dev rakam / isim / manşet) — ücretsiz, habere özel. Sitede etiket zaten yazdığı için kapakta yok."""
+        tmp = self.renderer.cache / "_cover.jpg"
+        ctx = covers.design(d, brand=brand, caption=caption, brand_name=self.brand, kicker=False)
+        self.renderer.html_to_image("cover.html", ctx, size, tmp, quality=95)
+        return Image.open(tmp).convert("RGB")
+
     def make_hero(self, d: dict, out: Path) -> dict:
         """Görseli üretir, out'a WEBP yazar. d['image'] bilgisini döndürür."""
         info = {"source": "fallback"}
@@ -217,6 +225,14 @@
             except (ImageError, OSError) as e:
                 log.warning("Yapay zeka görseli üretilemedi, yedek görsel kullanılacak: %s", e)
                 info = {"source": "fallback", "error": str(e)[:300]}
+        if img is None and self.cfg.get("images", "style", "kapak") == "kapak":
+            try:
+                img = self.cover_image(d)
+                c = covers.design(d)
+                info = {**info, "source": "cover", "layout": c["layout"], "palette": c["palette"],
+                        "cover_v": covers.COVER_VERSION}
+            except Exception as e:  # noqa: BLE001
+                log.warning("Kapak üretilemedi, 3D görsel denenecek: %s", e)
         if img is None:
             try:
                 img = fallback_hero(self.renderer, d)
@@ -276,6 +292,12 @@
 
     def render_card(self, d: dict, kind: str, hero: Path, out: Path) -> Path:
         size = self.SIZES[kind]
+        if (d.get("image") or {}).get("source") == "cover":
+            try:
+                ctx = covers.design(d, brand=True, caption=True, brand_name=self.brand)
+                return self.renderer.html_to_image("cover.html", ctx, size, out)
+            except Exception as e:  # noqa: BLE001
+                log.warning("Kapak kartı üretilemedi (%s): %s", kind, e)
         ctx = self.card_context(d, hero, kind)
         try:
             return self.renderer.html_to_image(f"{kind}.html", {**ctx, "kind": kind}, size, out)
@@@YZ@@@ PATCH static/style.css
--- a/static/style.css
+++ b/static/style.css
@@ -117,10 +117,11 @@
 .slide.dark .stat-chip { background: rgba(255,255,255,.16); color: #fff; }
 @media (max-width: 599px) { .slide-dek { display: none; } }
 @media (min-width: 800px) {
-  .slide-in { grid-template-columns: minmax(0, .95fr) minmax(0, 1.05fr); min-height: clamp(420px, 42vw, 540px); }
-  .slide-media { order: 0; aspect-ratio: auto; }
-  .slide-img { -webkit-mask-image: linear-gradient(to right, transparent 0, #000 26%); mask-image: linear-gradient(to right, transparent 0, #000 26%); }
-  .slide-txt { padding: 48px 8px 48px 56px; gap: 14px; }
+  .slide-in { grid-template-columns: minmax(0, 1fr) auto; height: clamp(400px, 40vw, 520px); }
+  .slide-media { order: 0; aspect-ratio: 4 / 3; height: 100%; }
+  .slide-img { -webkit-mask-image: linear-gradient(to right, transparent 0, #000 14%); mask-image: linear-gradient(to right, transparent 0, #000 14%); }
+  .slide-txt { padding: 40px 12px 40px 48px; gap: 12px; }
+  .slide h2 { font-size: clamp(26px, 2.7vw, 40px); }
 }
 
 .car-ui { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding-top: 16px; }
@@ -209,11 +210,11 @@
 .card .t { font-size: 14px; color: var(--muted); }
 @media (max-width: 639px) {
   .grid { gap: 0; }
-  .card { grid-template-columns: minmax(0, 1fr) 108px; grid-template-areas: "eb ph" "h ph" "t ph"; column-gap: 16px; row-gap: 6px;
+  .card { grid-template-columns: minmax(0, 1fr) 124px; grid-template-areas: "eb ph" "h ph" "t ph"; column-gap: 16px; row-gap: 6px;
     padding-block: 18px; border-bottom: 1px solid #E8E8ED; align-content: start; }
   .card:first-child { padding-top: 4px; }
   .card .ph { grid-area: ph; align-self: start; border-radius: 14px; }
-  .card img { aspect-ratio: 1; }
+  .card img { aspect-ratio: 4 / 3; }
   .card .eyebrow { grid-area: eb; }
   .card h2, .card h3 { grid-area: h; font-size: 18px; line-height: 1.25; }
   .card-dek { display: none; }
@@@YZ@@@ PATCH templates/article.html
--- a/templates/article.html
+++ b/templates/article.html
@@ -60,7 +60,7 @@
 
   <figure class="art-media">
     <div class="ph">{{ img(post, eager=true, sizes='(min-width: 1232px) 1200px, 100vw', priority=true) }}</div>
-    <figcaption>{% if post.ai_image %}Temsili görsel, yapay zeka ile üretilmiştir.{% else %}Temsili görsel.{% endif %}</figcaption>
+    {% if not post.cover_image %}<figcaption>{% if post.ai_image %}Temsili görsel, yapay zeka ile üretilmiştir.{% else %}Temsili görsel.{% endif %}</figcaption>{% endif %}
   </figure>
 
   <div class="narrow">
@@@YZ@@@ FILE haberbot/covers.py
"""Tipografik haber kapakları: her habere özel renk, düzen ve tek bir güçlü öğe.

Düzenler
  sayi   : haberin kalbindeki rakam dev boyutta ("311 milyon $", "%40")
  isim   : öne çıkan ürün / model / şirket adı dev boyutta ("GPT‑6 Astra", "Opus 5.5")
  manset : açık zeminde afiş gibi büyük başlık, anahtar sözcük renkli
  isik   : karanlıkta ışık huzmesi ve başlık (regülasyon, güvenlik gibi ciddi konular)

Logo ya da marka işareti kullanılmaz; yalnızca metin, renk ve ışık.
"""
from __future__ import annotations

import hashlib
import html
import random
import re

# c1..c4: vurgu renkleri, sonra koyu zemin ve açık zemin
PALETTES: dict[str, list[str]] = {
    "okyanus":   ["#38BDF8", "#3B82F6", "#6366F1", "#A78BFA", "#050816", "#EAF2FF"],
    "gunbatimi": ["#FDBA74", "#FB7185", "#E879F9", "#A855F7", "#12060F", "#FFF0EA"],
    "nane":      ["#6EE7B7", "#2DD4BF", "#22D3EE", "#A7F3D0", "#03110E", "#E8FAF3"],
    "lav":       ["#FDE047", "#FB923C", "#F43F5E", "#E11D48", "#140605", "#FFF1E8"],
    "lavanta":   ["#C4B5FD", "#A78BFA", "#F0ABFC", "#F9A8D4", "#0C0718", "#F4EEFF"],
    "altin":     ["#FEF08A", "#FACC15", "#F59E0B", "#FB923C", "#120C02", "#FFF7E3"],
    "buz":       ["#BAE6FD", "#7DD3FC", "#93C5FD", "#C7D2FE", "#040A14", "#EEF6FF"],
    "orman":     ["#D9F99D", "#84CC16", "#22C55E", "#10B981", "#040E06", "#EFFAE6"],
    "mercan":    ["#FED7AA", "#FDA4AF", "#FB7185", "#F97316", "#16080A", "#FFF0EC"],
    "elektrik":  ["#22D3EE", "#818CF8", "#C084FC", "#F472B6", "#050314", "#F1EEFF"],
    "grafit":    ["#F4F4F5", "#A1A1AA", "#D4D4D8", "#71717A", "#09090B", "#F2F2F4"],
}

# Tanınan şirket / ürün adları için renk çağrışımı (logo değil, yalnızca renk)
ENTITY_PALETTES: list[tuple[str, str]] = [
    (r"openai|chatgpt|gpt|sora|codex", "nane"),
    (r"anthropic|claude|opus|sonnet|haiku", "mercan"),
    (r"youtube", "lav"),
    (r"google|gemini|deepmind|veo|imagen", "elektrik"),
    (r"nvidia|jetson|isaac|blackwell|rubin|cuda", "orman"),
    (r"\bmeta\b|llama|ray-ban|muse", "okyanus"),
    (r"microsoft|copilot|azure|phi-", "buz"),
    (r"amazon|aws|alexa", "altin"),
    (r"apple|siri", "grafit"),
    (r"xai|grok|tesla", "grafit"),
    (r"mistral", "gunbatimi"),
    (r"deepseek|qwen|alibaba|baidu", "okyanus"),
    (r"hugging ?face", "altin"),
    (r"stripe", "lavanta"),
    (r"türkiye|istanbul|ankara|izmir", "lav"),
]
CATEGORY_PALETTES = {
    "modeller": ["elektrik", "lavanta", "okyanus"], "urunler": ["lavanta", "buz", "nane"],
    "arastirma": ["buz", "okyanus", "nane"], "sirketler": ["altin", "gunbatimi", "nane"],
    "politika": ["okyanus", "grafit", "mercan"], "donanim": ["orman", "grafit", "buz"],
    "acik-kaynak": ["gunbatimi", "lavanta", "altin"], "turkiye": ["lav", "mercan", "altin"],
}

PRODUCT_RE = re.compile(
    r"\b(GPT|ChatGPT|Gemini|Claude|Opus|Sonnet|Haiku|Llama|Grok|Copilot|Sora|Veo|Imagen|Isaac|Jetson|Blackwell|"
    r"Rubin|Mistral|Qwen|DeepSeek|Phi|Muse|Astra|Codex|Siri|Alexa|Nova|Titan|Ray-Ban|Vision Pro)\b", re.I)
GENERIC = {"yapay zeka", "yapay zekâ", "ai", "teknoloji", "veri merkezleri", "yapay zeka ajanları", "büyük dil modelleri"}


COVER_VERSION = 1


def _seed(d: dict) -> int:
    key = f'{d.get("id") or d.get("title", "x")}:{d.get("cover_variant", 0)}'
    return int(hashlib.sha1(key.encode()).hexdigest()[:8], 16)


def cover_word(d: dict) -> str:
    """Kapağa yazılacak ürün / model / şirket adı (yoksa '')."""
    w = (d.get("cover_text") or "").strip()
    if w:
        return w
    cands = [t for t in (d.get("tags") or []) if t and t.lower() not in GENERIC]
    kw = (d.get("focus_keyword") or "").strip()
    if kw:
        cands.append(kw)
    best, score = "", 0
    for c in cands:
        s = 0
        if PRODUCT_RE.search(c):
            s += 3
        if re.search(r"\d", c) and re.search(r"[A-Za-zÇĞİÖŞÜçğıöşü]", c):
            s += 2
        if len(c) <= 16:
            s += 1
        if len(c.split()) > 3 or len(c) > 24:
            s -= 3
        if s > score:
            best, score = c, s
    if score >= 3:
        # "Gemini 3.8 Flash TTS" gibi uzun adları kısalt
        words = best.split()
        while len(" ".join(words)) > 16 and len(words) > 2:
            words.pop()
        return " ".join(words)
    return ""


def palette_for(d: dict) -> tuple[str, list[str]]:
    text = " ".join([d.get("title", ""), d.get("short_title", ""), " ".join(d.get("tags") or []),
                     d.get("focus_keyword", ""), d.get("cover_text", "")]).lower()
    for pat, name in ENTITY_PALETTES:
        if re.search(pat, text):
            return name, PALETTES[name]
    opts = CATEGORY_PALETTES.get(d.get("category", ""), ["elektrik", "okyanus", "lavanta"])
    name = opts[_seed(d) % len(opts)]
    return name, PALETTES[name]


def _highlight(title: str, key: str) -> str:
    """Başlığı güvenli HTML'e çevir; anahtar sözcük renkli vurgulansın."""
    t = html.escape(title)
    k = html.escape(key or "")
    if k and len(k) >= 3:
        m = re.search(re.escape(k), t, re.I)
        if m:
            return t[:m.start()] + f'<em class="grad-text">{t[m.start():m.end()]}</em>' + t[m.end():]
    # anahtar yoksa ilk büyük harfli özel adı vurgula
    m = re.search(r"\b([A-ZÇĞİÖŞÜ][\w'’.-]{2,}(?:\s[A-ZÇĞİÖŞÜ0-9][\w'’.-]*)?)", t)
    if m:
        return t[:m.start()] + f'<em class="grad-text">{m.group(1)}</em>' + t[m.end():]
    return t


def _lum(hexc: str) -> float:
    h = hexc.lstrip("#")[:6]
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _blobs(rnd: random.Random, pal: list[str], layout: str, tone: str, variant: str = "center") -> list[dict]:
    cols = pal[:4]
    if tone == "vivid":  # tüm yüzeyi kaplayan canlı ağ degrade
        return [{"x": x, "y": y, "s": s_, "c": c} for x, y, s_, c in (
            (rnd.randint(0, 30), rnd.randint(0, 35), 85, cols[0]), (rnd.randint(70, 100), rnd.randint(0, 35), 80, cols[2]),
            (rnd.randint(20, 60), rnd.randint(70, 100), 90, cols[1]), (rnd.randint(80, 105), rnd.randint(70, 105), 70, cols[3]))]
    if layout == "sayi" and variant == "left":
        spots = [(rnd.randint(75, 95), rnd.randint(10, 30), 70, cols[1]), (100, 60, 50, cols[2]), (rnd.randint(10, 30), 105, 40, cols[0])]
    elif layout == "sayi" and tone == "dark":  # siyah zemin, rakamın arkasında tek parıltı
        spots = [(50, 62, 62, cols[2]), (rnd.choice((30, 70)), 70, 34, cols[3])]
    elif layout == "sayi":
        spots = [(50, 58, 78, cols[1]), (18, 22, 46, cols[0]), (86, 82, 50, cols[3]), (82, 18, 34, cols[2])]
    elif layout == "isim":
        spots = [(rnd.randint(10, 35), rnd.randint(15, 45), 70, cols[0]), (rnd.randint(60, 90), rnd.randint(10, 40), 64, cols[2]),
                 (rnd.randint(35, 65), rnd.randint(60, 95), 76, cols[1]), (rnd.randint(75, 100), rnd.randint(65, 100), 52, cols[3])]
    elif layout == "manset":
        spots = [(rnd.randint(70, 95), rnd.randint(5, 30), 70, cols[1]), (rnd.randint(85, 110), rnd.randint(40, 70), 55, cols[2]),
                 (rnd.randint(-5, 20), rnd.randint(-10, 15), 36, cols[0])]
    else:  # isik: ışığı şablon çizer
        spots = []
    out = []
    for x, y, s, c in spots:
        if tone == "dark" and layout in ("sayi", "isik"):
            c = c + "B3"  # hafif şeffaf
        out.append({"x": x, "y": y, "s": s, "c": c})
    return out


def design(d: dict, brand: bool = False, caption: bool = False, brand_name: str = "YZ Radar", kicker: bool = True) -> dict:
    """Kapak şablonu için bağlam sözlüğü. caption=True: sosyal medya için kısa başlık da yazılır."""
    seed = _seed(d)
    rnd = random.Random(seed)
    pal_name, pal = palette_for(d)
    stat = (d.get("hero_stat") or "").strip()
    word = cover_word(d)
    cat = d.get("category", "")
    serious = cat == "politika" or re.search(r"güvenlik|ihlal|dava|soruşturma|yasak", (d.get("kicker", "") + d.get("title", "")).lower())

    variant = "center"
    pick = seed % 6
    if stat and len(stat) <= 12 and not (word and pick in (1, 4)):
        layout = "sayi"
        tone, variant = [("dark", "center"), ("light", "left"), ("vivid", "center"),
                         ("dark", "center"), ("light", "left"), ("vivid", "left")][pick]
    elif word:
        layout = "isim"
        tone = ["vivid", "light", "dark", "vivid", "light", "vivid"][pick]
    elif serious:
        layout, tone = "isik", "dark"
    else:
        layout, tone = "manset", ["light", "vivid"][pick % 2]

    base = {"dark": "#040405", "light": pal[5], "vivid": pal[1]}[tone]
    if tone == "vivid":
        avg = sum(_lum(c) for c in pal[:4]) / 4
        ink = "#111114" if avg > 0.66 else "#FFFFFF"
    else:
        ink = "#FFFFFF" if tone == "dark" else "#111114"
    kw = d.get("focus_keyword") or ""
    if kw.lower() in GENERIC or len(kw.split()) > 3 or kw.lower().startswith("yapay zeka"):
        kw = ""
    headline = _highlight(d.get("short_title") or d.get("title", ""), word or kw) if not serious else html.escape(d.get("short_title") or d.get("title", ""))
    glyph = (word or re.sub(r"[^A-Za-zÇĞİÖŞÜçğıöşü]", "", d.get("short_title") or d.get("title") or "Y") or "Y")[:1].upper()
    return {
        "layout": layout, "tone": tone, "pal": pal[:4] + [base], "palette": pal_name, "seed": seed,
        "kicker": (d.get("kicker") or "") if kicker else "", "stat": stat, "stat_label": (d.get("hero_stat_label") or "").strip(),
        "word": word, "sub": "", "headline": headline, "glyph": glyph,
        "blobs": _blobs(rnd, pal, layout, tone, variant), "brand": brand, "variant": variant, "ink": ink,
        "brand_name": brand_name,
        "caption": (d.get("short_title") or d.get("title", "")) if caption and layout in ("sayi", "isim") else "",
    }
