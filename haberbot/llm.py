"""Claude API istemcisi (yapılandırılmış JSON çıktısı) + test için sahte (mock) mod."""
from __future__ import annotations

import json
import re
import time

import requests

from .util import log

API_URL = "https://api.anthropic.com/v1/messages"

# Tahmini fiyatlar ($ / 1M token): maliyet raporu içindir, faturalamayı etkilemez.
PRICES = {
    "haiku": (1.0, 5.0),
    "sonnet": (2.0, 10.0),
    "opus": (4.0, 20.0),
    "fable": (10.0, 50.0),
}


def estimate_cost(model: str, tok_in: int, tok_out: int) -> float:
    for k, (pi, po) in PRICES.items():
        if k in model:
            return tok_in / 1e6 * pi + tok_out / 1e6 * po
    return tok_in / 1e6 * 3 + tok_out / 1e6 * 15


class LLMError(RuntimeError):
    pass


class LLM:
    def __init__(self, api_key: str, usage_cb=None):
        self.api_key = api_key
        self.usage_cb = usage_cb  # (model, in, out) → None

    def _post(self, body: dict) -> dict:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        delays = [5, 20, 60]
        for attempt in range(len(delays) + 1):
            try:
                r = requests.post(API_URL, headers=headers, json=body, timeout=300)
            except requests.RequestException as e:
                if attempt < len(delays):
                    time.sleep(delays[attempt])
                    continue
                raise LLMError(f"Bağlantı hatası: {e}") from e
            if r.status_code in (429, 500, 502, 503, 504, 529) and attempt < len(delays):
                log.warning("Claude API %s, %ss sonra tekrar denenecek", r.status_code, delays[attempt])
                time.sleep(delays[attempt])
                continue
            if r.status_code >= 400:
                try:
                    msg = r.json().get("error", {}).get("message", r.text)
                except ValueError:
                    msg = r.text
                raise LLMError(f"HTTP {r.status_code}: {msg[:300]}")
            return r.json()
        raise LLMError("Tekrar denemeler tükendi")

    def json(self, model: str, system: str, user: str, schema: dict,
             max_tokens: int = 4000, effort: str | None = None) -> dict:
        """Şemaya uyan JSON döndürür. Model/sürüm farklarına karşı kademeli geri çekilir."""
        use_effort = bool(effort) and "haiku" not in model
        variants = []
        oc = {"format": {"type": "json_schema", "schema": schema}}
        if use_effort:
            variants.append({**oc, "effort": effort})
        variants.append(oc)
        variants.append(None)  # yapılandırılmış çıktı yoksa: şemayı talimata ekle

        last_err: Exception | None = None
        for oc_variant in variants:
            body = {
                "model": model,
                "max_tokens": max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            }
            if oc_variant is not None:
                body["output_config"] = oc_variant
            else:
                body["system"] = system + (
                    "\n\nReturn ONLY a JSON object (no prose, no code fences) matching this JSON schema:\n"
                    + json.dumps(schema, ensure_ascii=False))
            try:
                resp = self._post(body)
            except LLMError as e:
                last_err = e
                if "HTTP 400" in str(e):
                    log.info("Claude isteği bu biçimle kabul edilmedi, sade biçim deneniyor: %s", e)
                    continue
                raise
            usage = resp.get("usage") or {}
            if self.usage_cb:
                self.usage_cb(model, int(usage.get("input_tokens", 0)), int(usage.get("output_tokens", 0)))
            if resp.get("stop_reason") == "max_tokens":
                raise LLMError("Yanıt token sınırına takıldı")
            text = "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text")
            try:
                return _parse_json(text)
            except ValueError as e:
                last_err = LLMError(f"JSON çözümlenemedi: {e}; metin: {text[:200]}")
                continue
        raise LLMError(str(last_err))


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            raise ValueError("JSON bulunamadı")
        return json.loads(m.group(0))


# ── Sahte mod (yerel test için; gerçek API çağrısı yapmaz) ────────
_KW = [
    ("donanim", ("chip", "gpu", "nvidia", "data center", "qualcomm", "compute")),
    ("sirketler", ("raises", "funding", "valuation", "acquire", "series", "yatırım", "billion")),
    ("politika", ("law", "regulat", "court", "lawsuit", "safety", "pentagon", "eu ")),
    ("arastirma", ("research", "paper", "study", "benchmark")),
    ("acik-kaynak", ("open-source", "open source", "open-weight", "llama", "hugging")),
    ("modeller", ("gpt", "gemini", "claude", "model", "grok")),
]


class MockLLM:
    def __init__(self, *a, **k):
        self.usage_cb = k.get("usage_cb")

    def json(self, model, system, user, schema, max_tokens=4000, effort=None) -> dict:
        if self.usage_cb:
            self.usage_cb(model, len(user) // 4, 300)
        if "stories" in schema.get("properties", {}):
            return self._triage(user)
        return self._write(user)

    @staticmethod
    def _cat(text: str) -> str:
        t = text.lower()
        for cat, kws in _KW:
            if any(k in t for k in kws):
                return cat
        return "urunler"

    def _triage(self, user: str) -> dict:
        stories = []
        section = user.split("NEW ITEMS:", 1)[-1]
        for line in section.strip().splitlines():
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 4:
                continue
            tid, credit, _, title = parts[0], parts[1], parts[2], parts[3]
            imp = 8 if "(official)" in credit else 6
            if any(k in title.lower() for k in ("summit", "agenda", "podcast", "webinar")):
                imp = 3
            stories.append({"item_ids": [tid], "topic": title[:60], "ai_related": True,
                            "duplicate_of": "", "importance": imp, "category": self._cat(title),
                            "reason": "Test modu puanı"})
        return {"stories": stories}

    def _write(self, user: str) -> dict:
        m = re.search(r"\[1\] (.+?) \((\w+)\) — (.+)", user)
        credit, kind, title = (m.group(1), m.group(2), m.group(3)) if m else ("Kaynak", "media", "Haber")
        instr = re.search(r"EDITOR INSTRUCTION[^:]*: (.+)", user)
        t = f"{title[:80]}"
        if instr:
            t = f"{t} (düzeltildi)"
        body = (
            f"Bu metin **test modunda** üretildi; gerçek kurulumda burada Claude'un {credit} kaynağından "
            f"yazdığı özgün Türkçe haber metni yer alır.\n\n"
            f"Kaynak başlığı: _{title}_.\n\n"
            f"**Neden önemli?** Test modunda örnek bir değerlendirme cümlesi."
        )
        return {
            "title": t, "summary": f"{credit} kaynaklı gelişme (test özeti): {title[:120]}",
            "body": body, "category": self._cat(title), "tags": [credit, "yapay zeka"],
            "confidence": "yuksek" if kind == "official" else "orta",
            "flags": [] if kind == "official" else ["iddia"] if "report" in title.lower() else [],
            "editor_note": "",
            "short_title": t[:55],
            "kicker": {"official": "Duyuru", "media": "Gündem"}.get(kind, "Gündem"),
            "hero_stat": (m2.group(1) if (m2 := re.search(r"\$(\d+(?:\.\d+)?)\s?(B|M)\b", title)) else ""),
            "hero_stat_label": "",
            "visual_style": "studio",
            "visual_scene": "a smooth sculptural object on a pastel backdrop",
        }
