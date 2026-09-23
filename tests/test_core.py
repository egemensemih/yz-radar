"""Temel birim testleri:  python -m pytest -q  (ya da: python tests/test_core.py)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from haberbot import policy  # noqa: E402
from haberbot.config import Config  # noqa: E402
from haberbot.site import render_body  # noqa: E402
from haberbot.sources import parse_feed, parse_html_listing  # noqa: E402
from haberbot.app import md_to_tg  # noqa: E402
from haberbot.util import normalize_url, slugify, publisher_name  # noqa: E402

CFG = Config(raw={"autonomy": {"mode": "ogrenen", "source_min_decisions": 10, "source_min_approval": 0.9,
                               "global_window": 30, "global_min_approval": 0.85, "auto_min_importance": 6}})
GOOD = {"id": "x", "flags": [], "confidence": "yuksek", "importance": 8, "source_keys": ["OpenAI"]}


def test_policy_learning_path():
    stats = {"sources": {}, "decisions": []}
    assert policy.decide(CFG, {}, stats, GOOD)[0] == "ask"  # henüz karar yok
    for i in range(30):
        policy.record(stats, {"id": str(i), "source_keys": ["OpenAI"]}, ok=True)
    assert policy.decide(CFG, {}, stats, GOOD)[0] == "auto"
    # başka, güvenilmeyen kaynak → sor
    assert policy.decide(CFG, {}, stats, {**GOOD, "source_keys": ["OpenAI", "Yeni"]})[0] == "ask"
    # uyarı işareti → her zaman sor
    assert policy.decide(CFG, {}, stats, {**GOOD, "flags": ["iddia"]})[0] == "ask"
    assert policy.decide(CFG, {}, stats, {**GOOD, "confidence": "orta"})[0] == "ask"
    # manuel mod
    assert policy.decide(CFG, {"mode_override": "manuel"}, stats, GOOD)[0] == "ask"
    # çok ret → genel oran düşer → sor
    for i in range(10):
        policy.record(stats, {"id": f"r{i}", "source_keys": ["OpenAI"]}, ok=False)
    assert policy.decide(CFG, {}, stats, GOOD)[0] == "ask"


def test_parse_rss_and_atom():
    rss = b"""<?xml version="1.0"?><rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel>
      <item><title>A &amp; B</title><link>https://x.com/a</link><description>short</description>
      <content:encoded><![CDATA[<p>Long content here that is definitely more than eighty characters long for testing purposes ok.</p>]]></content:encoded>
      <pubDate>Tue, 22 Sep 2026 21:00:00 GMT</pubDate></item></channel></rss>"""
    items = parse_feed(rss)
    assert items[0]["title"] == "A & B" and items[0]["link"] == "https://x.com/a"
    assert "Long content" in items[0]["summary"] and items[0]["published"].year == 2026
    atom = b"""<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>T</title>
      <link rel="alternate" href="https://y.com/t"/><updated>2026-09-22T10:00:00Z</updated><summary>S</summary></entry></feed>"""
    a = parse_feed(atom)
    assert a[0]["link"] == "https://y.com/t" and a[0]["published"].hour == 10


def test_html_listing():
    html = b'<a href="/news/foo-bar"><h3>Foo bar announcement here</h3></a><a href="/careers">Careers page link</a>'
    out = parse_html_listing(html, "https://www.anthropic.com/news", r"^/news/[a-z0-9-]+/?$")
    assert len(out) == 1 and out[0]["link"] == "https://www.anthropic.com/news/foo-bar"


def test_body_is_safe():
    html = render_body('Metin <script>alert(1)</script> [x](javascript:alert(1))\n\n**Neden önemli?** Çünkü.')
    assert "<script>" not in html and "javascript:" not in html
    assert '<aside class="why">' in html


def test_misc():
    assert slugify("Şirket İstanbul'da yapay zekâ ofisi açtı!") == "sirket-istanbul-da-yapay-zeka-ofisi-acti"
    assert normalize_url("https://www.x.com/a/?utm_source=rss&id=3") == "https://x.com/a?id=3"
    assert publisher_name("https://www.bloomberg.com/graphics/x") == "Bloomberg"
    assert md_to_tg("**a** <b>") == "<b>a</b> &lt;b&gt;"


def test_image_helpers():
    import base64
    from haberbot.visuals import _find_image_b64, image_prompt
    fake = base64.b64encode(b"x" * 2000).decode()
    gc = {"candidates": [{"content": {"parts": [{"text": "ok"}, {"inlineData": {"mimeType": "image/png", "data": fake}}]}}]}
    assert _find_image_b64(gc) == fake
    inter = {"outputs": [{"type": "image", "mime_type": "image/jpeg", "data": fake}]}
    assert _find_image_b64(inter) == fake
    assert _find_image_b64({"candidates": [{"finishReason": "SAFETY"}]}) is None
    pr = image_prompt({"category": "sirketler", "visual_style": "macro", "visual_scene": "glass cubes"})
    assert "glass cubes" in pr and "no text" in pr.lower() and "macro" in pr


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
