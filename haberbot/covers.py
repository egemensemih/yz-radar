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
