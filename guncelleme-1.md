YZRADAR-BUNDLE v1 part 1/1
@@@YZ@@@ PATCH config.yaml
--- a/config.yaml
+++ b/config.yaml
@@ -29,15 +29,16 @@
 
 schedule:
   timezone: "Europe/Istanbul"
-  collect_every_minutes: 60      # Kaynaklar kaç dakikada bir taransın
+  collect_every_minutes: 15      # Kaynaklar kaç dakikada bir taransın
   daily_summary_hour: 21         # Günlük özet Telegram'a saat kaçta gelsin
   quiet_hours: [0, 8]            # Bu saatler arasında bildirimler sessiz gelir
-  listen_seconds: 120            # Bekleyen haber varsa, butonlara hızlı tepki için bekleme süresi
+  listen_seconds: 240            # Butonlara anında tepki için her turda Telegram'ı dinleme süresi (sn)
 
 editorial:
   min_importance: 6              # 1-10 arası. Bunun altındaki haberler hiç önüne gelmez
-  max_drafts_per_run: 5          # Bir taramada en fazla kaç yeni haber taslağı yazılsın
-  max_drafts_per_day: 25         # Günlük üst sınır (maliyet kontrolü)
+  max_drafts_per_run: 2          # Bir taramada en fazla kaç yeni haber taslağı yazılsın (haberler tek tek, düzenli gelsin)
+  max_drafts_per_day: 40         # Günlük üst sınır; gün içine eşit yayılır
+  active_hours: [7, 24]          # Taslakların yayıldığı saatler (gece en fazla birkaç haber gelir, kalanlar sabaha kalır)
   max_item_age_hours: 36         # Bundan eski haberler atlanır
   pending_expire_hours: 36       # Onaylanmayan taslak bu süre sonunda düşer
   fetch_full_text: true          # Haberin tam metnini kaynağından okuyup daha doğru özet çıkar
@@@YZ@@@ PATCH haberbot/app.py
--- a/haberbot/app.py
+++ b/haberbot/app.py
@@ -23,6 +23,13 @@
                    tr_date)
 
 KIND_ORDER = {"official": 0, "media": 1, "community": 2}
+# Uzun süren düğmeler: (hemen gösterilen yanıt, işlem bitince beklenen sonuç)
+SLOW_ACTIONS = {
+    "p": ("⏳ Yayınlanıyor…", "✅ Yayınlandı"),
+    "v": ("⏳ Yeni görsel hazırlanıyor…", "🎨 Yeni görsel hazır"),
+    "w": ("⏳ Yeniden yazılıyor…", "🔁 Yeniden yazıldı"),
+    "s": ("⏳ Görseller hazırlanıyor…", "📱 Gönderildi"),
+}
 CONF_LABEL = {"yuksek": "yüksek", "orta": "orta", "dusuk": "düşük"}
 COMMANDS = [
     ("durum", "Sistem durumu ve istatistikler"),
@@ -109,6 +116,19 @@
         h = local(now_utc(), self.cfg.tz).hour
         return (a <= h < b) if a <= b else (h >= a or h < b)
 
+    def draft_budget(self) -> int:
+        """Şu an yazılabilecek taslak sayısı. Günlük sınır güne yayılır: sabah hepsi birden tükenmez,
+        akşam da haber gelmeye devam eder."""
+        ed = lambda k, d: self.cfg.get("editorial", k, d)  # noqa: E731
+        cap = int(ed("max_drafts_per_day", 40))
+        used = self.store.count(self.today(), "drafts")
+        a, b = (ed("active_hours", [7, 24]) or [0, 24])[:2]
+        now_l = local(now_utc(), self.cfg.tz)
+        h = now_l.hour + now_l.minute / 60
+        frac = min(1.0, max(0.0, (h - a) / max(1, b - a)))
+        allowed = int(cap * frac + 0.999) + int(ed("burst", 3))
+        return max(0, min(cap - used, allowed - used))
+
     def notify(self, text: str, silent: bool | None = None, keyboard=None) -> None:
         if not (self.tg and self.chat_id):
             log.info("[bildirim] %s", re.sub(r"<[^>]+>", "", text)[:200])
@@ -140,7 +160,13 @@
         cfg, st = self.cfg, self.store
         ed = lambda k, d: cfg.get("editorial", k, d)  # noqa: E731
         today = self.today()
-        remaining = ed("max_drafts_per_day", 25) - st.count(today, "drafts")
+        remaining = self.draft_budget()
+        if remaining <= 0:
+            # Haberler "görüldü" sayılmaz; sıra gelince (en geç ertesi sabah) değerlendirilir.
+            self.state["last_collect"] = iso(now_utc())
+            log.info("Taslak sırası dolu (bugün %d taslak); yeni haberler sonraki turda değerlendirilecek.",
+                     st.count(today, "drafts"))
+            return
         items = fetch_all(cfg, st)
         seeded = set(self.state.get("seeded_sources", []))
         max_age = ed("max_item_age_hours", 36)
@@ -157,78 +183,95 @@
         self.state["seeded_sources"] = sorted(seeded | {it["source"] for it in items})
         self.state["last_collect"] = iso(now_utc())
         log.info("Yeni öğe: %d (toplam okunan %d)", len(fresh), len(items))
-        if not fresh:
-            return
-        if remaining <= 0:
-            log.info("Günlük taslak sınırına ulaşıldı (%s).", ed("max_drafts_per_day", 25))
-            return
-
-        fresh.sort(key=lambda x: (KIND_ORDER.get(x["kind"], 3), hours_since(x["published"]) if x["published"] else 0))
-        fresh = fresh[:80]
-        by_tid = {}
-        for i, it in enumerate(fresh, 1):
-            it["tid"] = f"i{i}"
-            by_tid[it["tid"]] = it
-
-        recent = []
-        for p in st.posts():
-            if hours_since(p.get("published_at")) < 72:
-                recent.append({"sid": "s:" + p["id"], "status": "published", "title": p["title"]})
-        for d in st.drafts():
-            recent.append({"sid": "s:" + d["id"], "status": d.get("status", "pending"), "title": d["title"]})
-
-        try:
-            tri = self.llm.json(cfg.get("ai", "triage_model", "claude-haiku-4-5-20251001"),
-                                triage_system(self.brand), triage_user(fresh, recent[:80], today),
-                                TRIAGE_SCHEMA, max_tokens=8000)
-        except LLMError as e:
-            if self._transient(e):
-                log.warning("Yapay zeka şu an yoğun (ayıklama), sonraki turda tekrar denenecek: %s", str(e)[:160])
-            else:
-                self.notify_error(f"Yapay zeka (ayıklama) hatası: {e}")
-            for it in fresh:  # bir sonraki turda tekrar denensin
-                st.seen.pop(it["key"], None)
+        queue = self._queue(max_age)
+        if not fresh and not queue:
             return
 
         min_imp = ed("min_importance", 6)
-        chosen, merged, skipped = [], 0, 0
-        for s in tri.get("stories", []):
-            its = [by_tid[t] for t in s.get("item_ids", []) if t in by_tid]
-            if not its:
-                continue
-            dup = (s.get("duplicate_of") or "").removeprefix("s:")
-            if dup:
-                if self._merge_sources(dup, its):
+        new_stories, merged, skipped = [], 0, 0
+        if fresh:
+            fresh.sort(key=lambda x: (KIND_ORDER.get(x["kind"], 3), hours_since(x["published"]) if x["published"] else 0))
+            fresh = fresh[:80]
+            by_tid = {}
+            for i, it in enumerate(fresh, 1):
+                it["tid"] = f"i{i}"
+                by_tid[it["tid"]] = it
+
+            recent = [{"sid": f"q:{i}", "status": "queued", "title": q["story"].get("topic", "")}
+                      for i, q in enumerate(queue)]
+            for d in st.drafts():
+                recent.append({"sid": "s:" + d["id"], "status": d.get("status", "pending"), "title": d["title"]})
+            for p in st.posts():
+                if hours_since(p.get("published_at")) < 72:
+                    recent.append({"sid": "s:" + p["id"], "status": "published", "title": p["title"]})
+
+            try:
+                tri = self.llm.json(cfg.get("ai", "triage_model", "claude-haiku-4-5-20251001"),
+                                    triage_system(self.brand), triage_user(fresh, recent[:100], today),
+                                    TRIAGE_SCHEMA, max_tokens=8000)
+            except LLMError as e:
+                if self._transient(e):
+                    log.warning("Yapay zeka şu an yoğun (ayıklama), sonraki turda tekrar denenecek: %s", str(e)[:160])
+                else:
+                    self.notify_error(f"Yapay zeka (ayıklama) hatası: {e}")
+                for it in fresh:  # bir sonraki turda tekrar denensin
+                    st.seen.pop(it["key"], None)
+                tri = {"stories": []}
+
+            for s in tri.get("stories", []):
+                its = [by_tid[t] for t in s.get("item_ids", []) if t in by_tid]
+                if not its:
+                    continue
+                dup = (s.get("duplicate_of") or "").strip()
+                if dup.startswith("q:") and dup[2:].isdigit() and int(dup[2:]) < len(queue):
+                    q = queue[int(dup[2:])]  # sıradaki habere yeni kaynak ekle
+                    urls = {it["url"] for it in q["items"]}
+                    q["items"] += [it for it in its if it["url"] not in urls]
                     merged += 1
-                continue
-            if not s.get("ai_related") or int(s.get("importance", 0)) < min_imp:
-                skipped += 1
-                continue
-            chosen.append((s, its))
-        chosen.sort(key=lambda x: -int(x[0].get("importance", 0)))
-        limit = min(ed("max_drafts_per_run", 5), remaining)
-        log.info("Ayıklama: %d hikâye seçildi, %d elendi, %d mevcut habere eklendi (sınır %d)",
-                 len(chosen), skipped, merged, limit)
-        for s, its in chosen[limit:]:  # sınırı aşanlar bir sonraki turda yeniden değerlendirilsin
-            for it in its:
-                st.seen.pop(it["key"], None)
-        todo = chosen[:limit]
-        for n, (s, its) in enumerate(todo):
+                    continue
+                if dup:
+                    if self._merge_sources(dup.removeprefix("s:"), its):
+                        merged += 1
+                    continue
+                if not s.get("ai_related") or int(s.get("importance", 0)) < min_imp:
+                    skipped += 1
+                    continue
+                new_stories.append({"story": s, "items": its, "at": iso(now_utc())})
+
+        # Sıra: önce önemli olanlar; eşitse önce gelen
+        queue = sorted(queue + new_stories, key=lambda q: (-int(q["story"].get("importance", 0)), q["at"]))
+        limit = min(ed("max_drafts_per_run", 2), remaining)
+        todo, queue = queue[:limit], queue[limit:]
+        self.state["queue"] = queue[:40]
+        if fresh:
+            log.info("Ayıklama: %d yeni hikâye, %d elendi, %d mevcut habere eklendi", len(new_stories), skipped, merged)
+        log.info("Bu tur %d taslak yazılacak, sırada %d haber var", len(todo), len(self.state["queue"]))
+        for n, q in enumerate(todo):
+            if n:
+                self.process_updates()  # yazım sürerken basılan düğmeler beklemesin
             try:
-                self.create_draft(s, its)
+                self.create_draft(q["story"], q["items"])
             except LLMError as e:
                 if self._transient(e):
                     log.warning("Yapay zeka şu an yoğun (yazım), kalan %d haber sonraki turda yazılacak: %s",
                                 len(todo) - n, str(e)[:160])
                 else:
                     self.notify_error(f"Yapay zeka (yazım) hatası: {e}")
-                for _, rest in todo[n:]:  # yazılamayanlar bir sonraki turda yeniden denensin
-                    for it in rest:
-                        st.seen.pop(it["key"], None)
+                self.state["queue"] = (todo[n:] + self.state["queue"])[:40]  # yazılamayanlar sırada kalsın
                 break
             except Exception as e:  # noqa: BLE001
                 log.exception("Taslak oluşturulamadı: %s", e)
 
+    def _queue(self, max_age: float) -> list[dict]:
+        """Seçilmiş ama henüz yazılmamış haberler (eskiyenler düşer)."""
+        out = []
+        for q in self.state.get("queue") or []:
+            pubs = [it.get("published") for it in q.get("items", []) if it.get("published")]
+            newest = max(pubs) if pubs else q.get("at")
+            if hours_since(newest) <= max_age and hours_since(q.get("at")) <= max_age:
+                out.append(q)
+        return out
+
     def _merge_sources(self, did: str, its: list[dict]) -> bool:
         d = self.store.load_draft(did)
         if not d or d.get("status") != "pending":
@@ -507,7 +550,15 @@
             if not self._authorized(chat):
                 self.tg.answer_callback(cq["id"], "Yetkin yok.")
                 return
+            self.state["last_activity"] = iso(now_utc())
             action, _, did = (cq.get("data") or "").partition(":")
+            slow = SLOW_ACTIONS.get(action)
+            if slow:  # uzun süren işlerde düğme hemen yanıt versin
+                self.tg.answer_callback(cq["id"], slow[0])
+                msg = self._on_button(action, did)
+                if msg and msg != slow[1]:
+                    self.notify(esc(msg), silent=True)
+                return
             msg = self._on_button(action, did)
             self.tg.answer_callback(cq["id"], msg)
             return
@@ -527,6 +578,8 @@
             return
         if not self._authorized(chat):
             return
+        self.state["last_activity"] = iso(now_utc())
+        self.tg.typing(chat)
 
         reply_to = (msg.get("reply_to_message") or {}).get("message_id")
         if reply_to and text and not text.startswith("/"):
@@ -751,7 +804,7 @@
             f"Mod: <b>{mode}</b>{' · ⏸ DURAKLATILDI' if self.state.get('paused') else ''}",
             f"Bugün: {c.get('published', 0)} yayın ({c.get('auto', 0)} otomatik, {c.get('approved', 0)} onayla), "
             f"{c.get('rejected', 0)} ret, {c.get('drafts', 0)} taslak",
-            f"Bekleyen: {pend}",
+            f"Onay bekleyen: {pend} · Yazılmak için sırada: {len(self.state.get('queue') or [])}",
             f"Son {n} kararda onay oranı: %{rate * 100:.0f}",
             f"Toplam yayın: {len(self.store.posts())}",
             f"Bugünkü tahmini maliyet: ${self._cost(c):.2f} ({c.get('images', 0)} görsel)",
@@ -880,13 +933,22 @@
             return
         deadline = time.time() + seconds
         while time.time() < deadline - 3:
-            if not self.store.drafts("pending") and not self.force_collect:
+            if not self._should_listen():
                 break
             self.process_updates(timeout=int(min(25, deadline - time.time())))
             if self.force_collect and not self.state.get("paused"):
                 self.force_collect = False
                 self.collect()
 
+    def _should_listen(self) -> bool:
+        """Telegram'ı canlı dinle: son 10 dakikada sen bir şey yaptıysan her zaman;
+        onay bekleyen haber varsa sessiz saatler dışında."""
+        if self.force_collect:
+            return True
+        if hours_since(self.state.get("last_activity")) * 60 < 10:
+            return True
+        return bool(self.store.drafts("pending")) and not self.quiet()
+
     # ── tek çalışma ─────────────────────────────────────────
     def run(self) -> bool:
         """Bir tur: Telegram → süre dolanlar → toplama → özet → dinleme. Site değiştiyse True döner."""
@@@YZ@@@ PATCH haberbot/llm.py
--- a/haberbot/llm.py
+++ b/haberbot/llm.py
@@ -140,40 +140,32 @@
 class GeminiLLM:
     """Google Gemini API: ücretsiz katmanda kredi kartı gerektirmez (dakika/gün sınırlıdır)."""
 
-    min_interval = 7.0  # ücretsiz katman: dakikada ~10 istek
+    min_interval = 6.0  # ücretsiz katman: model başına dakikada ~10 istek
 
     def __init__(self, api_key: str, usage_cb=None):
         self.api_key = api_key
         self.usage_cb = usage_cb
-        self._last = 0.0
+        self._last: dict[str, float] = {}  # model başına son istek zamanı
         self._model_ok: dict[str, str] = {}
         self._variant_ok: dict[str, int] = {}
         self._busy: set[str] = set()  # bu turda yoğunluk/sınır hatası veren modeller
+        self._dead: set[str] = set()  # bu hesapta çalışmayan (404) modeller
         self._avail: list[str] | None = None
 
     def _post(self, model: str, body: dict) -> dict:
-        delays = [8]
-        for attempt in range(len(delays) + 1):
-            wait = self.min_interval - (time.time() - self._last)
-            if wait > 0:
-                time.sleep(wait)
-            self._last = time.time()
-            try:
-                r = requests.post(GEMINI_URL.format(model=model), json=body, timeout=300,
-                                  headers={"x-goog-api-key": self.api_key, "Content-Type": "application/json"})
-            except requests.RequestException as e:
-                if attempt < len(delays):
-                    time.sleep(delays[attempt])
-                    continue
-                raise LLMError(f"Bağlantı hatası: {e}") from e
-            if r.status_code in (429, 500, 502, 503, 504) and attempt < len(delays):
-                log.warning("Gemini API %s, %ss sonra tekrar denenecek", r.status_code, delays[attempt])
-                time.sleep(delays[attempt])
-                continue
-            if r.status_code >= 400:
-                raise LLMError(f"HTTP {r.status_code}: {r.text[:300]}")
-            return r.json()
-        raise LLMError("Tekrar denemeler tükendi")
+        """Tek deneme. Yoğunluk/sınır hatasında beklemeden hata verir; json() hemen sıradaki modele geçer."""
+        wait = self.min_interval - (time.time() - self._last.get(model, 0.0))
+        if wait > 0:
+            time.sleep(wait)
+        self._last[model] = time.time()
+        try:
+            r = requests.post(GEMINI_URL.format(model=model), json=body, timeout=240,
+                              headers={"x-goog-api-key": self.api_key, "Content-Type": "application/json"})
+        except requests.RequestException as e:
+            raise LLMError(f"Bağlantı hatası: {e}") from e
+        if r.status_code >= 400:
+            raise LLMError(f"HTTP {r.status_code}: {r.text[:300]}")
+        return r.json()
 
     def _available(self) -> list[str]:
         """Hesapta kullanılabilen Gemini metin modellerini bir kez sorgula (yeni modeller kendiliğinden gelir)."""
@@ -227,7 +219,24 @@
         start = self._variant_ok.get(model, 0)
         variants = variants[start:] + variants[:start]
         last_err: Exception | None = None
+        for rnd in range(2):  # tüm modeller meşgulse kısa bir aradan sonra bir tur daha
+            if rnd:
+                if not self._busy:
+                    break
+                log.warning("Tüm Gemini modelleri meşgul, 20 sn sonra bir tur daha denenecek")
+                time.sleep(20)
+            out = self._try_models(model, base, variants, schema, system)
+            if isinstance(out, dict):
+                return out
+            last_err = out
+        raise LLMError(("Tüm modeller meşgul: " if self._busy else "") + str(last_err))
+
+    def _try_models(self, model: str, base: dict, variants: list[dict], schema: dict, system: str):
+        """Modelleri sırayla dener; başarıda sonuç sözlüğünü, olmazsa son hatayı döndürür."""
+        last_err: Exception | None = None
         for m in self._models(model):
+            if m in self._dead:
+                continue
             for gc in variants:
                 body = {**base, "generationConfig": gc}
                 if "responseJsonSchema" not in gc and "responseSchema" not in gc:
@@ -240,11 +249,12 @@
                     msg = str(e)
                     if "HTTP 404" in msg:
                         log.info("Gemini modeli bulunamadı (%s), sıradaki deneniyor", m)
+                        self._dead.add(m)
                         break
                     if "HTTP 400" in msg:
                         continue
                     if re.search(r"HTTP (429|5\d\d)|Tekrar denemeler|Bağlantı", msg):
-                        log.warning("Gemini %s meşgul/sınırda, sıradaki model deneniyor", m)
+                        log.warning("Gemini %s meşgul/sınırda (%s), sıradaki model deneniyor", m, msg[:8])
                         self._busy.add(m)
                         break
                     raise
@@ -269,7 +279,7 @@
                 except ValueError as e:
                     last_err = LLMError(f"JSON çözümlenemedi: {e}; metin: {text[:200]}")
                     continue
-        raise LLMError(("Tüm modeller meşgul: " if self._busy else "") + str(last_err))
+        return last_err or LLMError("Uygun model bulunamadı")
 
 
 def make_llm(cfg, usage_cb=None):
@@@YZ@@@ PATCH haberbot/telegram.py
--- a/haberbot/telegram.py
+++ b/haberbot/telegram.py
@@ -41,6 +41,13 @@
             "allowed_updates": ["message", "callback_query"],
         }, timeout=timeout + 15)
 
+    def typing(self, chat_id) -> None:
+        """Sohbetin üstünde "yazıyor…" göster (işlem sürerken)."""
+        try:
+            self._call("sendChatAction", {"chat_id": chat_id, "action": "typing"}, timeout=10)
+        except TelegramError:
+            pass
+
     def answer_callback(self, cb_id: str, text: str = "") -> None:
         try:
             self._call("answerCallbackQuery", {"callback_query_id": cb_id, "text": text[:190]})
@@@YZ@@@ PATCH haberbot/__main__.py
--- a/haberbot/__main__.py
+++ b/haberbot/__main__.py
@@ -11,7 +11,7 @@
 from .app import App, write_github_output
 from .config import load_config
 from .site import SiteBuilder
-from .util import log, setup_logging
+from .util import hours_since, iso, log, now_utc, setup_logging
 
 
 def main(argv: list[str]) -> int:
@@ -32,8 +32,11 @@
         app = App(cfg)
         changed = app.run()
         in_ci = os.environ.get("GITHUB_ACTIONS") == "true"
-        if changed or cfg.force_build or (not in_ci and not (cfg.out_dir / "index.html").exists()):
+        stale = hours_since(app.state.get("last_build")) >= 1  # "bugün N gelişme" gibi bilgiler saatte bir tazelensin
+        if changed or cfg.force_build or stale or (not in_ci and not (cfg.out_dir / "index.html").exists()):
             SiteBuilder(cfg).build()
+            app.state["last_build"] = iso(now_utc())
+            app.store.save()
             changed = True
         write_github_output("site_changed", "true" if changed else "false")
         return 0
@@@YZ@@@ PATCH haberbot/prompts.py
--- a/haberbot/prompts.py
+++ b/haberbot/prompts.py
@@ -60,7 +60,7 @@
 Do the following:
 1. Group items that report the same underlying event into ONE story (a company's own announcement and media coverage of it are the same story). Every item id must appear in exactly one story.
 2. ai_related: true only if the story is substantially about AI/ML (models, AI products, AI companies, AI research, AI chips/infrastructure, AI policy/safety). Tangential mentions → false.
-3. duplicate_of: if the story is the same event as one of the RECENT STORIES, write that story id (e.g. "s:ab12cd34ef"); otherwise "".
+3. duplicate_of: if the story is the same event as one of the RECENT STORIES, write that story id (e.g. "s:ab12cd34ef" or "q:3"); otherwise "".
 4. importance (integer 1–10) for a Turkish audience that follows AI:
    9–10 major frontier-model releases from leading labs, >$1B deals/acquisitions, landmark regulation, events dominating global tech news
    7–8 notable product or model launches, significant research results, large funding rounds, important policy moves, major open-source releases, noteworthy AI news about Turkey
@@@YZ@@@ SHA
18f87f5a11e7f74e6ffc6ac20cc259226562b73d621d7de2a820dc3787b7c335  config.yaml
862d81d625269aaf75b509ddd10fd4758a66ba2e30a67683edda5ea659fe3fc0  haberbot/app.py
b1117cbaa0b62efa7257f00b67545fe51736e3ef110e3931e3bcc953b2f2882a  haberbot/llm.py
7a795abbfe5d8512f53beb2e4817e6253e8a1d3e693679cf81e73e79b448ce89  haberbot/telegram.py
f221f7089be441c2510fab29c1e53ddcef3fe39d1c6266bf7f97e73094394907  haberbot/__main__.py
0f22634e04f4e3425c978c36a1b942174ace8fda6b454c1509ee0f2477c02327  haberbot/prompts.py
