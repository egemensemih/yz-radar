YZRADAR-BUNDLE v1 part 3/3
<section class="wrap"><div class="grid">{% for p in posts %}{{ card(p, heading='h2') }}{% endfor %}</div></section>
{% endblock %}
@@@YZ@@@ PATCH templates/about.html
--- a/templates/about.html
+++ b/templates/about.html
@@ -1,4 +1,5 @@
 {% extends "base.html" %}
-{% block title %}Hakkında — {{ site.name }}{% endblock %}
+{% block title %}Hakkında ve yayın ilkeleri | {{ site.name }}{% endblock %}
+{% block description %}{{ site.name }} nasıl çalışır? Kaynak gösterme, doğruluk ve düzeltme ilkelerimiz, takip ettiğimiz yapay zeka kaynakları.{% endblock %}
 {% block main %}
 <header class="page-head wrap" style="--c:#6E6E73">
@@@YZ@@@ FILE templates/sitemap.xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
  <url><loc>{{ site.url }}/</loc><lastmod>{{ site.built_iso }}</lastmod></url>
  <url><loc>{{ site.url }}/hakkinda/</loc></url>
  {% for n in range(2, pages + 1) %}
  <url><loc>{{ site.url }}/sayfa/{{ n }}/</loc></url>
  {% endfor %}
  {% for c in cats %}
  <url><loc>{{ site.url }}/kategori/{{ c.slug }}/</loc>{% if c.lastmod %}<lastmod>{{ c.lastmod }}</lastmod>{% endif %}</url>
  {% endfor %}
  {% for t in tags %}
  <url><loc>{{ site.url }}/etiket/{{ t.slug }}/</loc><lastmod>{{ t.lastmod }}</lastmod></url>
  {% endfor %}
  {% for p in posts %}
  <url>
    <loc>{{ p.abs_url }}</loc><lastmod>{{ p.mod_iso }}</lastmod>
    <image:image><image:loc>{{ p.abs_img }}</image:loc></image:image>
  </url>
  {% endfor %}
</urlset>
@@@YZ@@@ FILE templates/news-sitemap.xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
  {% for p in posts %}
  <url>
    <loc>{{ p.abs_url }}</loc>
    <news:news>
      <news:publication><news:name>{{ site.name }}</news:name><news:language>tr</news:language></news:publication>
      <news:publication_date>{{ p.iso }}</news:publication_date>
      <news:title>{{ p.title }}</news:title>
    </news:news>
  </url>
  {% endfor %}
</urlset>
@@@YZ@@@ PATCH static/style.css
--- a/static/style.css
+++ b/static/style.css
@@ -75,6 +75,8 @@
 @media (min-width: 900px) { .nav-links { display: flex; } .menu { display: none; } }
 
-/* ── canlı şerit ───────────────────────── */
-.live { background: var(--bg-alt); font-size: 14px; color: var(--ink-2); text-align: center; padding: 12px 16px; }
+/* ── ana sayfa başlığı ─────────────────── */
+.home-head { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: 6px 20px; padding-block: 28px 18px; }
+.home-head h1 { margin: 0; font-size: clamp(28px, 4vw, 44px); letter-spacing: -.04em; line-height: 1.05; font-weight: 700; }
+.live { margin: 0; font-size: 14px; color: var(--muted); }
 .live b { font-weight: 600; color: var(--ink); }
 .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #30D158; margin-right: 8px;
@@ -82,16 +84,75 @@
 @keyframes pulse { 70% { box-shadow: 0 0 0 9px rgba(48, 209, 88, 0); } 100% { box-shadow: 0 0 0 0 rgba(48, 209, 88, 0); } }
 
-/* ── manşet ───────────────────────────── */
-.hero { text-align: center; padding-block: 56px 0; padding-inline: 16px; overflow: hidden; }
-.hero .eyebrow { font-size: 21px; }
-.hero h1 { font-size: clamp(34px, 6.2vw, 80px); line-height: 1.04; letter-spacing: -.04em; font-weight: 700;
-  margin: 10px auto 0; max-width: 17ch; text-wrap: balance; }
-.hero .dek { font-size: clamp(19px, 2.2vw, 26px); line-height: 1.3; color: var(--ink-2); margin: 16px auto 0; max-width: 34ch; text-wrap: balance; letter-spacing: -.02em; }
-.hero .links { margin-top: 22px; }
-.hero-media { display: block; margin: 44px auto 0; width: min(1200px, 100%); border-radius: var(--r-lg); overflow: hidden; background: var(--bg-alt);
-  aspect-ratio: 4 / 3; }
-@media (min-width: 700px) { .hero-media { aspect-ratio: 16 / 8.5; } }
-.hero-media img { width: 100%; height: 100%; object-fit: cover; }
-.hero-stat { margin: 26px auto 0; display: grid; justify-items: center; gap: 2px; }
+/* ── kaydırmalı manşet ─────────────────── */
+.car { position: relative; --gap: 12px; --pad: max(16px, (100% - 1200px) / 2); }
+.car-track { display: grid; grid-auto-flow: column; grid-auto-columns: min(1200px, 100% - 32px); gap: var(--gap);
+  overflow-x: auto; overscroll-behavior-x: contain; scroll-snap-type: x mandatory; scroll-padding-inline: var(--pad);
+  padding-inline: var(--pad); scrollbar-width: none; -webkit-overflow-scrolling: touch; }
+.car-track::-webkit-scrollbar { display: none; }
+.slide { scroll-snap-align: start; scroll-snap-stop: always; border-radius: var(--r-lg); overflow: hidden; background: #1D1D1F;
+  position: relative; aspect-ratio: 4 / 5; isolation: isolate; }
+@media (min-width: 600px) { .slide { aspect-ratio: 4 / 3; } }
+@media (min-width: 900px) { .slide { aspect-ratio: 16 / 7.4; } }
+.slide-in { position: absolute; inset: 0; display: block; color: #fff; }
+.slide-img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; transform: scale(1.02);
+  transition: transform 1.2s var(--ease); }
+.slide.on .slide-img { transform: scale(1.07); transition-duration: 7s; }
+.slide-in:hover .slide-img { transform: scale(1.05); }
+.slide-scrim { position: absolute; inset: 0; background:
+  linear-gradient(to top, rgba(0,0,0,.86) 0%, rgba(0,0,0,.62) 32%, rgba(0,0,0,.18) 62%, rgba(0,0,0,0) 78%),
+  linear-gradient(to right, rgba(0,0,0,.28), rgba(0,0,0,0) 60%); }
+.slide-txt { position: absolute; left: 0; right: 0; bottom: 0; padding: 22px 20px 24px; display: grid; gap: 10px; justify-items: start; }
+@media (min-width: 900px) { .slide-txt { padding: 44px 56px 48px; max-width: 900px; gap: 14px; } }
+.slide-top { display: flex; flex-wrap: wrap; gap: 8px; }
+.chip { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 600; letter-spacing: .01em; padding: 6px 12px;
+  border-radius: 999px; background: color-mix(in srgb, var(--c) 82%, #000); color: #fff; }
+.stat-chip { background: rgba(255,255,255,.16); -webkit-backdrop-filter: blur(12px); backdrop-filter: blur(12px); font-weight: 500; }
+.stat-chip b { font-weight: 700; }
+.slide h2 { margin: 0; font-size: clamp(26px, 4.4vw, 54px); line-height: 1.06; letter-spacing: -.035em; font-weight: 700;
+  text-wrap: balance; text-shadow: 0 2px 24px rgba(0,0,0,.25); }
+.slide-dek { display: none; font-size: 19px; line-height: 1.4; color: rgba(255,255,255,.86); max-width: 62ch; letter-spacing: -.01em;
+  overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
+@media (max-width: 599px) { .slide-dek { display: none; } }
+.slide-meta { font-size: 14px; color: rgba(255,255,255,.72); }
+.slide-in:hover h2 { text-decoration: underline; text-decoration-thickness: 2px; text-underline-offset: 6px; }
+.slide-in:focus-visible { outline-offset: -4px; outline-color: #fff; }
+
+.car-ui { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding-top: 16px; }
+.car-dots { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
+.car-dots button { width: 10px; height: 10px; padding: 0; border: 0; border-radius: 99px; background: #C7C7CC; cursor: pointer; position: relative;
+  overflow: hidden; transition: width .4s var(--ease), background .3s; }
+.car-dots button[aria-current="true"] { width: 44px; background: #D2D2D7; }
+.car-dots button i { position: absolute; inset: 0; transform-origin: 0 50%; transform: scaleX(0); background: var(--ink); border-radius: inherit; }
+.car-dots button[aria-current="true"] i { transform: scaleX(1); }
+.car.playing .car-dots button[aria-current="true"] i { animation: fill var(--dur, 6.5s) linear both; }
+.car.paused .car-dots button[aria-current="true"] i { animation-play-state: paused; }
+@keyframes fill { from { transform: scaleX(0); } to { transform: scaleX(1); } }
+.car-ctrl { display: flex; gap: 10px; }
+.car-ctrl button { width: 40px; height: 40px; border-radius: 50%; border: 0; background: #E8E8ED; cursor: pointer; font-size: 20px;
+  display: grid; place-items: center; color: var(--ink); transition: background .2s; }
+.car-ctrl button:hover { background: #DCDCE1; }
+.car-play span { width: 10px; height: 12px; border-inline: 3px solid var(--ink); box-sizing: border-box; }
+.car-play[data-state="pause"] span { width: 0; height: 0; border: 0; border-left: 11px solid var(--ink);
+  border-top: 7px solid transparent; border-bottom: 7px solid transparent; margin-left: 3px; }
+@media (max-width: 599px) { .car-arr { display: none !important; } }
+
+/* ── kategori çipleri ve konular ───────── */
+.chips { display: flex; gap: 8px; overflow-x: auto; scrollbar-width: none; padding-block: 28px 4px; }
+@media (max-width: 899px) { .chips { width: 100%; padding-inline: 16px; } }
+@media (min-width: 900px) { .chips { flex-wrap: wrap; overflow: visible; } }
+.chips::-webkit-scrollbar { display: none; }
+.chip-link { flex: none; display: inline-flex; align-items: center; gap: 8px; padding: 9px 14px; border-radius: 999px; background: var(--bg-alt);
+  font-size: 15px; font-weight: 500; transition: background .2s; }
+.chip-link i { width: 8px; height: 8px; border-radius: 50%; background: var(--c); }
+.chip-link span { color: var(--muted); font-size: 13px; }
+.chip-link:hover { background: #E8E8ED; }
+.tags { display: flex; flex-wrap: wrap; gap: 10px; }
+.tags a { display: inline-flex; gap: 8px; align-items: baseline; padding: 10px 16px; border-radius: 999px; border: 1px solid var(--line); font-size: 16px; font-weight: 500; }
+.tags a span { color: var(--muted); font-size: 13px; }
+.tags a:hover { border-color: var(--ink); }
+.about-note { margin-top: 88px; padding: 32px; border-radius: var(--r-md); background: var(--bg-alt); }
+.about-note h2 { margin: 0 0 8px; font-size: 21px; letter-spacing: -.02em; }
+.about-note p { margin: 0; color: var(--ink-2); max-width: 80ch; }
+.about-note a { color: var(--link); }
 
 /* dev rakam */
@@ -101,35 +162,10 @@
 .stat-label { font-size: 19px; color: var(--muted); }
 
-/* ── karolar (2'li) ───────────────────── */
-.tiles { display: grid; gap: 12px; margin-top: 12px; padding-inline: 12px; }
-@media (min-width: 834px) { .tiles { grid-template-columns: 1fr 1fr; } }
-.tile { position: relative; background: var(--bg-alt); border-radius: var(--r-lg); overflow: hidden; text-align: center;
-  display: flex; flex-direction: column; min-height: 580px; isolation: isolate; }
-.tile-txt { padding: 52px 28px 0; display: grid; justify-items: center; gap: 8px; }
-.tile h2 { margin: 0; font-size: clamp(28px, 3.4vw, 40px); line-height: 1.08; letter-spacing: -.035em; font-weight: 700; max-width: 18ch; text-wrap: balance; }
-.tile p.dek { margin: 4px 0 0; font-size: 19px; color: var(--ink-2); max-width: 36ch; text-wrap: balance; }
-.tile .links { margin-top: 12px; }
-.tile .stat { font-size: clamp(56px, 7vw, 96px); margin-top: 6px; }
-.tile-media { margin-top: auto; padding-top: 28px; }
-.tile-media img { width: 100%; aspect-ratio: 4 / 3; object-fit: cover;
-  -webkit-mask-image: linear-gradient(to bottom, transparent 0, #000 16%); mask-image: linear-gradient(to bottom, transparent 0, #000 16%);
-  transition: transform .8s var(--ease); }
-.tile:hover .tile-media img { transform: scale(1.035); }
-.tile > a.cover { position: absolute; inset: 0; z-index: 1; }
-.tile .links, .tile .eyebrow { position: relative; z-index: 2; }
-.tile.wide { grid-column: 1 / -1; min-height: 0; }
-@media (min-width: 834px) {
-  .tile.wide { flex-direction: row; text-align: left; align-items: stretch; }
-  .tile.wide .tile-txt { justify-items: start; align-content: center; padding: 56px 20px 56px 64px; flex: 1 1 42%; }
-  .tile.wide .links { justify-content: flex-start; }
-  .tile.wide .tile-media { flex: 1 1 58%; padding: 0; }
-  .tile.wide .tile-media img { height: 100%; -webkit-mask-image: linear-gradient(to right, transparent 0, #000 14%); mask-image: linear-gradient(to right, transparent 0, #000 14%); }
-}
-
 /* ── bölüm başlığı ─────────────────────── */
-.sec { padding-block: 88px 0; }
+.sec { padding-block: 72px 0; }
 .sec-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; margin-bottom: 28px; }
 .sec-head h2 { margin: 0; font-size: clamp(30px, 4vw, 48px); letter-spacing: -.04em; line-height: 1.05; font-weight: 700; }
 .sec-head h2 span { color: var(--muted); }
+.sec-tools { display: flex; align-items: center; gap: 18px; }
 .arrows { display: flex; gap: 10px; }
 .arrows button { width: 40px; height: 40px; border-radius: 50%; border: 0; background: #E8E8ED; cursor: pointer; font-size: 20px;
@@ -157,21 +193,44 @@
 @media (min-width: 640px) { .grid { grid-template-columns: 1fr 1fr; } }
 @media (min-width: 1000px) { .grid { grid-template-columns: repeat(3, 1fr); } }
-.card { display: grid; gap: 12px; align-content: start; }
-.card .ph { border-radius: var(--r-md); overflow: hidden; background: var(--bg-alt); }
+.card { display: grid; gap: 10px; align-content: start; }
+.card .ph { display: block; border-radius: var(--r-md); overflow: hidden; background: var(--bg-alt); }
 .card img { aspect-ratio: 4 / 3; object-fit: cover; width: 100%; transition: transform .8s var(--ease); }
 .card:hover img { transform: scale(1.04); }
-.card h3 { margin: 0; font-size: 21px; line-height: 1.22; letter-spacing: -.025em; font-weight: 700; text-wrap: pretty; }
-.card:hover h3 { color: var(--link); }
+.card h2, .card h3 { margin: 0; font-size: 21px; line-height: 1.22; letter-spacing: -.025em; font-weight: 700; text-wrap: pretty; }
+.card h2 a:hover, .card h3 a:hover { color: var(--link); }
+.card-dek { margin: 0; font-size: 15px; line-height: 1.45; color: var(--ink-2); overflow: hidden;
+  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
 .card .t { font-size: 14px; color: var(--muted); }
+@media (max-width: 639px) {
+  .grid { gap: 0; }
+  .card { grid-template-columns: minmax(0, 1fr) 108px; grid-template-areas: "eb ph" "h ph" "t ph"; column-gap: 16px; row-gap: 6px;
+    padding-block: 18px; border-bottom: 1px solid #E8E8ED; align-content: start; }
+  .card:first-child { padding-top: 4px; }
+  .card .ph { grid-area: ph; align-self: start; border-radius: 14px; }
+  .card img { aspect-ratio: 1; }
+  .card .eyebrow { grid-area: eb; }
+  .card h2, .card h3 { grid-area: h; font-size: 18px; line-height: 1.25; }
+  .card-dek { display: none; }
+  .card .t { grid-area: t; font-size: 13px; }
+}
 
 .pager { display: flex; justify-content: center; align-items: center; gap: 20px; margin-top: 64px; font-size: 17px; }
 .pager a { color: var(--link); }
 
+/* ── konum (breadcrumb) ───────────────── */
+.crumbs { padding-top: 18px; font-size: 13px; color: var(--muted); }
+.crumbs ol { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 4px; }
+.crumbs li + li::before { content: "›"; margin-right: 6px; color: #AEAEB2; }
+.crumbs a:hover { color: var(--ink); text-decoration: underline; }
+.crumbs [aria-current] { color: var(--ink-2); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 46ch; display: inline-block; vertical-align: bottom; }
+.small { font-size: 15px !important; }
+@media (max-width: 599px) { .crumbs li:last-child { display: none; } }
+
 /* ── haber sayfası (Newsroom tarzı) ────── */
 .progress { position: fixed; top: 0; left: 0; right: 0; height: 3px; z-index: 60; background: var(--grad); transform-origin: 0 50%; transform: scaleX(0); }
-.art-head { padding-block: 56px 0; }
+.art-head { padding-block: 28px 0; }
 .art-head .meta-top { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 14px; font-size: 14px; font-weight: 600; }
 .art-head .meta-top .eyebrow { font-size: 14px; text-transform: uppercase; letter-spacing: .04em; }
-.art-head .meta-top time { color: var(--muted); font-weight: 400; }
+.art-head .meta-top time, .art-head .meta-top .muted { color: var(--muted); font-weight: 400; }
 .art-head h1 { margin: 14px 0 0; font-size: clamp(32px, 5vw, 56px); line-height: 1.07; letter-spacing: -.04em; font-weight: 700; text-wrap: balance; }
 .art-head .dek { margin: 18px 0 0; font-size: clamp(19px, 2vw, 24px); line-height: 1.35; color: var(--ink-2); letter-spacing: -.02em; text-wrap: pretty; }
@@ -189,8 +248,12 @@
 .art-body p { margin: 0 0 1.15em; }
 .art-body a { color: var(--link); text-decoration: underline; text-underline-offset: 3px; }
+.art-body h2 { font-size: 26px; line-height: 1.2; letter-spacing: -.03em; margin: 1.6em 0 .5em; }
 .art-body ul, .art-body ol { padding-left: 1.2em; margin: 0 0 1.15em; }
 .why { margin: 36px 0; padding: 30px 32px; border-radius: var(--r-md); background: var(--bg-alt); }
 .why strong { display: block; font-size: 14px; font-weight: 600; color: color-mix(in srgb, var(--c) 78%, #000); letter-spacing: .02em; }
 .why p { margin: 8px 0 0; font-size: 21px; line-height: 1.4; letter-spacing: -.02em; font-weight: 600; text-wrap: pretty; }
+.art-tags { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-top: 32px; font-size: 14px; }
+.art-tags a { padding: 7px 14px; border-radius: 999px; background: var(--bg-alt); font-weight: 500; }
+.art-tags a:hover { background: #E8E8ED; }
 .sources { margin-top: 40px; border-top: 1px solid var(--line); padding-top: 24px; }
 .sources h2 { margin: 0 0 8px; font-size: 14px; font-weight: 600; color: var(--muted); }
@@ -205,7 +268,7 @@
 
 /* ── kategori & sayfa başlıkları ───────── */
-.page-head { text-align: center; padding-block: 72px 48px; }
-.page-head h1 { margin: 8px 0 0; font-size: clamp(40px, 7vw, 80px); letter-spacing: -.045em; line-height: 1; font-weight: 700; }
-.page-head p { margin: 14px 0 0; font-size: 21px; color: var(--ink-2); }
+.page-head { text-align: center; padding-block: 48px 40px; }
+.page-head h1 { margin: 8px auto 0; font-size: clamp(36px, 5.6vw, 68px); letter-spacing: -.045em; line-height: 1.02; font-weight: 700; max-width: 16ch; text-wrap: balance; }
+.page-head p { margin: 14px auto 0; font-size: 21px; color: var(--ink-2); max-width: 56ch; text-wrap: balance; }
 .empty { text-align: center; padding: 120px 16px; }
 .empty h1 { font-size: clamp(36px, 6vw, 64px); letter-spacing: -.04em; margin: 0; }
@@ -223,4 +286,5 @@
 .foot-cats { display: flex; flex-wrap: wrap; gap: 8px 20px; padding-block: 14px; border-block: 1px solid var(--line); }
 .foot-cats a { color: var(--ink-2); }
+.foot-tags { border-top: 0; padding-top: 0; }
 .foot-cats a:hover, .foot a:hover { text-decoration: underline; }
 .foot p { margin: 0; }
@@ -232,10 +296,10 @@
   @supports (animation-timeline: view()) {
     .reveal { animation: reveal linear both; animation-timeline: view(); animation-range: entry 0% cover 22%; }
-    .hero-media, .art-media .ph { animation: settle linear both; animation-timeline: view(); animation-range: entry 0% cover 45%; }
+    .art-media .ph { animation: settle linear both; animation-timeline: view(); animation-range: entry 0% cover 45%; }
     .progress { animation: grow-x linear both; animation-timeline: scroll(root); }
   }
-  .hero > *:not(.hero-media) { animation: rise .9s var(--ease) both; }
-  .hero > *:nth-child(2) { animation-delay: .06s; } .hero > *:nth-child(3) { animation-delay: .12s; }
-  .hero > *:nth-child(4) { animation-delay: .18s; } .hero > *:nth-child(5) { animation-delay: .26s; }
+  .slide.on .slide-txt > * { animation: rise .8s var(--ease) both; }
+  .slide.on .slide-txt > *:nth-child(2) { animation-delay: .06s; } .slide.on .slide-txt > *:nth-child(3) { animation-delay: .12s; }
+  .slide.on .slide-txt > *:nth-child(4) { animation-delay: .18s; }
 }
 @keyframes reveal { from { opacity: 0; transform: translateY(48px); } to { opacity: 1; transform: none; } }
@@ -243,3 +307,3 @@
 @keyframes rise { from { opacity: 0; transform: translateY(18px); } to { opacity: 1; transform: none; } }
 @keyframes grow-x { to { transform: scaleX(1); } }
-@media (prefers-reduced-motion: reduce) { .dot { animation: none; } * { transition: none !important; } }
+@media (prefers-reduced-motion: reduce) { .dot { animation: none; } * { transition: none !important; } .slide.on .slide-img { transform: none; } }
@@@YZ@@@ PATCH static/site.js
--- a/static/site.js
+++ b/static/site.js
@@ -43,4 +43,79 @@
   });
 
+  // Kaydırmalı manşet: parmakla kaydırılır, kendiliğinden ilerler, üzerine gelince/dokununca durur
+  document.querySelectorAll(".car").forEach(function (car) {
+    var track = car.querySelector(".car-track");
+    var slides = Array.prototype.slice.call(car.querySelectorAll(".slide"));
+    var dots = Array.prototype.slice.call(car.querySelectorAll(".car-dots button"));
+    var play = car.querySelector(".car-play");
+    if (!track || slides.length < 2) { if (slides[0]) slides[0].classList.add("on"); return; }
+    var dur = +car.getAttribute("data-interval") || 6500;
+    car.style.setProperty("--dur", dur + "ms");
+    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
+    var cur = 0, timer = null, userStopped = reduce, hover = false, visible = true, settleT = null;
+
+    function setCur(i) {
+      if (i === cur && slides[i].classList.contains("on")) return;
+      cur = i;
+      slides.forEach(function (s, k) { s.classList.toggle("on", k === i); s.setAttribute("aria-hidden", k === i ? "false" : "true");
+        s.querySelector("a").tabIndex = k === i ? 0 : -1; });
+      dots.forEach(function (d, k) {
+        if (k === i) { d.setAttribute("aria-current", "true"); var bar = d.firstElementChild; if (bar) { bar.style.animation = "none"; void bar.offsetWidth; bar.style.animation = ""; } }
+        else d.removeAttribute("aria-current");
+      });
+    }
+    function go(i, smooth) {
+      i = (i + slides.length) % slides.length;
+      var x = slides[i].offsetLeft - slides[0].offsetLeft;
+      track.scrollTo({ left: x, behavior: smooth === false || reduce ? "auto" : "smooth" });
+      setCur(i);
+      schedule();
+    }
+    function running() { return !userStopped && !hover && visible && !document.hidden; }
+    function schedule() {
+      clearTimeout(timer);
+      car.classList.toggle("playing", !userStopped);
+      car.classList.toggle("paused", !running());
+      if (running()) timer = setTimeout(function () { go(cur + 1); }, dur);
+    }
+    // kullanıcı kaydırınca hangi karede olduğumuzu bul
+    track.addEventListener("scroll", function () {
+      clearTimeout(settleT);
+      settleT = setTimeout(function () {
+        var mid = track.scrollLeft + track.clientWidth / 2, best = 0, bd = 1e9;
+        slides.forEach(function (s, k) { var c = s.offsetLeft - slides[0].offsetLeft + s.clientWidth / 2 + parseFloat(getComputedStyle(track).paddingLeft);
+          var d = Math.abs(c - mid); if (d < bd) { bd = d; best = k; } });
+        if (best !== cur) { setCur(best); schedule(); }
+      }, 90);
+    }, { passive: true });
+    dots.forEach(function (d, k) { d.addEventListener("click", function () { go(k); }); });
+    car.querySelectorAll(".car-arr").forEach(function (b) {
+      b.addEventListener("click", function () { go(cur + (+b.getAttribute("data-dir"))); });
+    });
+    if (play) play.addEventListener("click", function () {
+      userStopped = !userStopped;
+      play.setAttribute("data-state", userStopped ? "pause" : "play");
+      play.setAttribute("aria-label", userStopped ? "Otomatik geçişi başlat" : "Otomatik geçişi durdur");
+      schedule();
+    });
+    if (reduce && play) { play.setAttribute("data-state", "pause"); play.setAttribute("aria-label", "Otomatik geçişi başlat"); }
+    car.addEventListener("mouseenter", function () { hover = true; schedule(); });
+    car.addEventListener("mouseleave", function () { hover = false; schedule(); });
+    car.addEventListener("focusin", function () { hover = true; schedule(); });
+    car.addEventListener("focusout", function () { hover = false; schedule(); });
+    track.addEventListener("pointerdown", function (e) { if (e.pointerType !== "mouse") { hover = true; schedule(); } }, { passive: true });
+    track.addEventListener("touchend", function () { setTimeout(function () { hover = false; schedule(); }, 2500); }, { passive: true });
+    car.addEventListener("keydown", function (e) {
+      if (e.key === "ArrowRight") { e.preventDefault(); go(cur + 1); }
+      else if (e.key === "ArrowLeft") { e.preventDefault(); go(cur - 1); }
+    });
+    document.addEventListener("visibilitychange", schedule);
+    if ("IntersectionObserver" in window) {
+      new IntersectionObserver(function (en) { visible = en[0].isIntersecting; schedule(); }, { threshold: 0.35 }).observe(car);
+    }
+    setCur(0);
+    schedule();
+  });
+
   // Menü: bir bağlantıya basınca kapansın
   document.querySelectorAll(".menu-panel a").forEach(function (a) {
@@@YZ@@@ SHA
be2ad673d28da4d66f1fa7f7af1ac4f7472b6f43981f971f8eb5b23e6c671750 haberbot/config.py
abb8295c05cd66b5782f7b699f5eefa989a71bc126f5a894b49dd09a27931a5f haberbot/site.py
b68b107c31d3a75801cd08eeccc8497262d0d98ed87494e95472b997b3e7bfcd haberbot/app.py
accf78faf7f5729d7a32e31919c6f2e4c54e3d8e5f3c2c503561aa0fd0146d64 haberbot/prompts.py
bec3124ea9dc19ee83eee5752c8fdd37914b58f3fbb882f5e3995cb1ae2015ff haberbot/llm.py
24948f41983de10235d4d7fd9c1881e95b4148f2edbe37a88bfa75d1fc5fb9f5 config.yaml
f45058d1428458559bcaab7c05bb9fbf0eda39650483f21c98a75e183e9a5073 templates/base.html
8b66d03576e31b69df19c466a3d8afedb4cdef74007e33f6de7a653e31ac82dd templates/index.html
debed2c036fac1389b684bb2121642c0069ac215ea56a74eed18a172af5f895a templates/_macros.html
515d4acd8a3b871b6291336513cf778e880ec0c1af8dc0264a8401ba23efb62b templates/article.html
bab58410dd21be48caef13d4c8a607ca596ed87bd594a7ad929cd3feb80edace templates/category.html
e42fcc7c3af74f32ab9097f0cfa2d23dfd94c8bb1fc055209e6fb2968e7e5691 templates/archive.html
04ae5cf3c61afb231b3a7b5df65cef1a1945a0e95627a494f917a9a2c98cb182 templates/tag.html
8795a601ec2fac5f5237325be9884a3d39703c2525cb7837bfa80587ca6ed129 templates/about.html
e8f3413bc2cea9f5af1f3a92bf946dd7e329af22a7c59b029da06a02a0407cdd templates/sitemap.xml
a5815369d0afcdf71bdf57715a042ad3c120fb673ae34c8bd02afdb79d1dc4df templates/news-sitemap.xml
b6c33575dea25d7268b94f12ddde097148d832e131c0296d78af977269d86093 static/style.css
9d7f4a67c6f55dd915a3d24e8daa711a8296d492898abf5fd610a7f8734d4469 static/site.js
