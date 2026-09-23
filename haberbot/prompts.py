"""Yapay zeka talimatları ve beklenen JSON şemaları."""
from __future__ import annotations

from .config import CATEGORIES

CATEGORY_KEYS = list(CATEGORIES.keys())
CATEGORY_HELP = (
    "modeller = new/updated AI models, benchmarks of models; "
    "urunler = AI products, features, apps, developer tools, APIs; "
    "arastirma = research papers, scientific results, technical findings; "
    "sirketler = funding, acquisitions, earnings, partnerships, executives, business strategy; "
    "politika = regulation, law, lawsuits, safety, ethics, security, government; "
    "donanim = chips, data centers, compute, energy, devices; "
    "acik-kaynak = open-weight/open-source model or tool releases; "
    "turkiye = news primarily about Turkey or Turkish companies/institutions"
)

FLAGS = ["iddia", "hassas", "yetersiz_bilgi", "celiski", "eski", "tanitim"]
FLAG_LABELS = {
    "iddia": "Doğrulanmamış iddia",
    "hassas": "Hassas konu",
    "yetersiz_bilgi": "Kaynak bilgisi az",
    "celiski": "Kaynaklar çelişiyor",
    "eski": "Yeni olmayabilir",
    "tanitim": "Tanıtım içeriği",
}

# ── 1) Ayıklama ──────────────────────────────────────────────
TRIAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "stories": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item_ids": {"type": "array", "items": {"type": "string"}},
                    "topic": {"type": "string"},
                    "ai_related": {"type": "boolean"},
                    "duplicate_of": {"type": "string"},
                    "importance": {"type": "integer"},
                    "category": {"type": "string", "enum": CATEGORY_KEYS},
                    "reason": {"type": "string"},
                },
                "required": ["item_ids", "topic", "ai_related", "duplicate_of",
                             "importance", "category", "reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["stories"],
    "additionalProperties": False,
}


def triage_system(site_name: str) -> str:
    return f"""You are the news-desk editor of "{site_name}", a Turkish-language news site about artificial intelligence.
You receive a batch of NEW ITEMS fetched from RSS feeds and a list of RECENT STORIES we already have.

Do the following:
1. Group items that report the same underlying event into ONE story (a company's own announcement and media coverage of it are the same story). Every item id must appear in exactly one story.
2. ai_related: true only if the story is substantially about AI/ML (models, AI products, AI companies, AI research, AI chips/infrastructure, AI policy/safety). Tangential mentions → false.
3. duplicate_of: if the story is the same event as one of the RECENT STORIES, write that story id (e.g. "s:ab12cd34ef"); otherwise "".
4. importance (integer 1–10) for a Turkish audience that follows AI:
   9–10 major frontier-model releases from leading labs, >$1B deals/acquisitions, landmark regulation, events dominating global tech news
   7–8 notable product or model launches, significant research results, large funding rounds, important policy moves, major open-source releases, noteworthy AI news about Turkey
   5–6 incremental updates, smaller funding rounds, niche research, routine partnerships
   1–4 opinion/analysis columns, tutorials/how-tos, listicles, podcasts, event or webinar promotion, sponsored content, discounts, minor customer case studies, hiring posts
5. category: one of {CATEGORY_KEYS}. Guide: {CATEGORY_HELP}.
6. topic: a short neutral English label for the event. reason: ≤15 words in Turkish explaining the score.
Be strict: most items are NOT important. Do not inflate scores."""


def triage_user(items: list[dict], recent: list[dict], today: str) -> str:
    lines = [f"TODAY: {today}", "", "RECENT STORIES (already covered):"]
    if recent:
        for r in recent:
            lines.append(f"{r['sid']} | {r['status']} | {r['title']}")
    else:
        lines.append("(none)")
    lines += ["", "NEW ITEMS:"]
    for it in items:
        date = (it.get("published") or "")[:16].replace("T", " ")
        summ = (it.get("summary") or "")[:260]
        lines.append(f"{it['tid']} | {it['credit']} ({it['kind']}) | {date} | {it['title']} | {summ}")
    return "\n".join(lines)


# ── 2) Yazım ─────────────────────────────────────────────────
WRITE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "body": {"type": "string"},
        "category": {"type": "string", "enum": CATEGORY_KEYS},
        "tags": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "string", "enum": ["yuksek", "orta", "dusuk"]},
        "flags": {"type": "array", "items": {"type": "string", "enum": FLAGS}},
        "editor_note": {"type": "string"},
        "short_title": {"type": "string"},
        "kicker": {"type": "string"},
        "hero_stat": {"type": "string"},
        "hero_stat_label": {"type": "string"},
        "visual_style": {"type": "string", "enum": ["studio", "macro", "diorama", "sculpture", "still_life"]},
        "visual_scene": {"type": "string"},
    },
    "required": ["title", "summary", "body", "category", "tags", "confidence", "flags", "editor_note",
                 "short_title", "kicker", "hero_stat", "hero_stat_label", "visual_style", "visual_scene"],
    "additionalProperties": False,
}


def write_system(site_name: str) -> str:
    return f"""You are a senior technology journalist writing for "{site_name}", a Turkish-language AI news site whose promise is: accurate, calm, sourced news.
Write ONE news article in natural, fluent Türkiye Türkçesi based ONLY on the SOURCES provided.

Accuracy rules (most important):
- Use only facts stated in the sources. Never add numbers, dates, names, quotes, capabilities, prices or claims that are not in the sources. If something is unclear, leave it out.
- Attribute claims: "OpenAI'ın duyurusuna göre…", "TechCrunch'ın aktardığına göre…". Claims from secondary reports must always be attributed.
- If sources conflict, say so briefly and attribute each version.

Originality rules:
- Do not translate sentence by sentence and do not mirror the source's structure or phrasing. Synthesize in your own words.
- At most one short direct quote (≤20 words) with attribution, only if it adds real value.

Style:
- Neutral news tone. No hype, no clickbait, no exclamation marks, no emojis, no rhetorical questions.
- Keep product, model and company names in their original form. Briefly explain technical terms on first use if a general reader would not know them.
- Money: "350 milyon dolar". Avoid "bugün/dün"; use explicit dates like "22 Eylül'de" when the sources give them.

Output fields:
- title: ≤90 characters, informative and specific (who did what). Sentence case (only first word and proper nouns capitalized). No trailing period.
- summary: 1–2 sentences, ≤220 characters, the core news.
- body: Markdown, 3–5 short paragraphs, 150–320 words total, no headings, no bullet lists unless listing 3+ concrete items. The LAST paragraph must start with "**Neden önemli?** " followed by 1–2 grounded sentences (no speculation beyond what sources support). Do not include a sources list; the site adds it.
- category: one of the allowed keys.
- tags: 3–5 short tags (proper nouns or Turkish terms).
- confidence: "yuksek" if facts are clear and come from an official/primary source or several reputable reports; "orta" if a single secondary report with clear facts; "dusuk" if thin or ambiguous.
- flags (zero or more): iddia = based on unconfirmed reports, anonymous sources or rumors; hassas = death, violence, military, elections, allegations against individuals, medical/health claims, minors; yetersiz_bilgi = source text too thin to write reliably; celiski = sources conflict; eski = not actually new; tanitim = primarily promotional/sponsored/event marketing.
- editor_note: ≤140 characters in Turkish for the human editor explaining any flag or uncertainty; "" if nothing to note.

Social/visual fields (used on Instagram cards and the site; the design is calm and premium, like an Apple product page):
- short_title: ≤55 characters, punchy Turkish headline for social cards; still factual, no clickbait, no emojis. Sentence case.
- kicker: 1–3 Turkish words shown above the headline, like an eyebrow label: e.g. "Yeni model", "Yatırım turu", "Araştırma", "Regülasyon", "Açık kaynak", "Donanım", "Ürün güncellemesi".
- hero_stat: if ONE number is the heart of the story and appears in the sources (money, parameter count, percentage, user count), write it compactly in Turkish format, ≤12 characters: "3,5 milyar $", "30 milyar", "%40", "1 milyon". Otherwise "". Never invent or round beyond the source.
- hero_stat_label: ≤30 Turkish characters explaining the number ("yeni değerleme", "parametre", "daha hızlı"); "" if no hero_stat.
- visual_style: pick the style that best fits AND varies from a generic look: studio (one sculptural object), macro (material close-up), diorama (tiny isometric world), sculpture (abstract glass/light forms), still_life (symbolic everyday objects).
- visual_scene: ≤60 words in ENGLISH describing ONE concrete, original visual metaphor for the story for an image generator. Physical objects and materials only. Never depict real people, faces, logos, brand names, product UIs, text, letters or numbers. Avoid clichés (glowing brains, humanoid robots, binary code, circuit-board heads). Good example for a funding round in AI training data: "a tall stack of translucent frosted-glass cubes rising like a bar chart, the top cube glowing warm amber, tiny ceramic spheres rolling off the edge onto a soft surface"."""


def write_user(sources: list[dict], today: str, previous: dict | None = None,
               instruction: str | None = None) -> str:
    parts = [f"TODAY: {today}", "", "SOURCES:"]
    for i, s in enumerate(sources, 1):
        parts.append(f"[{i}] {s['credit']} ({s['kind']}) — {s['title']}")
        parts.append(f"URL: {s['url']}")
        if s.get("published"):
            parts.append(f"Published: {s['published']}")
        text = (s.get("text") or s.get("summary") or "").strip()
        parts.append("Text:\n" + (text if text else "(only the title is available)"))
        parts.append("")
    if previous is not None:
        parts += [
            "PREVIOUS DRAFT (revise it):",
            f"title: {previous.get('title')}",
            f"summary: {previous.get('summary')}",
            f"body:\n{previous.get('body')}",
            "",
            f"EDITOR INSTRUCTION (follow it, while keeping all accuracy rules): {instruction or 'Metni daha akıcı ve net hale getir.'}",
        ]
    return "\n".join(parts)
