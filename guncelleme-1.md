YZRADAR-BUNDLE v1 part 1/3
@@@YZ@@@ PATCH haberbot/config.py
--- a/haberbot/config.py
+++ b/haberbot/config.py
@@ -23,4 +23,34 @@
 }
 DEFAULT_CATEGORY = "urunler"
+
+# Kategori sayfaları için arama motoru başlığı ve tanıtım metni
+CATEGORY_SEO: dict[str, tuple[str, str]] = {
+    "modeller": ("Yapay zeka modelleri haberleri",
+                 "GPT, Gemini, Claude, Llama ve diğer büyük dil modellerindeki yeni sürümler, yetenekler ve karşılaştırmalar."),
+    "urunler": ("Yapay zeka ürünleri ve araçları",
+                "ChatGPT, Gemini ve Copilot gibi yapay zeka uygulamalarındaki yeni özellikler, geliştirici araçları ve API güncellemeleri."),
+    "arastirma": ("Yapay zeka araştırmaları",
+                  "Yapay zeka alanındaki yeni bilimsel makaleler, deney sonuçları ve teknik buluşlar."),
+    "sirketler": ("Yapay zeka şirketleri ve yatırımlar",
+                  "OpenAI, Anthropic, Google, NVIDIA ve yapay zeka girişimlerinin yatırım turları, satın almaları ve iş stratejileri."),
+    "politika": ("Yapay zeka regülasyonu ve güvenliği",
+                 "Yapay zeka yasaları, davalar, güvenlik ve etik tartışmaları ile hükümetlerin aldığı kararlar."),
+    "donanim": ("Yapay zeka çipleri ve altyapısı",
+                "GPU'lar, yapay zeka çipleri, veri merkezleri ve enerji altyapısındaki gelişmeler."),
+    "acik-kaynak": ("Açık kaynak yapay zeka",
+                    "Açık ağırlıklı modeller, açık kaynak yapay zeka araçları ve topluluk projeleri."),
+    "turkiye": ("Türkiye'de yapay zeka",
+                "Türkiye'deki yapay zeka girişimleri, yatırımlar, kamu politikaları ve yerli projeler."),
+}
+
+
+def category_seo(slug: str) -> tuple[str, str]:
+    return CATEGORY_SEO.get(slug, (category_label(slug), ""))
+
+
+def indexnow_key(site_url: str) -> str:
+    """IndexNow (Bing/Yandex anlık bildirim) anahtarı: site adresinden türetilir, sitede /<anahtar>.txt olarak durur."""
+    import hashlib
+    return hashlib.sha1(("yzradar-indexnow:" + site_url).encode()).hexdigest()[:32]
 
 
@@@YZ@@@ FILE haberbot/site.py
"""Statik web sitesi üretici: content/posts/*.json → _site/"""
from __future__ import annotations

import html as htmlmod
import json
import re
import shutil
from collections import Counter
from email.utils import format_datetime

import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .config import CATEGORIES, ROOT, Config, category_color, category_label, category_seo, indexnow_key
from .store import Store
from .util import clip, hours_since, iso, local, log, now_utc, parse_iso, slugify, tr_date

ASSET_V = "5"
WHY_RE = re.compile(r"<p><strong>Neden önemli\?</strong>\s*(.*?)</p>", re.S)
H2_RE = re.compile(r"<h[1-3]>(.*?)</h[1-3]>", re.S)


def render_body(md: str) -> str:
    safe = htmlmod.escape(md or "", quote=False)
    out = markdown.markdown(safe, extensions=["sane_lists"], output_format="html")
    out = re.sub(r'href="(?!https?://)[^"]*"', 'href="#"', out)
    out = out.replace('<a href="http', '<a rel="noopener" target="_blank" href="http')
    out = WHY_RE.sub(r'<aside class="why"><strong>Neden önemli?</strong><p>\1</p></aside>', out)
    # Metindeki başlıklar sayfanın H1'i ile yarışmasın: hepsi H2, bağlantılanabilir
    out = H2_RE.sub(lambda m: f'<h2 id="{slugify(re.sub("<[^>]+>", "", m.group(1)), 60)}">{m.group(1)}</h2>', out)
    return out


def nobr_hyphen(title: str) -> str:
    """'GPT-6' gibi kısa tireli sözcüklerin satır sonunda bölünmesini engelle."""
    return re.sub(r"(?<=\w)-(?=\w)", "‑", title or "")


def reading_minutes(text: str) -> int:
    return max(1, round(len((text or "").split()) / 180))


def plain(md: str) -> str:
    s = re.sub(r"[*_`#>]+", "", md or "")
    return re.sub(r"\s+", " ", s).strip()


def tag_slug(tag: str) -> str:
    return slugify(tag, 50)


# Her habere uyan genel sözcükler konu sayfası olmaz
GENERIC_TAGS = {"yapay-zeka", "yapay-zek", "ai", "artificial-intelligence", "teknoloji", "technology", "haber", "haberler",
                "gelisme", "duyuru", "yenilik", "yapay-zeka-haberleri"}


def make_logo(path, size: int = 512) -> None:
    """Marka simgesini (degrade halkalar) PNG olarak üret: arama motorları ve paylaşım için."""
    from PIL import Image, ImageDraw
    s = size * 4
    grad = Image.new("RGB", (s, s))
    stops = [(0, (255, 106, 61)), (.28, (255, 61, 139)), (.58, (162, 89, 255)), (.82, (61, 139, 255)), (1, (34, 199, 232))]
    px = grad.load()
    for x in range(s):
        t = x / (s - 1)
        for i in range(len(stops) - 1):
            a, ca = stops[i]
            b, cb = stops[i + 1]
            if a <= t <= b:
                f = (t - a) / (b - a)
                col = tuple(int(ca[k] + (cb[k] - ca[k]) * f) for k in range(3))
                break
        for y in range(s):
            px[x, y] = col
    mask = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(mask)
    c, r = s / 2, s * 0.40
    for outer, inner in ((1.0, .80), (.66, .46), (.30, 0)):
        d.ellipse([c - r * outer, c - r * outer, c + r * outer, c + r * outer], fill=255)
        if inner:
            d.ellipse([c - r * inner, c - r * inner, c + r * inner, c + r * inner], fill=0)
    bg = Image.new("RGB", (s, s), (255, 255, 255))
    bg.paste(grad, (0, 0), mask)
    bg.resize((size, size), Image.LANCZOS).save(path, "PNG", optimize=True)


class SiteBuilder:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.base = cfg.base_path
        self.skip_tags = GENERIC_TAGS | {slugify(x.get("name", ""), 50) for x in cfg.sources
                                         if x.get("kind") in ("media", "community")}
        self.env = Environment(
            loader=FileSystemLoader(str(ROOT / "templates")),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True, lstrip_blocks=True,
        )

    def _post_view(self, p: dict) -> dict:
        cfg, b = self.cfg, self.base
        pub = p.get("published_at")
        dt = parse_iso(pub) or now_utc()
        mod = parse_iso(p.get("updated_at")) or dt
        ext = "webp" if (cfg.images_dir / f"{p['id']}.webp").exists() else "jpg"
        has_og = (cfg.images_dir / f"{p['id']}-og.jpg").exists()
        title = p.get("title", "")
        short = p.get("short_title") or title
        summary = p.get("summary", "")
        seo_title = clip(p.get("seo_title") or short or title, 62)
        meta = p.get("meta_description") or ""
        if len(meta) < 70:  # yedek: özet + ilk paragraf
            meta = summary if len(summary) >= 110 else f"{summary} {plain(p.get('body', ''))}"
        tags = []
        for t in dict.fromkeys(t.strip() for t in (p.get("tags") or []) if t and t.strip()):
            ts = tag_slug(t)
            if ts and ts not in self.skip_tags and len(tags) < 6:
                tags.append({"label": t, "slug": ts, "url": f"{b}/etiket/{ts}/"})
        cat = p.get("category", "urunler")
        return {
            **p,
            "url": f"{b}/haber/{p['slug']}/",
            "title_disp": nobr_hyphen(title),
            "short_disp": nobr_hyphen(short),
            "kicker_disp": p.get("kicker") or category_label(cat),
            "hero_stat": (p.get("hero_stat") or "").strip(),
            "hero_stat_label": (p.get("hero_stat_label") or "").strip(),
            "ai_image": (p.get("image") or {}).get("source") == "ai",
            "img_alt": clip(p.get("image_alt") or f"{short}: habere ait temsili görsel", 125),
            "seo_title": seo_title,
            "meta_description": clip(meta, 158),
            "focus_keyword": p.get("focus_keyword", ""),
            "tag_list": tags,
            "abs_url": cfg.post_url(p["slug"]),
            "img": f"{b}/img/{p['id']}.{ext}",
            "abs_img": f"{cfg.site_url}/img/{p['id']}.{ext}",
            "abs_og": f"{cfg.site_url}/img/{p['id']}-og.jpg" if has_og else f"{cfg.site_url}/static/og-default.jpg",
            "date_str": tr_date(pub, cfg.tz),
            "date_short": tr_date(pub, cfg.tz, with_time=False),
            "iso": iso(dt),
            "mod_iso": iso(max(mod, dt)),
            "rfc822": format_datetime(dt),
            "cat_label": category_label(cat),
            "cat_seo": category_seo(cat)[0],
            "cat_color": category_color(cat),
            "cat_url": f"{b}/kategori/{cat}/",
            "abs_cat_url": f"{cfg.site_url}/kategori/{cat}/",
            "credits": list(dict.fromkeys(s["name"] for s in p.get("sources", []))),
            "minutes": reading_minutes(p.get("body", "")),
            "words": len(plain(p.get("body", "")).split()),
            "body_html": render_body(p.get("body", "")),
            "updated_str": tr_date(p.get("updated_at"), cfg.tz) if p.get("updated_at") else "",
        }

    def _write(self, rel: str, content: str) -> None:
        path = self.cfg.out_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    @staticmethod
    def _featured(posts: list[dict], n: int) -> list[dict]:
        """Manşet: son 3 günün en önemli haberleri (eşitlikte en yenisi); yetmezse en yeniler."""
        fresh = [p for p in posts if hours_since(p.get("published_at")) <= 72]
        pick = sorted(fresh, key=lambda p: (-int(p.get("importance") or 5), -(parse_iso(p.get("published_at")) or now_utc()).timestamp()))[:n]
        for p in posts:
            if len(pick) >= n:
                break
            if p not in pick:
                pick.append(p)
        return pick

    def build(self) -> int:
        cfg, b = self.cfg, self.base
        seo = cfg.raw.get("seo") or {}
        out = cfg.out_dir
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)
        store = Store(cfg)
        posts = [self._post_view(p) for p in store.posts()]
        counts = Counter(p["category"] for p in posts)
        latest_by_cat: dict[str, str] = {}
        for p in posts:
            latest_by_cat.setdefault(p["category"], p["mod_iso"])
        cats = [{"slug": k, "label": v[0], "color": v[1], "count": counts.get(k, 0),
                 "seo_title": category_seo(k)[0], "intro": category_seo(k)[1],
                 "url": f"{b}/kategori/{k}/", "lastmod": latest_by_cat.get(k)} for k, v in CATEGORIES.items()]

        # etiketler (konular)
        tag_posts: dict[str, list[dict]] = {}
        tag_label: dict[str, Counter] = {}
        for p in posts:
            for t in p["tag_list"]:
                tag_posts.setdefault(t["slug"], []).append(p)
                tag_label.setdefault(t["slug"], Counter())[t["label"]] += 1
        tags = sorted(({"slug": s, "label": tag_label[s].most_common(1)[0][0], "count": len(ps),
                        "url": f"{b}/etiket/{s}/", "lastmod": ps[0]["mod_iso"]}
                       for s, ps in tag_posts.items()), key=lambda t: (-t["count"], t["label"].lower()))

        now_l = local(now_utc(), cfg.tz)
        key = indexnow_key(cfg.site_url)
        site = {
            **cfg.site,
            "base": b,
            "url": cfg.site_url,
            "year": now_l.year,
            "categories": cats,
            "nav_categories": [c for c in cats if c["count"] > 0] or cats[:6],
            "top_tags": [t for t in tags if t["count"] >= 2][:14],
            "built": tr_date(now_utc(), cfg.tz),
            "built_iso": iso(now_utc()),
            "today_count": sum(1 for p in posts if (local(p["published_at"], cfg.tz) or now_l).date() == now_l.date()),
            "og_image": f"{cfg.site_url}/static/og-default.jpg",
            "logo": f"{cfg.site_url}/static/logo.png",
            "asset_v": ASSET_V,
            "home_title": seo.get("home_title") or f"{cfg.site.get('name')}: {cfg.site.get('tagline')}",
            "home_description": seo.get("home_description") or cfg.site.get("description", ""),
            "verify": {k: seo.get(k) for k in ("google_site_verification", "bing_site_verification", "yandex_verification")},
        }
        ctx = {"site": site}

        # statik dosyalar, logo ve görseller
        shutil.copytree(ROOT / "static", out / "static")
        try:
            make_logo(out / "static" / "logo.png", 512)
            make_logo(out / "static" / "apple-touch-icon.png", 180)
        except Exception as e:  # noqa: BLE001
            log.warning("Logo üretilemedi: %s", e)
        (out / "img").mkdir()
        for p in posts:
            for name in (f"{p['id']}.webp", f"{p['id']}.jpg", f"{p['id']}-og.jpg"):
                src = cfg.images_dir / name
                if src.exists():
                    shutil.copy2(src, out / "img" / name)

        # ana sayfa: manşet + son haberler; devamı arşiv sayfalarında
        n_feat = int(seo.get("featured_count", 5) or 5)
        featured = self._featured(posts, n_feat)
        rest = [p for p in posts if p not in featured]
        latest = rest[:12] if len(rest) >= 3 else posts[:6]
        if len(latest) > 3:
            latest = latest[:len(latest) - len(latest) % 3]
        shown = {p["id"] for p in featured} | {p["id"] for p in latest}
        archive = [p for p in posts if p["id"] not in shown]
        per = int(cfg.site.get("posts_per_page", 18))
        pages = 1 + (len(archive) + per - 1) // per
        rails = []
        for c in sorted(cats, key=lambda c: -c["count"]):
            cp = [p for p in posts if p["category"] == c["slug"]]
            if len(cp) >= 4 and len(rails) < 3:
                rails.append({"cat": c, "posts": cp[:10]})
        self._write("index.html", self.env.get_template("index.html").render(
            **ctx, featured=featured, latest=latest, rails=rails, tags=site["top_tags"],
            page=1, pages=pages, next_url=f"{b}/sayfa/2/" if pages > 1 else None,
            canonical=cfg.site_url + "/"))
        for n in range(2, pages + 1):
            chunk = archive[(n - 2) * per:(n - 1) * per]
            self._write(f"sayfa/{n}/index.html", self.env.get_template("archive.html").render(
                **ctx, posts=chunk, page=n, pages=pages,
                prev_url=f"{b}/" if n == 2 else f"{b}/sayfa/{n - 1}/",
                next_url=f"{b}/sayfa/{n + 1}/" if n < pages else None,
                canonical=f"{cfg.site_url}/sayfa/{n}/"))

        # haber sayfaları
        for p in posts:
            same_tag = {t["slug"] for t in p["tag_list"]}
            related = sorted((q for q in posts if q["id"] != p["id"]),
                             key=lambda q: (-(len(same_tag & {t["slug"] for t in q["tag_list"]}) * 2
                                              + (q["category"] == p["category"])), posts.index(q)))[:8]
            self._write(f"haber/{p['slug']}/index.html", self.env.get_template("article.html").render(
                **ctx, post=p, related=related, canonical=p["abs_url"]))

        # kategoriler
        for c in cats:
            cp = [p for p in posts if p["category"] == c["slug"]][:120]
            self._write(f"kategori/{c['slug']}/index.html", self.env.get_template("category.html").render(
                **ctx, cat=c, posts=cp, active_cat=c["slug"], canonical=f"{cfg.site_url}/kategori/{c['slug']}/",
                noindex=not cp))

        # konu (etiket) sayfaları: tek haberlik konular dizine eklenmez (ince içerik)
        for t in tags:
            self._write(f"etiket/{t['slug']}/index.html", self.env.get_template("tag.html").render(
                **ctx, tag=t, posts=tag_posts[t["slug"]][:120], canonical=f"{cfg.site_url}/etiket/{t['slug']}/",
                noindex=t["count"] < 2))

        self._write("hakkinda/index.html", self.env.get_template("about.html").render(
            **ctx, canonical=f"{cfg.site_url}/hakkinda/",
            sources=[s for s in cfg.sources]))
        self._write("404.html", self.env.get_template("404.html").render(**ctx, canonical=cfg.site_url + "/", noindex=True))

        # besleme, site haritaları, robots, IndexNow anahtarı, json
        self._write("feed.xml", self.env.get_template("feed.xml").render(
            **ctx, posts=posts[:40], now_rfc=format_datetime(now_utc())))
        self._write("sitemap.xml", self.env.get_template("sitemap.xml").render(
            **ctx, posts=posts, cats=[c for c in cats if c["count"]], tags=[t for t in tags if t["count"] >= 2],
            pages=pages))
        news = [p for p in posts if hours_since(p.get("published_at")) <= 48][:1000]
        self._write("news-sitemap.xml", self.env.get_template("news-sitemap.xml").render(**ctx, posts=news))
        self._write("robots.txt", "User-agent: *\nAllow: /\nDisallow: /api/\n\n"
                                  f"Sitemap: {cfg.site_url}/sitemap.xml\nSitemap: {cfg.site_url}/news-sitemap.xml\n")
        self._write(f"{key}.txt", key)
        latest_json = [{"id": p["id"], "title": p["title"], "summary": p["summary"], "url": p["abs_url"],
                        "image": p["abs_img"], "og_image": p["abs_og"], "category": p["category"],
                        "published_at": p["published_at"],
                        "sources": [{"name": s["name"], "url": s["url"]} for s in p.get("sources", [])]}
                       for p in posts[:50]]
        self._write("api/latest.json", json.dumps(latest_json, ensure_ascii=False, indent=1))
        (out / ".nojekyll").write_text("")
        log.info("Site üretildi: %d haber, %d sayfa, %d konu → %s", len(posts), pages, len(tags), out)
        return len(posts)
@@@YZ@@@ PATCH haberbot/app.py
--- a/haberbot/app.py
+++ b/haberbot/app.py
@@ -6,11 +6,14 @@
 import re
 import time
+from urllib.parse import urlsplit
+
+import requests
 
 from . import policy
-from .config import CATEGORIES, Config, category_label
+from .config import CATEGORIES, Config, category_label, indexnow_key
 from .extract import full_text
 from .llm import LLMError, MockLLM, estimate_cost, make_llm
-from .prompts import (FLAG_LABELS, FLAGS, TRIAGE_SCHEMA, WRITE_SCHEMA, triage_system,
-                      triage_user, write_system, write_user)
+from .prompts import (FLAG_LABELS, FLAGS, SEO_SCHEMA, TRIAGE_SCHEMA, WRITE_SCHEMA, seo_system, seo_user,
+                      triage_system, triage_user, write_system, write_user)
 from .sources import fetch_all
 from .store import Store
@@ -249,5 +252,5 @@
             "body": (out.get("body") or "").strip(),
             "category": cat,
-            "tags": [clip(t, 30) for t in (out.get("tags") or [])][:5],
+            "tags": [clip(t, 30) for t in (out.get("tags") or [])][:6],
             "confidence": out.get("confidence") if out.get("confidence") in CONF_LABEL else "orta",
             "flags": [f for f in (out.get("flags") or []) if f in FLAGS],
@@ -259,4 +262,9 @@
             "visual_style": out.get("visual_style") or "studio",
             "visual_scene": clip((out.get("visual_scene") or "").strip(), 600),
+            "focus_keyword": clip((out.get("focus_keyword") or "").strip(), 60),
+            "seo_title": clip((out.get("seo_title") or "").strip().rstrip("."), 62),
+            "meta_description": clip((out.get("meta_description") or "").strip(), 170),
+            "seo_slug": slugify(out["slug"], 64) if (out.get("slug") or "").strip() else "",
+            "image_alt": clip((out.get("image_alt") or "").strip(), 125),
         }
 
@@ -332,5 +340,5 @@
         st = self.store
         used = {p.get("slug") for p in st.posts()}
-        base = slugify(d["title"])
+        base = d.get("seo_slug") if len(d.get("seo_slug") or "") >= 12 else slugify(d["title"], 64)
         slug, n = base, 2
         while slug in used:
@@ -338,4 +346,5 @@
         post = {k: v for k, v in d.items() if k not in ("source_texts", "status", "policy_reason")}
         post.update({"slug": slug, "published_at": iso(now_utc()), "publish_mode": "auto" if auto else "manual"})
+        self.queue_indexnow(self.cfg.post_url(slug))
         st.move_image_to_post(d["id"])
         if not st.post_image(d["id"]).exists():
@@ -363,4 +372,6 @@
         lines = [head, "", f"<b>{esc(d['title'])}</b>", "", "{SUMMARY}", "",
                  "📰 " + esc(", ".join(self._credits(d))), meta]
+        if d.get("focus_keyword") and kind in ("pending", "auto"):
+            lines.append(f"🔎 Google: <i>{esc(d['focus_keyword'])}</i>")
         if d.get("flags"):
             fl = ", ".join(FLAG_LABELS.get(f, f) for f in d["flags"])
@@ -755,4 +766,57 @@
                 st.archive_draft(d, "rejected")
 
+    # ── ARAMA MOTORLARI ─────────────────────────────────────
+    def queue_indexnow(self, url: str) -> None:
+        q = self.state.setdefault("indexnow_queue", [])
+        if url not in q:
+            q.append(url)
+
+    def flush_indexnow(self) -> None:
+        """Önceki turda yayınlanan adresleri Bing/Yandex'e bildir (IndexNow). Site o arada yayına girmiş olur."""
+        q = self.state.get("indexnow_queue") or []
+        if not q or self.cfg.mock or not (self.cfg.raw.get("seo") or {}).get("indexnow", True):
+            return
+        site = self.cfg.site_url
+        if "localhost" in site:
+            return
+        key = indexnow_key(site)
+        urls = list(dict.fromkeys(q + [site + "/"]))[:500]
+        try:
+            r = requests.post("https://api.indexnow.org/indexnow", timeout=20, json={
+                "host": urlsplit(site).netloc, "key": key, "keyLocation": f"{site}/{key}.txt", "urlList": urls})
+            log.info("IndexNow: %d adres bildirildi (HTTP %s)", len(urls), r.status_code)
+            if r.status_code < 300 or r.status_code in (400, 403, 422):
+                self.state["indexnow_queue"] = []
+        except requests.RequestException as e:
+            log.warning("IndexNow bildirimi başarısız: %s", e)
+
+    def backfill_seo(self, limit: int = 3) -> None:
+        """SEO bilgisi olmayan eski haberlere (metnine dokunmadan) arama başlığı ve açıklaması ekle."""
+        if not self.llm:
+            return
+        todo = [p for p in self.store.posts() if not p.get("seo_title") and not p.get("seo_skip")][:limit]
+        for p in todo:
+            try:
+                out = self.llm.json(self.cfg.get("ai", "triage_model", "gemini-flash-lite-latest"),
+                                    seo_system(self.brand), seo_user(p), SEO_SCHEMA, max_tokens=2000)
+            except LLMError as e:
+                log.warning("SEO bilgisi üretilemedi (%s): %s", p["id"], e)
+                p["seo_tries"] = int(p.get("seo_tries", 0)) + 1
+                if p["seo_tries"] >= 3:
+                    p["seo_skip"] = True
+                self.store.save_post(p)
+                return
+            p["focus_keyword"] = clip((out.get("focus_keyword") or "").strip(), 60)
+            p["seo_title"] = clip((out.get("seo_title") or "").strip().rstrip("."), 62) or p.get("short_title") or p["title"]
+            p["meta_description"] = clip((out.get("meta_description") or "").strip(), 170)
+            p["image_alt"] = clip((out.get("image_alt") or "").strip(), 125)
+            tags = [clip(t, 30) for t in (out.get("tags") or []) if t and t.strip()][:6]
+            if len(tags) >= 2:
+                p["tags"] = tags
+            self.store.save_post(p)
+            self.store.site_dirty = True
+            self.queue_indexnow(self.cfg.post_url(p["slug"]))
+            log.info("SEO bilgisi eklendi: %s → %s", p["id"], p["seo_title"])
+
     def maybe_summary(self) -> None:
         now_l = local(now_utc(), self.cfg.tz)
@@ -796,4 +860,5 @@
             log.warning("TELEGRAM_CHAT_ID tanımlı değil; bota /start yaz, numaranı söyleyecek.")
 
+        self.flush_indexnow()
         self.process_updates()
         self.expire()
@@ -807,4 +872,6 @@
                 log.exception("Toplama hatası: %s", e)
                 self.notify_error(f"Toplama sırasında hata: {type(e).__name__}: {e}")
+        if not self.state.get("paused"):
+            self.backfill_seo()
         self.maybe_summary()
         self.listen(int(self.cfg.get("schedule", "listen_seconds", 120) or 0))
@@@YZ@@@ PATCH haberbot/prompts.py
--- a/haberbot/prompts.py
+++ b/haberbot/prompts.py
@@ -105,7 +105,13 @@
         "visual_style": {"type": "string", "enum": ["studio", "macro", "diorama", "sculpture", "still_life"]},
         "visual_scene": {"type": "string"},
+        "focus_keyword": {"type": "string"},
+        "seo_title": {"type": "string"},
+        "meta_description": {"type": "string"},
+        "slug": {"type": "string"},
+        "image_alt": {"type": "string"},
     },
     "required": ["title", "summary", "body", "category", "tags", "confidence", "flags", "editor_note",
-                 "short_title", "kicker", "hero_stat", "hero_stat_label", "visual_style", "visual_scene"],
+                 "short_title", "kicker", "hero_stat", "hero_stat_label", "visual_style", "visual_scene",
+                 "focus_keyword", "seo_title", "meta_description", "slug", "image_alt"],
     "additionalProperties": False,
 }
@@ -130,10 +136,20 @@
 - Money: "350 milyon dolar". Avoid "bugün/dün"; use explicit dates like "22 Eylül'de" when the sources give them.
 
+SEO (the site must rank on Google for Turkish searches — write for readers first, never keyword-stuff):
+- First decide focus_keyword: the 2–4 word Turkish phrase a Turkish reader would most likely type into Google to find THIS news, built around the main entity (e.g. "GPT-6 Sol", "Anthropic Opus 5.5", "Nvidia yapay zeka çipi", "OpenAI yatırım"). Lowercase except proper nouns.
+- Use the focus_keyword (or a natural inflection of it) in: title, the first sentence of the body, seo_title, meta_description, and at least one subheading. Keep it natural Turkish; never repeat it more than 3 times in the body.
+- Mention the full, official names of the companies, products and models involved at least once (e.g. "Google DeepMind", "Gemini 3.5 Flash"), since people search for these names.
+
 Output fields:
-- title: ≤90 characters, informative and specific (who did what). Sentence case (only first word and proper nouns capitalized). No trailing period.
-- summary: 1–2 sentences, ≤220 characters, the core news.
