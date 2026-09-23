YZRADAR-BUNDLE v1 part 2/3
-- body: Markdown, 3–5 short paragraphs, 150–320 words total, no headings, no bullet lists unless listing 3+ concrete items. The LAST paragraph must start with "**Neden önemli?** " followed by 1–2 grounded sentences (no speculation beyond what sources support). Do not include a sources list; the site adds it.
+- title: the H1. ≤90 characters, informative and specific (who did what), starts with or contains the focus_keyword. Sentence case (only first word and proper nouns capitalized). No trailing period, no clickbait.
+- summary: 1–2 sentences, ≤220 characters, the core news (shown under the headline).
+- body: Markdown, 250–450 words. Structure: a 2–3 sentence lead paragraph that answers who/what/when and contains the focus_keyword; then 2 or 3 sections, each starting with a "## " subheading (short, informative, natural search-style phrase such as "## GPT-6 Sol neler sunuyor?" or "## Fiyat ve erişim"), each followed by 1–2 short paragraphs. Use a bullet list only for 3+ concrete items from the sources. Bold at most 2 key terms. The LAST paragraph (not under a new heading) must start with "**Neden önemli?** " followed by 1–2 grounded sentences (no speculation beyond what sources support). Do not include a sources list or links; the site adds them. If the sources are thin, write fewer, shorter sections rather than padding — accuracy beats length.
 - category: one of the allowed keys.
-- tags: 3–5 short tags (proper nouns or Turkish terms).
+- tags: 3–6 tags that people search for: companies, products, models, technologies, places (e.g. "OpenAI", "GPT-6", "Nvidia", "Avrupa Birliği", "büyük dil modelleri"). Use the official spelling consistently. Never use generic words like "yapay zeka", "teknoloji", "haber", and never use the names of news outlets (TechCrunch, The Verge…).
+- focus_keyword: as described above.
+- seo_title: ≤58 characters, the title shown in Google results. Starts with the focus_keyword or puts it near the start; specific and compelling but not clickbait; may differ from title. No site name, no trailing period.
+- meta_description: 140–156 characters, one or two sentences in active voice that contain the focus_keyword and tell the reader exactly what they will learn. No quotes, no emojis.
+- slug: URL slug in lowercase ASCII (convert ç→c, ğ→g, ı→i, ö→o, ş→s, ü→u), words separated by hyphens, 3–7 words, ≤60 characters, based on the focus_keyword plus the key action (e.g. "openai-gpt-6-sol-ve-luna-modellerini-duyurdu"). No stop-word padding, no dates.
+- image_alt: ≤120 characters Turkish alt text for the cover image: briefly describe the visual metaphor from visual_scene and relate it to the news topic (e.g. "Buzlu cam küplerden yükselen grafik: Enveda'nın 311 milyon dolarlık yatırımını temsil eden görsel").
 - confidence: "yuksek" if facts are clear and come from an official/primary source or several reputable reports; "orta" if a single secondary report with clear facts; "dusuk" if thin or ambiguous.
 - flags (zero or more): iddia = based on unconfirmed reports, anonymous sources or rumors; hassas = death, violence, military, elections, allegations against individuals, medical/health claims, minors; yetersiz_bilgi = source text too thin to write reliably; celiski = sources conflict; eski = not actually new; tanitim = primarily promotional/sponsored/event marketing.
@@ -170,2 +186,38 @@
         ]
     return "\n".join(parts)
+
+
+# ── 3) Yayınlanmış haberler için SEO bilgisi (metni değiştirmeden) ──
+SEO_SCHEMA = {
+    "type": "object",
+    "properties": {
+        "focus_keyword": {"type": "string"},
+        "seo_title": {"type": "string"},
+        "meta_description": {"type": "string"},
+        "image_alt": {"type": "string"},
+        "tags": {"type": "array", "items": {"type": "string"}},
+    },
+    "required": ["focus_keyword", "seo_title", "meta_description", "image_alt", "tags"],
+    "additionalProperties": False,
+}
+
+
+def seo_system(site_name: str) -> str:
+    return f"""You are the SEO editor of "{site_name}", a Turkish-language AI news site. You receive an already published Turkish article.
+Do NOT change the article. Produce search metadata in natural Türkiye Türkçesi that is faithful to the article — never add facts that are not in it.
+- focus_keyword: the 2–4 word Turkish phrase a reader would most likely type into Google to find this news, built around the main entity.
+- seo_title: ≤58 characters, starts with or contains the focus_keyword near the start, specific, no clickbait, no site name, no trailing period.
+- meta_description: 140–156 characters, active voice, contains the focus_keyword, tells the reader what they will learn. No quotes, no emojis.
+- image_alt: ≤120 characters, describes the cover image (described in VISUAL) and relates it to the news topic.
+- tags: 3–6 searchable entities (companies, products, models, technologies, places) with official spelling. Never generic words like "yapay zeka", "teknoloji", and never news outlet names."""
+
+
+def seo_user(post: dict) -> str:
+    return "\n".join([
+        f"TITLE: {post.get('title', '')}",
+        f"SUMMARY: {post.get('summary', '')}",
+        f"CURRENT TAGS: {', '.join(post.get('tags') or [])}",
+        f"VISUAL: {post.get('visual_scene', '')}",
+        "BODY:",
+        post.get("body", ""),
+    ])
@@@YZ@@@ PATCH haberbot/llm.py
--- a/haberbot/llm.py
+++ b/haberbot/llm.py
@@ -313,4 +313,10 @@
         if "stories" in schema.get("properties", {}):
             return self._triage(user)
+        if "body" not in schema.get("properties", {}):  # yalnızca SEO bilgisi
+            t = re.search(r"TITLE: (.+)", user)
+            t = t.group(1) if t else "Haber"
+            return {"focus_keyword": " ".join(t.split()[:3]), "seo_title": t[:58],
+                    "meta_description": (t + ". Gelişmenin ayrıntıları, kaynağıyla ve Türkçe olarak YZ Radar'da.")[:156],
+                    "image_alt": f"{t[:80]} haberini temsil eden 3D görsel", "tags": ["OpenAI", "Test"]}
         return self._write(user)
 
@@ -364,3 +370,8 @@
             "visual_style": "studio",
             "visual_scene": "a smooth sculptural object on a pastel backdrop",
+            "focus_keyword": " ".join(title.split()[:3]),
+            "seo_title": title[:58],
+            "meta_description": (f"{title}. {credit} kaynaklı gelişmenin ayrıntıları, kaynağıyla ve Türkçe olarak.")[:156],
+            "slug": "",
+            "image_alt": f"{title[:80]} haberini temsil eden 3D görsel",
         }
@@@YZ@@@ PATCH config.yaml
--- a/config.yaml
+++ b/config.yaml
@@ -15,4 +15,16 @@
   contact_email: ""        # Hakkında sayfasında görünür (boş bırakılabilir)
   instagram: ""            # Örn: "yzradar" (2. aşamada kullanılacak)
+
+seo:
+  # Ana sayfanın Google'da görünen başlığı ve açıklaması
+  home_title: "Yapay Zeka Haberleri: Güncel YZ Gelişmeleri"
+  home_description: "ChatGPT, Gemini, Claude ve dünyadaki tüm yapay zeka gelişmeleri. Kaynağıyla, Türkçe ve her gün güncel yapay zeka haberleri."
+  # Arama motoru doğrulama kodları (Search Console / Bing / Yandex'in verdiği "content" değeri)
+  google_site_verification: ""
+  bing_site_verification: ""
+  yandex_verification: ""
+  # Yeni haberleri Bing ve Yandex'e anında bildir (ücretsiz, hesap gerekmez)
+  indexnow: true
+  featured_count: 5        # Ana sayfadaki kaydırmalı manşette kaç haber olsun
 
 schedule:
@@@YZ@@@ PATCH templates/base.html
--- a/templates/base.html
+++ b/templates/base.html
@@ -4,19 +4,31 @@
 <meta charset="utf-8">
 <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
-<title>{% block title %}{{ site.name }} — {{ site.tagline }}{% endblock %}</title>
-<meta name="description" content="{% block description %}{{ site.description }}{% endblock %}">
+<title>{% block title %}{{ site.home_title }} | {{ site.name }}{% endblock %}</title>
+<meta name="description" content="{% block description %}{{ site.home_description }}{% endblock %}">
 <link rel="canonical" href="{{ canonical }}">
+{% if noindex|default(false) %}
+<meta name="robots" content="noindex, follow">
+{% else %}
+<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
+{% endif %}
+{% if site.verify.google_site_verification %}<meta name="google-site-verification" content="{{ site.verify.google_site_verification }}">{% endif %}
+{% if site.verify.bing_site_verification %}<meta name="msvalidate.01" content="{{ site.verify.bing_site_verification }}">{% endif %}
+{% if site.verify.yandex_verification %}<meta name="yandex-verification" content="{{ site.verify.yandex_verification }}">{% endif %}
 <meta property="og:site_name" content="{{ site.name }}">
 <meta property="og:locale" content="tr_TR">
 {% block og %}
 <meta property="og:type" content="website">
-<meta property="og:title" content="{{ site.name }} — {{ site.tagline }}">
-<meta property="og:description" content="{{ site.description }}">
+<meta property="og:title" content="{{ self.title() }}">
+<meta property="og:description" content="{{ self.description() }}">
 <meta property="og:url" content="{{ canonical }}">
 <meta property="og:image" content="{{ site.og_image }}">
+<meta name="twitter:image" content="{{ site.og_image }}">
 {% endblock %}
 <meta name="twitter:card" content="summary_large_image">
-<link rel="alternate" type="application/rss+xml" title="{{ site.name }}" href="{{ site.base }}/feed.xml">
+<meta name="twitter:title" content="{{ self.title() }}">
+<meta name="twitter:description" content="{{ self.description() }}">
+<link rel="alternate" type="application/rss+xml" title="{{ site.name }}: yapay zeka haberleri" href="{{ site.url }}/feed.xml">
 <link rel="icon" href="{{ site.base }}/static/favicon.svg" type="image/svg+xml">
+<link rel="apple-touch-icon" href="{{ site.base }}/static/apple-touch-icon.png">
 <meta name="theme-color" content="#FFFFFF">
 <link rel="preconnect" href="https://fonts.googleapis.com">
@@ -58,8 +70,13 @@
   <div class="wrap foot-in">
     <a class="brand" href="{{ site.base }}/"><span class="mark" aria-hidden="true"></span>{{ site.name }}</a>
-    <p>{{ site.tagline }} Her haberde orijinal kaynak adıyla ve bağlantısıyla belirtilir. Haberler kaynaklardan yapay zeka yardımıyla Türkçe derlenir. Görseller yapay zeka ile üretilmiş temsili görsellerdir.</p>
+    <p>{{ site.name }}, dünyadaki yapay zeka gelişmelerini Türkçe ve kaynağıyla aktaran bir haber sitesidir. Her haberde orijinal kaynak adıyla ve bağlantısıyla belirtilir. Haberler kaynaklardan yapay zeka yardımıyla derlenir ve editör denetiminden geçer. Görseller temsilidir.</p>
     <div class="foot-cats">
       {% for c in site.categories %}<a href="{{ c.url }}">{{ c.label }}</a>{% endfor %}
     </div>
+    {% if site.top_tags %}
+    <div class="foot-cats foot-tags" aria-label="Popüler konular">
+      {% for t in site.top_tags %}<a href="{{ t.url }}">{{ t.label }}</a>{% endfor %}
+    </div>
+    {% endif %}
     <p>© {{ site.year }} {{ site.name }} · <a href="{{ site.base }}/hakkinda/">Hakkında ve yayın ilkeleri</a> · <a href="{{ site.base }}/feed.xml">RSS</a>{% if site.instagram %} · <a href="https://instagram.com/{{ site.instagram }}" rel="noopener" target="_blank">Instagram</a>{% endif %}</p>
   </div>
@@@YZ@@@ FILE templates/index.html
{% extends "base.html" %}
{% from "_macros.html" import card, slide, rail %}

{% block head %}
{% if featured %}<link rel="preload" as="image" href="{{ featured[0].img }}" fetchpriority="high">{% endif %}
<script type="application/ld+json">{{ {
  "@context": "https://schema.org",
  "@graph": [
    {"@type": "WebSite", "@id": site.url ~ "/#website", "name": site.name, "alternateName": "YZ Radar yapay zeka haberleri",
     "url": site.url ~ "/", "inLanguage": "tr-TR", "description": site.home_description,
     "publisher": {"@id": site.url ~ "/#org"}},
    {"@type": "NewsMediaOrganization", "@id": site.url ~ "/#org", "name": site.name, "url": site.url ~ "/",
     "logo": {"@type": "ImageObject", "url": site.logo, "width": 512, "height": 512},
     "publishingPrinciples": site.url ~ "/hakkinda/"}
  ]
}|tojson }}</script>
{% endblock %}

{% block main %}
<header class="home-head wrap">
  <h1>Yapay zeka haberleri</h1>
  {% if featured %}
  <p class="live" role="status"><span class="dot" aria-hidden="true"></span>Canlı · Son güncelleme <b><time datetime="{{ site.built_iso }}" data-rel>{{ site.built }}</time></b>{% if site.today_count %} · Bugün <b>{{ site.today_count }}</b> gelişme{% endif %}</p>
  {% endif %}
</header>

{% if not featured %}
  <section class="empty">
    <p>{{ site.name }} yayına hazırlanıyor. {{ site.tagline }}</p>
  </section>
{% else %}
  <section class="car" aria-roledescription="carousel" aria-label="Öne çıkan yapay zeka haberleri" data-interval="6500">
    <div class="car-track" id="car-track">
      {% for p in featured %}{{ slide(p, loop.index, loop.length) }}{% endfor %}
    </div>
    {% if featured|length > 1 %}
    <div class="car-ui wrap">
      <div class="car-dots">
        {% for p in featured %}
        <button type="button" data-go="{{ loop.index0 }}" aria-label="{{ loop.index }}. manşet: {{ p.short_title or p.title }}"{% if loop.first %} aria-current="true"{% endif %}><i></i></button>
        {% endfor %}
      </div>
      <div class="car-ctrl">
        <button type="button" class="car-play" aria-label="Otomatik geçişi durdur" data-state="play"><span aria-hidden="true"></span></button>
        <button type="button" class="car-arr" data-dir="-1" aria-label="Önceki manşet">‹</button>
        <button type="button" class="car-arr" data-dir="1" aria-label="Sonraki manşet">›</button>
      </div>
    </div>
    {% endif %}
  </section>

  <nav class="chips wrap" aria-label="Kategoriler">
    {% for c in site.categories if c.count %}
    <a class="chip-link" href="{{ c.url }}" style="--c:{{ c.color }}"><i aria-hidden="true"></i>{{ c.label }}<span>{{ c.count }}</span></a>
    {% endfor %}
  </nav>

  <section class="sec wrap" aria-labelledby="h-son">
    <div class="sec-head"><h2 id="h-son">Son gelişmeler.</h2></div>
    <div class="grid">{% for p in latest %}{{ card(p) }}{% endfor %}</div>
    {% if next_url %}
    <nav class="pager" aria-label="Sayfalar"><a class="more" href="{{ next_url }}">Daha eski haberler</a></nav>
    {% endif %}
  </section>

  {% for r in rails %}
    {{ rail(r.posts, r.cat.seo_title ~ '.', 'k-' ~ r.cat.slug, '', r.cat.url) }}
  {% endfor %}

  {% if tags %}
  <section class="sec wrap" aria-labelledby="h-konu">
    <div class="sec-head"><h2 id="h-konu">Popüler konular.</h2></div>
    <div class="tags">{% for t in tags %}<a href="{{ t.url }}">{{ t.label }}<span>{{ t.count }}</span></a>{% endfor %}</div>
  </section>
  {% endif %}

  <section class="about-note wrap" aria-labelledby="h-hakkinda">
    <h2 id="h-hakkinda">{{ site.name }} nedir?</h2>
    <p>{{ site.name }}, dünyadaki yapay zeka gelişmelerini Türkçe olarak takip eden bir haber sitesidir. OpenAI, Google, Anthropic, NVIDIA ve Hugging Face gibi şirketlerin resmi duyurularını ve saygın teknoloji yayınlarını her saat tarar. ChatGPT, Gemini ve Claude gibi yapay zeka modellerindeki yenilikleri, yatırımları, araştırmaları ve regülasyon haberlerini sade bir dille, her zaman orijinal kaynağıyla aktarır. <a href="{{ site.base }}/hakkinda/">Yayın ilkelerimiz</a></p>
  </section>
{% endif %}
{% endblock %}
@@@YZ@@@ FILE templates/_macros.html
{% macro img(p, cls='', eager=false, sizes='(min-width: 1000px) 400px, 100vw', priority=false) %}
<img src="{{ p.img }}" alt="{{ p.img_alt }}" width="1280" height="960"{% if not eager %} loading="lazy"{% endif %}{% if priority %} fetchpriority="high"{% endif %} decoding="async" class="{{ cls }}" style="view-transition-name: v{{ p.id }}">
{% endmacro %}

{% macro card(p, dek=true, heading='h3') %}
<article class="card reveal" style="--c:{{ p.cat_color }}">
  <a class="ph" href="{{ p.url }}" tabindex="-1" aria-hidden="true">{{ img(p) }}</a>
  <a class="eyebrow sm" href="{{ p.cat_url }}">{{ p.cat_label }}</a>
  <{{ heading }}><a href="{{ p.url }}">{{ p.title_disp }}</a></{{ heading }}>
  {% if dek %}<p class="card-dek">{{ p.summary }}</p>{% endif %}
  <span class="t"><time datetime="{{ p.iso }}" data-rel>{{ p.date_str }}</time> · {{ p.credits|join(', ') }}</span>
</article>
{% endmacro %}

{% macro rcard(p) %}
<a class="rcard" href="{{ p.url }}" style="--c:{{ p.cat_color }}">
  {{ img(p) }}
  <div class="rcard-body">
    <span class="eyebrow sm">{{ p.kicker_disp }}</span>
    <h3>{{ p.title_disp }}</h3>
    <span class="t"><time datetime="{{ p.iso }}" data-rel>{{ p.date_str }}</time> · {{ p.credits|join(', ') }}</span>
  </div>
</a>
{% endmacro %}

{% macro slide(p, i, n) %}
<article class="slide" role="group" aria-roledescription="slayt" aria-label="{{ i }} / {{ n }}" style="--c:{{ p.cat_color }}" data-i="{{ i - 1 }}">
  <a class="slide-in" href="{{ p.url }}">
    {{ img(p, 'slide-img', eager=(i == 1), sizes='(min-width: 1232px) 1200px, 100vw', priority=(i == 1)) }}
    <span class="slide-scrim" aria-hidden="true"></span>
    <span class="slide-txt">
      <span class="slide-top">
        <span class="chip">{{ p.kicker_disp }}</span>
        {% if p.hero_stat %}<span class="chip stat-chip"><b>{{ p.hero_stat }}</b>{% if p.hero_stat_label %} {{ p.hero_stat_label }}{% endif %}</span>{% endif %}
      </span>
      <h2>{{ p.title_disp }}</h2>
      <span class="slide-dek">{{ p.summary }}</span>
      <span class="slide-meta"><time datetime="{{ p.iso }}" data-rel>{{ p.date_str }}</time> · Kaynak: {{ p.credits|join(', ') }}</span>
    </span>
  </a>
</article>
{% endmacro %}

{% macro rail(posts, title, id, muted_title='', more_url='') %}
<section class="sec{{ ' bg-alt' if id == 'son' }}" aria-labelledby="h-{{ id }}">
  <div class="wrap sec-head">
    <h2 id="h-{{ id }}">{{ title }}{% if muted_title %} <span>{{ muted_title }}</span>{% endif %}</h2>
    <div class="sec-tools">
      {% if more_url %}<a class="more" href="{{ more_url }}">Tümü</a>{% endif %}
      <div class="arrows" data-rail="r-{{ id }}">
        <button type="button" data-dir="-1" aria-label="Önceki">‹</button>
        <button type="button" data-dir="1" aria-label="Sonraki">›</button>
      </div>
    </div>
  </div>
  <div class="rail" id="r-{{ id }}">
    {% for p in posts %}{{ rcard(p) }}{% endfor %}
  </div>
</section>
{% endmacro %}

{% macro crumbs(items) %}
{# items: [(ad, göreli_url, mutlak_url), ...] #}
<nav class="crumbs wrap" aria-label="Konum">
  <ol>
    {% for it in items %}
    <li>{% if not loop.last %}<a href="{{ it[1] }}">{{ it[0] }}</a>{% else %}<span aria-current="page">{{ it[0] }}</span>{% endif %}</li>
    {% endfor %}
  </ol>
</nav>
{% set ns = namespace(els=[]) %}
{% for it in items %}{% set ns.els = ns.els + [{"@type": "ListItem", "position": loop.index, "name": it[0], "item": it[2]}] %}{% endfor %}
<script type="application/ld+json">{{ {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": ns.els}|tojson }}</script>
{% endmacro %}
@@@YZ@@@ PATCH templates/article.html
--- a/templates/article.html
+++ b/templates/article.html
@@ -1,24 +1,38 @@
 {% extends "base.html" %}
-{% from "_macros.html" import rail, img %}
+{% from "_macros.html" import rail, img, crumbs %}
 {% set active_cat = post.category %}
-{% block title %}{{ post.title }} — {{ site.name }}{% endblock %}
-{% block description %}{{ post.summary }}{% endblock %}
+{% block title %}{{ post.seo_title }} | {{ site.name }}{% endblock %}
+{% block description %}{{ post.meta_description }}{% endblock %}
 {% block og %}
 <meta property="og:type" content="article">
 <meta property="og:title" content="{{ post.title }}">
-<meta property="og:description" content="{{ post.summary }}">
+<meta property="og:description" content="{{ post.meta_description }}">
 <meta property="og:url" content="{{ post.abs_url }}">
 <meta property="og:image" content="{{ post.abs_og }}">
 <meta property="og:image:width" content="1200">
 <meta property="og:image:height" content="630">
+<meta property="og:image:alt" content="{{ post.img_alt }}">
+<meta name="twitter:image" content="{{ post.abs_og }}">
 <meta property="article:published_time" content="{{ post.iso }}">
+<meta property="article:modified_time" content="{{ post.mod_iso }}">
 <meta property="article:section" content="{{ post.cat_label }}">
+{% for t in post.tag_list %}<meta property="article:tag" content="{{ t.label }}">
+{% endfor %}
 {% endblock %}
 {% block head %}
+<link rel="preload" as="image" href="{{ post.img }}" fetchpriority="high">
 <script type="application/ld+json">{{ {
   "@context": "https://schema.org", "@type": "NewsArticle",
-  "headline": post.title, "description": post.summary, "image": [post.abs_og, post.abs_img],
-  "datePublished": post.iso, "inLanguage": "tr", "mainEntityOfPage": post.abs_url,
-  "publisher": {"@type": "Organization", "name": site.name},
+  "mainEntityOfPage": {"@type": "WebPage", "@id": post.abs_url},
+  "headline": post.title[:110], "alternativeHeadline": post.seo_title,
+  "description": post.meta_description,
+  "image": [post.abs_og, post.abs_img],
+  "datePublished": post.iso, "dateModified": post.mod_iso,
+  "inLanguage": "tr-TR", "articleSection": post.cat_label,
+  "keywords": post.tag_list|map(attribute='label')|list,
+  "wordCount": post.words, "isAccessibleForFree": true,
+  "author": {"@type": "Organization", "name": site.name ~ " Haber Masası", "url": site.url ~ "/hakkinda/"},
+  "publisher": {"@type": "NewsMediaOrganization", "@id": site.url ~ "/#org", "name": site.name,
+                "logo": {"@type": "ImageObject", "url": site.logo, "width": 512, "height": 512}},
   "isBasedOn": post.sources|map(attribute='url')|list
 }|tojson }}</script>
@@ -27,4 +41,5 @@
 
 {% block main %}
+{{ crumbs([("Ana sayfa", site.base ~ "/", site.url ~ "/"), (post.cat_label, post.cat_url, post.abs_cat_url), (post.short_title or post.title, post.url, post.abs_url)]) }}
 <article style="--c:{{ post.cat_color }}">
   <header class="art-head narrow">
@@ -32,4 +47,5 @@
       <a class="eyebrow" href="{{ post.cat_url }}">{{ post.cat_label }}</a>
       <time datetime="{{ post.iso }}">{{ post.date_str }}</time>
+      <span class="muted">{{ post.minutes }} dk okuma</span>
     </div>
     <h1>{{ post.title_disp }}</h1>
@@ -44,5 +60,5 @@
 
   <figure class="art-media">
-    <div class="ph">{{ img(post, eager=true, sizes='100vw') }}</div>
+    <div class="ph">{{ img(post, eager=true, sizes='(min-width: 1232px) 1200px, 100vw', priority=true) }}</div>
     <figcaption>{% if post.ai_image %}Temsili görsel, yapay zeka ile üretilmiştir.{% else %}Temsili görsel.{% endif %}</figcaption>
   </figure>
@@ -53,4 +69,11 @@
     {% endif %}
     <div class="art-body">{{ post.body_html|safe }}</div>
+
+    {% if post.tag_list %}
+    <nav class="art-tags" aria-label="Konular">
+      <span class="muted">Konular</span>
+      {% for t in post.tag_list %}<a href="{{ t.url }}">{{ t.label }}</a>{% endfor %}
+    </nav>
+    {% endif %}
 
     <section class="sources" aria-labelledby="kaynaklar">
@@ -75,5 +98,5 @@
 
 {% if related %}
-  {{ rail(related, 'Daha fazla haber.', 'ilgili') }}
+  {{ rail(related, 'İlgili haberler.', 'ilgili', '', post.cat_url) }}
 {% endif %}
 {% endblock %}
@@@YZ@@@ FILE templates/category.html
{% extends "base.html" %}
{% from "_macros.html" import card, crumbs %}
{% block title %}{{ cat.seo_title }}: son dakika gelişmeler | {{ site.name }}{% endblock %}
{% block description %}{{ cat.seo_title }}: {{ cat.intro }} Güncel ve kaynağıyla, Türkçe.{% endblock %}
{% block main %}
{{ crumbs([("Ana sayfa", site.base ~ "/", site.url ~ "/"), (cat.label, cat.url, site.url ~ "/kategori/" ~ cat.slug ~ "/")]) }}
<header class="page-head wrap" style="--c:{{ cat.color }}">
  <span class="eyebrow">{{ cat.label }}</span>
  <h1>{{ cat.seo_title }}.</h1>
  <p>{{ cat.intro }}</p>
  <p class="muted small">{% if cat.count %}{{ cat.count }} haber{% else %}Bu kategoride henüz haber yok.{% endif %}</p>
</header>
{% if posts %}
<section class="wrap"><div class="grid">{% for p in posts %}{{ card(p, heading='h2') }}{% endfor %}</div></section>
{% endif %}
{% endblock %}
@@@YZ@@@ FILE templates/archive.html
{% extends "base.html" %}
{% from "_macros.html" import card %}
{% block title %}Yapay zeka haberleri arşivi, sayfa {{ page }} | {{ site.name }}{% endblock %}
{% block description %}Yapay zeka haberleri arşivi, sayfa {{ page }}: modeller, ürünler, yatırımlar, araştırmalar ve regülasyon haberleri, kaynağıyla.{% endblock %}
{% block head %}
{% if prev_url %}<link rel="prev" href="{{ prev_url }}">{% endif %}
{% if next_url %}<link rel="next" href="{{ next_url }}">{% endif %}
{% endblock %}
{% block main %}
<header class="page-head wrap"><span class="eyebrow" style="--c:#6E6E73">Arşiv</span><h1>Yapay zeka haberleri.</h1><p>Sayfa {{ page }} / {{ pages }}</p></header>
<section class="wrap"><div class="grid">{% for p in posts %}{{ card(p, heading='h2') }}{% endfor %}</div></section>
<nav class="pager wrap" aria-label="Sayfalar">
  {% if prev_url %}<a class="more" href="{{ prev_url }}">Daha yeni</a>{% endif %}
  <span class="muted">{{ page }} / {{ pages }}</span>
  {% if next_url %}<a class="more" href="{{ next_url }}">Daha eski</a>{% endif %}
</nav>
{% endblock %}
@@@YZ@@@ FILE templates/tag.html
{% extends "base.html" %}
{% from "_macros.html" import card, crumbs %}
{% block title %}{{ tag.label }} haberleri: son gelişmeler | {{ site.name }}{% endblock %}
{% block description %}{{ tag.label }} ile ilgili en son yapay zeka haberleri ve gelişmeler. {{ tag.count }} haber, her biri kaynağıyla ve Türkçe.{% endblock %}
{% block main %}
{{ crumbs([("Ana sayfa", site.base ~ "/", site.url ~ "/"), (tag.label, tag.url, site.url ~ "/etiket/" ~ tag.slug ~ "/")]) }}
<header class="page-head wrap" style="--c:#6E6E73">
  <span class="eyebrow">Konu</span>
  <h1>{{ tag.label }} haberleri.</h1>
  <p>{{ tag.label }} hakkındaki son yapay zeka gelişmeleri, kaynağıyla.</p>
  <p class="muted small">{{ tag.count }} haber</p>
</header>
