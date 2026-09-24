YZRADAR-BUNDLE v1 part 1/1
@@@YZ@@@ PATCH haberbot/llm.py
--- a/haberbot/llm.py
+++ b/haberbot/llm.py
@@ -149,8 +149,9 @@
         self._model_ok: dict[str, str] = {}
         self._variant_ok: dict[str, int] = {}
+        self._busy: set[str] = set()  # bu turda yoğunluk/sınır hatası veren modeller
         self._avail: list[str] | None = None
 
     def _post(self, model: str, body: dict) -> dict:
-        delays = [10, 25]
+        delays = [8]
         for attempt in range(len(delays) + 1):
             wait = self.min_interval - (time.time() - self._last)
@@ -203,10 +204,12 @@
 
     def _models(self, model: str) -> list[str]:
-        if model in self._model_ok:
-            return [self._model_ok[model]]
         avail = self._available()
         flash, lite = self._rank(avail, False)[:3], self._rank(avail, True)[:2]
         order = [model] + (lite + flash if "lite" in model else flash + lite) + GEMINI_FALLBACKS
-        return list(dict.fromkeys(order))
+        if model in self._model_ok:  # son çalışan model önce denenir, ama diğerleri yedekte kalır
+            order.insert(0, self._model_ok[model])
+        order = list(dict.fromkeys(order))
+        # yoğun olanlar sona
+        return [m for m in order if m not in self._busy] + [m for m in order if m in self._busy]
 
     def json(self, model: str, system: str, user: str, schema: dict,
@@ -243,4 +246,5 @@
                     if re.search(r"HTTP (429|5\d\d)|Tekrar denemeler|Bağlantı", msg):
                         log.warning("Gemini %s meşgul/sınırda, sıradaki model deneniyor", m)
+                        self._busy.add(m)
                         break
                     raise
@@ -260,4 +264,5 @@
                     out = _parse_json(text)
                     self._model_ok[model] = m
+                    self._busy.discard(m)
                     self._variant_ok[model] = ("responseJsonSchema" not in gc) + ("responseSchema" not in gc and "responseJsonSchema" not in gc)
                     return out
@@ -265,5 +270,5 @@
                     last_err = LLMError(f"JSON çözümlenemedi: {e}; metin: {text[:200]}")
                     continue
-        raise LLMError(str(last_err))
+        raise LLMError(("Tüm modeller meşgul: " if self._busy else "") + str(last_err))
 
 
@@@YZ@@@ PATCH haberbot/app.py
--- a/haberbot/app.py
+++ b/haberbot/app.py
@@ -118,4 +118,9 @@
         except TelegramError as e:
             log.warning("Telegram bildirimi gönderilemedi: %s", e)
+
+    @staticmethod
+    def _transient(e: Exception) -> bool:
+        """Google tarafındaki geçici yoğunluk/sınır: kullanıcıyı rahatsız etmeye gerek yok, sonraki turda tekrar denenir."""
+        return bool(re.search(r"HTTP (429|5\d\d)|meşgul|Tekrar denemeler|Bağlantı hatası|high demand|UNAVAILABLE", str(e)))
 
     def notify_error(self, text: str) -> None:
@@ -177,5 +182,8 @@
                                 TRIAGE_SCHEMA, max_tokens=8000)
         except LLMError as e:
-            self.notify_error(f"Yapay zeka (ayıklama) hatası: {e}")
+            if self._transient(e):
+                log.warning("Yapay zeka şu an yoğun (ayıklama), sonraki turda tekrar denenecek: %s", str(e)[:160])
+            else:
+                self.notify_error(f"Yapay zeka (ayıklama) hatası: {e}")
             for it in fresh:  # bir sonraki turda tekrar denensin
                 st.seen.pop(it["key"], None)
@@ -209,5 +217,9 @@
                 self.create_draft(s, its)
             except LLMError as e:
-                self.notify_error(f"Yapay zeka (yazım) hatası: {e}")
+                if self._transient(e):
+                    log.warning("Yapay zeka şu an yoğun (yazım), kalan %d haber sonraki turda yazılacak: %s",
+                                len(todo) - n, str(e)[:160])
+                else:
+                    self.notify_error(f"Yapay zeka (yazım) hatası: {e}")
                 for _, rest in todo[n:]:  # yazılamayanlar bir sonraki turda yeniden denensin
                     for it in rest:
@@@YZ@@@ SHA
bc70b70ca47b6e0cfcef002074e7c7ac0f5d52e4377ed8411778d8c7d3aaa71b haberbot/llm.py
d92baa9cbf90c51df8d66912e7cfff83fb02c374afcee6a1011abb4592b54922 haberbot/app.py
