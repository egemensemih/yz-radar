"""Test için örnek kaynak dosyaları üretir (tarihler 'şimdi'ye göre ayarlanır)."""
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).parent / "fixtures"
NOW = datetime.now(timezone.utc)


def rss(title, items):
    body = []
    for t, link, desc, hours_ago in items:
        d = format_datetime(NOW - timedelta(hours=hours_ago))
        body.append(f"<item><title>{escape(t)}</title><link>{escape(link)}</link>"
                    f"<description>{escape(desc)}</description><pubDate>{d}</pubDate></item>")
    return (f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{escape(title)}</title>'
            + "".join(body) + "</channel></rss>")


def atom(title, items):
    body = []
    for t, link, desc, hours_ago in items:
        d = (NOW - timedelta(hours=hours_ago)).isoformat()
        body.append(f'<entry><title>{escape(t)}</title><link rel="alternate" href="{escape(link)}"/>'
                    f"<summary>{escape(desc)}</summary><updated>{d}</updated></entry>")
    return (f'<?xml version="1.0" encoding="utf-8"?><feed xmlns="http://www.w3.org/2005/Atom"><title>{escape(title)}</title>'
            + "".join(body) + "</feed>")


FILES = {
    "openai.xml": rss("OpenAI News", [
        ("Introducing GPT-6 Sol and Luna", "https://openai.com/index/introducing-gpt-6-sol-and-luna",
         "Meet GPT-6 Sol and Luna, two models that bring frontier intelligence to everyday work with different balances of capability and cost.", 14),
        ("Better prompt caching for GPT-6", "https://openai.com/index/better-prompt-caching-for-gpt-6",
         "Learn how GPT-6 improves prompt caching with higher cache hit rates, new diagnostics, explicit breakpoints.", 11),
        ("An old announcement", "https://openai.com/index/old", "Old item", 200),
    ]),
    "techcrunch.xml": rss("TechCrunch AI", [
        ("Snorkel AI triples valuation to $3.5B as demand for AI training data booms",
         "https://techcrunch.com/2026/09/22/snorkel-ai-triples-valuation-to-3-5b/?utm_source=rss",
         "The seven-year-old startup has raised a $350 million Series E to fuel its data-as-a-service approach.", 10),
        ("Qualcomm launches two new smartphone chips with emphasis on AI",
         "https://techcrunch.com/2026/09/22/qualcomm-launches-two-new-smartphone-chips/",
         "Qualcomm said that its new top chip can run 30B mixture-of-expert model locally.", 12),
        ("TechCrunch Founder Summit's agenda revealed",
         "https://techcrunch.com/2026/09/22/founder-summit-agenda/", "Event promo.", 9),
        ("OpenAI unveils GPT-6 Sol and Luna models", "https://techcrunch.com/2026/09/22/openai-gpt-6-sol-luna/",
         "OpenAI released two new GPT-6 models on Tuesday.", 13),
    ]),
    "hugging-face.xml": rss("Hugging Face - Blog", [
        ("Transformers now runs llama.cpp quants", "https://huggingface.co/blog/transformers-llama-cpp-quants", "", 16),
    ]),
    "nvidia.xml": rss("NVIDIA Blog", [
        ("NVIDIA Launches DSX Ready to Qualify Power and Cooling Products for AI Factories",
         "https://blogs.nvidia.com/blog/dsx-ready-ai-factories-power-cooling/", "DSX Ready program.", 30),
    ]),
    "webrazzi.xml": rss("Yapay Zeka - Webrazzi", [
        ("Yapay zeka uygulamaları için bulut altyapısı geliştiren Verda, 189 milyon dolar yatırım aldı",
         "https://webrazzi.com/2026/09/22/verda-189-milyon-dolar-yatirim/", "Verda yatırım aldı.", 17),
    ]),
    "google-deepmind.xml": atom("Google DeepMind", [
        ("SIMA 2: An Agent that Plays, Reasons, and Learns With You in Virtual 3D Worlds",
         "https://deepmind.google/blog/sima-2/", "Introducing SIMA 2.", 400),
    ]),
    "hacker-news.xml": rss("HN", [
        ("Pentagon says overreliance on AI contributed to missile strike",
         "https://www.bloomberg.com/graphics/2026-iran-school-attack/", "Comments", 12),
    ]),
    "anthropic.html": """<html><body><main>
      <a href="/news/accenture-embedded-evaluation"><h3>Partnering with Accenture on embedded evaluation</h3><span>Sep 18, 2026</span></a>
      <a href="/news/life-sciences-verification-program"><h3>Introducing the Life Sciences Verification Program</h3></a>
      <a href="/careers">Careers</a>
    </main></body></html>""",
}

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, content in FILES.items():
        (OUT / name).write_text(content, encoding="utf-8")
    print("fixtures:", ", ".join(FILES))
