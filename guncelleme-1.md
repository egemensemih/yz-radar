YZRADAR-BUNDLE v1 part 1/1
@@@YZ@@@ PATCH haberbot/__main__.py
--- a/haberbot/__main__.py
+++ b/haberbot/__main__.py
@@ -5,8 +5,10 @@
 """
 from __future__ import annotations
 
+import hashlib
 import os
 import sys
+from pathlib import Path
 
 from .app import App, write_github_output
 from .config import load_config
@@ -32,10 +34,13 @@
         app = App(cfg)
         changed = app.run()
         in_ci = os.environ.get("GITHUB_ACTIONS") == "true"
-        stale = hours_since(app.state.get("last_build")) >= 1  # "bugün N gelişme" gibi bilgiler saatte bir tazelensin
+        # Site saatte bir tazelenir ("bugün N gelişme" gibi bilgiler için); tasarım/kod değişince hemen yeniden üretilir
+        sig = build_signature(cfg)
+        stale = hours_since(app.state.get("last_build")) >= 1 or app.state.get("build_sig") != sig
         if changed or cfg.force_build or stale or (not in_ci and not (cfg.out_dir / "index.html").exists()):
             SiteBuilder(cfg).build()
             app.state["last_build"] = iso(now_utc())
+            app.state["build_sig"] = sig
             app.store.save()
             changed = True
         write_github_output("site_changed", "true" if changed else "false")
@@ -45,6 +50,20 @@
     return 2
 
 
+def build_signature(cfg) -> str:
+    """Siteyi etkileyen dosyaların (şablonlar, stil, site kodu, ayarlar) özeti."""
+    root = Path(__file__).resolve().parent.parent
+    h = hashlib.sha1()
+    files = [root / "config.yaml", root / "haberbot" / "site.py"]
+    for d in ("templates", "static"):
+        files += sorted(p for p in (root / d).rglob("*") if p.is_file())
+    for p in files:
+        if p.exists():
+            h.update(p.relative_to(root).as_posix().encode())
+            h.update(p.read_bytes())
+    return h.hexdigest()[:16]
+
+
 def check(cfg) -> int:
     ok = True
     print(f"Site adresi       : {cfg.site_url}")
@@@YZ@@@ SHA
d4909d2a582876630d6aeae0aac89c669fb39133be1b33bf49447c066fd1d18d  haberbot/__main__.py
