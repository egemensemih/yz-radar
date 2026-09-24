YZRADAR-BUNDLE v1 part 1/1
@@@YZ@@@ PATCH haberbot/site.py
--- a/haberbot/site.py
+++ b/haberbot/site.py
@@ -16,5 +16,5 @@
 from .util import clip, hours_since, iso, local, log, now_utc, parse_iso, slugify, tr_date
 
-ASSET_V = "5"
+ASSET_V = "6"
 WHY_RE = re.compile(r"<p><strong>Neden önemli\?</strong>\s*(.*?)</p>", re.S)
 H2_RE = re.compile(r"<h[1-3]>(.*?)</h[1-3]>", re.S)
@@ -53,4 +53,17 @@
 GENERIC_TAGS = {"yapay-zeka", "yapay-zek", "ai", "artificial-intelligence", "teknoloji", "technology", "haber", "haberler",
                 "gelisme", "duyuru", "yenilik", "yapay-zeka-haberleri"}
+
+
+def edge_color(path) -> tuple[str, bool]:
+    """Görselin sol kenar rengi: manşet zemini bu renge boyanır, görsel dikişsiz kaynaşır."""
+    from PIL import Image
+    try:
+        im = Image.open(path).convert("RGB")
+    except Exception:  # noqa: BLE001
+        return "#F5F5F7", False
+    w, h = im.size
+    r, g, b = im.crop((0, 0, max(2, int(w * .05)), h)).resize((1, 1), Image.BOX).getpixel((0, 0))
+    lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
+    return f"#{r:02X}{g:02X}{b:02X}", lum < .5
 
 
@@ -236,4 +249,7 @@
         n_feat = int(seo.get("featured_count", 5) or 5)
         featured = self._featured(posts, n_feat)
+        for p in featured:
+            src = cfg.images_dir / p["img"].rsplit("/", 1)[-1]
+            p["slide_bg"], p["slide_dark"] = edge_color(src)
         rest = [p for p in posts if p not in featured]
         latest = rest[:12] if len(rest) >= 3 else posts[:6]
@@ -251,4 +267,6 @@
         self._write("index.html", self.env.get_template("index.html").render(
             **ctx, featured=featured, latest=latest, rails=rails, tags=site["top_tags"],
+            latest_iso=max((q["iso"] for q in posts), default=site["built_iso"]),
+            latest_str=tr_date(max((q.get("published_at") or "" for q in posts), default=None), cfg.tz),
             page=1, pages=pages, next_url=f"{b}/sayfa/2/" if pages > 1 else None,
             canonical=cfg.site_url + "/"))
@@@YZ@@@ PATCH haberbot/prompts.py
--- a/haberbot/prompts.py
+++ b/haberbot/prompts.py
@@ -148,5 +148,5 @@
 - tags: 3–6 tags that people search for: companies, products, models, technologies, places (e.g. "OpenAI", "GPT-6", "Nvidia", "Avrupa Birliği", "büyük dil modelleri"). Use the official spelling consistently. Never use generic words like "yapay zeka", "teknoloji", "haber", and never use the names of news outlets (TechCrunch, The Verge…).
 - focus_keyword: as described above.
-- seo_title: ≤58 characters, the title shown in Google results. Starts with the focus_keyword or puts it near the start; specific and compelling but not clickbait; may differ from title. No site name, no trailing period.
+- seo_title: ≤58 characters, the title shown in Google results. Starts with the focus_keyword or puts it near the start; specific and compelling but not clickbait; may differ from title. Sentence case. No site name, no trailing period.
 - meta_description: 140–156 characters, one or two sentences in active voice that contain the focus_keyword and tell the reader exactly what they will learn. No quotes, no emojis.
 - slug: URL slug in lowercase ASCII (convert ç→c, ğ→g, ı→i, ö→o, ş→s, ü→u), words separated by hyphens, 3–7 words, ≤60 characters, based on the focus_keyword plus the key action (e.g. "openai-gpt-6-sol-ve-luna-modellerini-duyurdu"). No stop-word padding, no dates.
@@ -207,5 +207,5 @@
 Do NOT change the article. Produce search metadata in natural Türkiye Türkçesi that is faithful to the article — never add facts that are not in it.
 - focus_keyword: the 2–4 word Turkish phrase a reader would most likely type into Google to find this news, built around the main entity.
-- seo_title: ≤58 characters, starts with or contains the focus_keyword near the start, specific, no clickbait, no site name, no trailing period.
+- seo_title: ≤58 characters, starts with or contains the focus_keyword near the start, specific, sentence case (only first word and proper nouns capitalized), no clickbait, no site name, no trailing period.
 - meta_description: 140–156 characters, active voice, contains the focus_keyword, tells the reader what they will learn. No quotes, no emojis.
 - image_alt: ≤120 characters, describes the cover image (described in VISUAL) and relates it to the news topic.
@@@YZ@@@ PATCH templates/_macros.html
--- a/templates/_macros.html
+++ b/templates/_macros.html
@@ -25,8 +25,6 @@
 
 {% macro slide(p, i, n) %}
-<article class="slide" role="group" aria-roledescription="slayt" aria-label="{{ i }} / {{ n }}" style="--c:{{ p.cat_color }}" data-i="{{ i - 1 }}">
+<article class="slide{{ ' dark' if p.slide_dark }}" role="group" aria-roledescription="slayt" aria-label="{{ i }} / {{ n }}" style="--c:{{ p.cat_color }}; --sbg:{{ p.slide_bg or '#F5F5F7' }}" data-i="{{ i - 1 }}">
   <a class="slide-in" href="{{ p.url }}">
-    {{ img(p, 'slide-img', eager=(i == 1), sizes='(min-width: 1232px) 1200px, 100vw', priority=(i == 1)) }}
-    <span class="slide-scrim" aria-hidden="true"></span>
     <span class="slide-txt">
       <span class="slide-top">
@@ -36,6 +34,8 @@
       <h2>{{ p.title_disp }}</h2>
       <span class="slide-dek">{{ p.summary }}</span>
-      <span class="slide-meta"><time datetime="{{ p.iso }}" data-rel>{{ p.date_str }}</time> · Kaynak: {{ p.credits|join(', ') }}</span>
+      <span class="slide-meta"><time datetime="{{ p.iso }}" data-rel>{{ p.date_str }}</time> · {{ p.credits|join(', ') }}</span>
+      <span class="more">Haberi oku</span>
     </span>
+    <span class="slide-media">{{ img(p, 'slide-img', eager=(i == 1), sizes='(min-width: 900px) 640px, 100vw', priority=(i == 1)) }}</span>
   </a>
 </article>
@@@YZ@@@ PATCH templates/index.html
--- a/templates/index.html
+++ b/templates/index.html
@@ -21,5 +21,5 @@
   <h1>Yapay zeka haberleri</h1>
   {% if featured %}
-  <p class="live" role="status"><span class="dot" aria-hidden="true"></span>Canlı · Son güncelleme <b><time datetime="{{ site.built_iso }}" data-rel>{{ site.built }}</time></b>{% if site.today_count %} · Bugün <b>{{ site.today_count }}</b> gelişme{% endif %}</p>
+  <p class="live" role="status"><span class="dot" aria-hidden="true"></span>Son haber <b><time datetime="{{ latest_iso }}" data-rel data-live>{{ latest_str }}</time></b>{% if site.today_count %} · Bugün <b>{{ site.today_count }}</b> gelişme{% endif %}</p>
   {% endif %}
 </header>
@@ -31,6 +31,8 @@
 {% else %}
   <section class="car" aria-roledescription="carousel" aria-label="Öne çıkan yapay zeka haberleri" data-interval="6500">
-    <div class="car-track" id="car-track">
-      {% for p in featured %}{{ slide(p, loop.index, loop.length) }}{% endfor %}
+    <div class="car-view wrap">
+      <div class="car-track" id="car-track">
+        {% for p in featured %}{{ slide(p, loop.index, loop.length) }}{% endfor %}
+      </div>
     </div>
     {% if featured|length > 1 %}
@@@YZ@@@ PATCH static/style.css
--- a/static/style.css
+++ b/static/style.css
@@ -79,4 +79,5 @@
 .home-head h1 { margin: 0; font-size: clamp(28px, 4vw, 44px); letter-spacing: -.04em; line-height: 1.05; font-weight: 700; }
 .live { margin: 0; font-size: 14px; color: var(--muted); }
+.live.stale .dot { display: none; }
 .live b { font-weight: 600; color: var(--ink); }
 .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #30D158; margin-right: 8px;
@@ -85,36 +86,41 @@
 
 /* ── kaydırmalı manşet ─────────────────── */
-.car { position: relative; --gap: 12px; --pad: max(16px, (100% - 1200px) / 2); }
-.car-track { display: grid; grid-auto-flow: column; grid-auto-columns: min(1200px, 100% - 32px); gap: var(--gap);
-  overflow-x: auto; overscroll-behavior-x: contain; scroll-snap-type: x mandatory; scroll-padding-inline: var(--pad);
-  padding-inline: var(--pad); scrollbar-width: none; -webkit-overflow-scrolling: touch; }
+.car { position: relative; }
+.car-view { border-radius: var(--r-lg); overflow: hidden; isolation: isolate; }
+.car-track { display: grid; grid-auto-flow: column; grid-auto-columns: 100%; overflow-x: auto; overscroll-behavior-x: contain;
+  scroll-snap-type: x mandatory; scrollbar-width: none; -webkit-overflow-scrolling: touch; }
 .car-track::-webkit-scrollbar { display: none; }
-.slide { scroll-snap-align: start; scroll-snap-stop: always; border-radius: var(--r-lg); overflow: hidden; background: #1D1D1F;
-  position: relative; aspect-ratio: 4 / 5; isolation: isolate; }
-@media (min-width: 600px) { .slide { aspect-ratio: 4 / 3; } }
-@media (min-width: 900px) { .slide { aspect-ratio: 16 / 7.4; } }
-.slide-in { position: absolute; inset: 0; display: block; color: #fff; }
-.slide-img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; transform: scale(1.02);
+.slide { scroll-snap-align: start; scroll-snap-stop: always; position: relative; background: var(--sbg, #F5F5F7); }
+.slide-in { display: grid; grid-template-columns: minmax(0, 1fr); color: var(--ink); height: 100%; }
+.slide-media { position: relative; order: -1; aspect-ratio: 4 / 3; overflow: hidden; }
+.slide-img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover;
+  -webkit-mask-image: linear-gradient(to bottom, #000 70%, transparent); mask-image: linear-gradient(to bottom, #000 70%, transparent);
   transition: transform 1.2s var(--ease); }
-.slide.on .slide-img { transform: scale(1.07); transition-duration: 7s; }
-.slide-in:hover .slide-img { transform: scale(1.05); }
-.slide-scrim { position: absolute; inset: 0; background:
-  linear-gradient(to top, rgba(0,0,0,.86) 0%, rgba(0,0,0,.62) 32%, rgba(0,0,0,.18) 62%, rgba(0,0,0,0) 78%),
-  linear-gradient(to right, rgba(0,0,0,.28), rgba(0,0,0,0) 60%); }
-.slide-txt { position: absolute; left: 0; right: 0; bottom: 0; padding: 22px 20px 24px; display: grid; gap: 10px; justify-items: start; }
-@media (min-width: 900px) { .slide-txt { padding: 44px 56px 48px; max-width: 900px; gap: 14px; } }
+.slide-in:hover .slide-img { transform: scale(1.03); }
+.slide-txt { display: grid; gap: 10px; justify-items: start; align-content: center; padding: 4px 20px 28px; position: relative; z-index: 1; }
 .slide-top { display: flex; flex-wrap: wrap; gap: 8px; }
 .chip { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 600; letter-spacing: .01em; padding: 6px 12px;
-  border-radius: 999px; background: color-mix(in srgb, var(--c) 82%, #000); color: #fff; }
-.stat-chip { background: rgba(255,255,255,.16); -webkit-backdrop-filter: blur(12px); backdrop-filter: blur(12px); font-weight: 500; }
+  border-radius: 999px; background: color-mix(in srgb, var(--c) 86%, #000); color: #fff; }
+.stat-chip { background: rgba(255,255,255,.72); color: var(--ink); font-weight: 500; }
 .stat-chip b { font-weight: 700; }
-.slide h2 { margin: 0; font-size: clamp(26px, 4.4vw, 54px); line-height: 1.06; letter-spacing: -.035em; font-weight: 700;
-  text-wrap: balance; text-shadow: 0 2px 24px rgba(0,0,0,.25); }
-.slide-dek { display: none; font-size: 19px; line-height: 1.4; color: rgba(255,255,255,.86); max-width: 62ch; letter-spacing: -.01em;
-  overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
+.slide h2 { margin: 0; font-size: clamp(26px, 3.3vw, 46px); line-height: 1.08; letter-spacing: -.035em; font-weight: 700; text-wrap: balance; }
+.slide-dek { font-size: 17px; line-height: 1.45; color: var(--ink-2); max-width: 46ch;
+  overflow: hidden; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; }
+.slide-meta { font-size: 14px; color: var(--muted); }
+.slide .more { margin-top: 4px; }
+.slide-in:hover .more { text-decoration: underline; text-underline-offset: 3px; }
+.slide-in:focus-visible { outline-offset: -4px; }
+.slide.dark .slide-in { color: #fff; }
+.slide.dark .slide-dek { color: rgba(255,255,255,.82); }
+.slide.dark .slide-meta { color: rgba(255,255,255,.66); }
+.slide.dark .more { color: #6CB4FF; }
+.slide.dark .stat-chip { background: rgba(255,255,255,.16); color: #fff; }
 @media (max-width: 599px) { .slide-dek { display: none; } }
-.slide-meta { font-size: 14px; color: rgba(255,255,255,.72); }
-.slide-in:hover h2 { text-decoration: underline; text-decoration-thickness: 2px; text-underline-offset: 6px; }
-.slide-in:focus-visible { outline-offset: -4px; outline-color: #fff; }
+@media (min-width: 800px) {
+  .slide-in { grid-template-columns: minmax(0, .95fr) minmax(0, 1.05fr); min-height: clamp(420px, 42vw, 540px); }
+  .slide-media { order: 0; aspect-ratio: auto; }
+  .slide-img { -webkit-mask-image: linear-gradient(to right, transparent 0, #000 26%); mask-image: linear-gradient(to right, transparent 0, #000 26%); }
+  .slide-txt { padding: 48px 8px 48px 56px; gap: 14px; }
+}
 
 .car-ui { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding-top: 16px; }
@@ -295,5 +301,5 @@
   ::view-transition-old(root), ::view-transition-new(root) { animation-duration: .35s; }
   @supports (animation-timeline: view()) {
-    .reveal { animation: reveal linear both; animation-timeline: view(); animation-range: entry 0% cover 22%; }
+    .reveal { animation: reveal linear both; animation-timeline: view(); animation-range: entry 0% entry 60%; }
     .art-media .ph { animation: settle linear both; animation-timeline: view(); animation-range: entry 0% cover 45%; }
     .progress { animation: grow-x linear both; animation-timeline: scroll(root); }
@@ -303,7 +309,7 @@
   .slide.on .slide-txt > *:nth-child(4) { animation-delay: .18s; }
 }
-@keyframes reveal { from { opacity: 0; transform: translateY(48px); } to { opacity: 1; transform: none; } }
+@keyframes reveal { from { opacity: .5; transform: translateY(20px); } to { opacity: 1; transform: none; } }
 @keyframes settle { from { transform: scale(.92); border-radius: 48px; } to { transform: scale(1); } }
 @keyframes rise { from { opacity: 0; transform: translateY(18px); } to { opacity: 1; transform: none; } }
 @keyframes grow-x { to { transform: scaleX(1); } }
-@media (prefers-reduced-motion: reduce) { .dot { animation: none; } * { transition: none !important; } .slide.on .slide-img { transform: none; } }
+@media (prefers-reduced-motion: reduce) { .dot { animation: none; } * { transition: none !important; } }
@@@YZ@@@ PATCH static/site.js
--- a/static/site.js
+++ b/static/site.js
@@ -8,4 +8,5 @@
     var s = m < 1 ? "az önce" : m < 60 ? m + " dk önce" : m < 1440 ? Math.round(m / 60) + " saat önce" : m < 10080 ? Math.round(m / 1440) + " gün önce" : null;
     if (s) { t.title = t.textContent; t.textContent = s; }
+    if (t.hasAttribute("data-live") && m > 180) { var l = t.closest(".live"); if (l) l.classList.add("stale"); }
   });
 
@@@YZ@@@ SHA
3bbfa926413b8983d501412752ef9a315c74f0d025d5a36db5bfd601778affeb haberbot/site.py
0f93ac4a95bf4cca5215807d79c166890ba0dea5e2729c2b760c3151340e5740 haberbot/prompts.py
efd3a0b76395321c7f7b118b0dcfd7e9ac5cb59b55f30ef8a08e405b133c9912 templates/_macros.html
ade8017367aceacc3427f86c9bef6585c2f240a68557c1e0f3920ab9a32ffad7 templates/index.html
4bb52dbcb9a8f7b61212188734564750b319fd669cf052bc28b47f0f5fd753a3 static/style.css
eaf6120c77118cd36acb396f214bcbcb1c0158209a35210e394b0b28db331736 static/site.js
