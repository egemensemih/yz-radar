YZRADAR-BUNDLE v1 part 1/1
@@@YZ@@@ PATCH haberbot/site.py
--- a/haberbot/site.py
+++ b/haberbot/site.py
@@ -139,6 +139,7 @@
             "hero_stat_label": (p.get("hero_stat_label") or "").strip(),
             "ai_image": (p.get("image") or {}).get("source") == "ai",
             "cover_image": (p.get("image") or {}).get("source") == "cover",
+            "stat_on_cover": (p.get("image") or {}).get("source") == "cover" and (p.get("image") or {}).get("layout") == "sayi",
             "img_alt": clip(p.get("image_alt") or f"{short}: habere ait temsili görsel", 125),
             "seo_title": seo_title,
             "meta_description": clip(meta, 158),
@@@YZ@@@ PATCH templates/_macros.html
--- a/templates/_macros.html
+++ b/templates/_macros.html
@@ -29,7 +29,7 @@
     <span class="slide-txt">
       <span class="slide-top">
         <span class="chip">{{ p.kicker_disp }}</span>
-        {% if p.hero_stat %}<span class="chip stat-chip"><b>{{ p.hero_stat }}</b>{% if p.hero_stat_label %} {{ p.hero_stat_label }}{% endif %}</span>{% endif %}
+        {% if p.hero_stat and not p.stat_on_cover %}<span class="chip stat-chip"><b>{{ p.hero_stat }}</b>{% if p.hero_stat_label %} {{ p.hero_stat_label }}{% endif %}</span>{% endif %}
       </span>
       <h2>{{ p.title_disp }}</h2>
       <span class="slide-dek">{{ p.summary }}</span>
@@@YZ@@@ PATCH templates/article.html
--- a/templates/article.html
+++ b/templates/article.html
@@ -64,7 +64,7 @@
   </figure>
 
   <div class="narrow">
-    {% if post.hero_stat %}
+    {% if post.hero_stat and not post.stat_on_cover %}
     <div class="stat-band"><div class="stat">{{ post.hero_stat }}</div>{% if post.hero_stat_label %}<div class="stat-label">{{ post.hero_stat_label }}</div>{% endif %}</div>
     {% endif %}
     <div class="art-body">{{ post.body_html|safe }}</div>
@@@YZ@@@ SHA
bf526470b99d2fdd25e183420853170c1cac839c43ee63981dfa4c12d115dcbe  haberbot/site.py
f50e1a4bd19b9a51f3d09c3454d21b5a897bd8ad213ab883b33ef252fbec9965  templates/_macros.html
d4a89009660ae522589510d7da08ec03be0d77d383d7fc9e9ec16f2212e3768d  templates/article.html
