"""Ayarların yüklenmesi ve ortam değişkenleri."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

import yaml

ROOT = Path(__file__).resolve().parent.parent

# Sabit kategori listesi: slug → (etiket, renk)
CATEGORIES: dict[str, tuple[str, str]] = {
    "modeller":    ("Modeller",            "#7C5CFF"),
    "urunler":     ("Ürün & Araçlar",      "#12B5A6"),
    "arastirma":   ("Araştırma",           "#3B82F6"),
    "sirketler":   ("Şirketler & Yatırım", "#F59E0B"),
    "politika":    ("Politika & Güvenlik", "#EF4444"),
    "donanim":     ("Donanım & Altyapı",   "#22C55E"),
    "acik-kaynak": ("Açık Kaynak",         "#EC4899"),
    "turkiye":     ("Türkiye",             "#E11D48"),
}
DEFAULT_CATEGORY = "urunler"

# Kategori sayfaları için arama motoru başlığı ve tanıtım metni
CATEGORY_SEO: dict[str, tuple[str, str]] = {
    "modeller": ("Yapay zeka modelleri haberleri",
                 "GPT, Gemini, Claude, Llama ve diğer büyük dil modellerindeki yeni sürümler, yetenekler ve karşılaştırmalar."),
    "urunler": ("Yapay zeka ürünleri ve araçları",
                "ChatGPT, Gemini ve Copilot gibi yapay zeka uygulamalarındaki yeni özellikler, geliştirici araçları ve API güncellemeleri."),
    "arastirma": ("Yapay zeka araştırmaları",
                  "Yapay zeka alanındaki yeni bilimsel makaleler, deney sonuçları ve teknik buluşlar."),
    "sirketler": ("Yapay zeka şirketleri ve yatırımlar",
                  "OpenAI, Anthropic, Google, NVIDIA ve yapay zeka girişimlerinin yatırım turları, satın almaları ve iş stratejileri."),
    "politika": ("Yapay zeka regülasyonu ve güvenliği",
                 "Yapay zeka yasaları, davalar, güvenlik ve etik tartışmaları ile hükümetlerin aldığı kararlar."),
    "donanim": ("Yapay zeka çipleri ve altyapısı",
                "GPU'lar, yapay zeka çipleri, veri merkezleri ve enerji altyapısındaki gelişmeler."),
    "acik-kaynak": ("Açık kaynak yapay zeka",
                    "Açık ağırlıklı modeller, açık kaynak yapay zeka araçları ve topluluk projeleri."),
    "turkiye": ("Türkiye'de yapay zeka",
                "Türkiye'deki yapay zeka girişimleri, yatırımlar, kamu politikaları ve yerli projeler."),
}


def category_seo(slug: str) -> tuple[str, str]:
    return CATEGORY_SEO.get(slug, (category_label(slug), ""))


def indexnow_key(site_url: str) -> str:
    """IndexNow (Bing/Yandex anlık bildirim) anahtarı: site adresinden türetilir, sitede /<anahtar>.txt olarak durur."""
    import hashlib
    return hashlib.sha1(("yzradar-indexnow:" + site_url).encode()).hexdigest()[:32]


def category_label(slug: str) -> str:
    return CATEGORIES.get(slug, CATEGORIES[DEFAULT_CATEGORY])[0]


def category_color(slug: str) -> str:
    return CATEGORIES.get(slug, CATEGORIES[DEFAULT_CATEGORY])[1]


@dataclass
class Config:
    raw: dict
    root: Path = ROOT
    site_url: str = ""          # https://kullanici.github.io/depo  (sonda / yok)
    base_path: str = ""         # /depo   ya da ""
    anthropic_key: str = ""
    telegram_token: str = ""
    telegram_chat_id: str = ""
    google_key: str = ""
    mock: bool = False
    fixtures_dir: Path | None = None
    force_collect: bool = False
    force_build: bool = False
    extras: dict = field(default_factory=dict)

    # kısa yollar
    def get(self, section: str, key: str, default=None):
        return (self.raw.get(section) or {}).get(key, default)

    @property
    def site(self) -> dict:
        return self.raw.get("site") or {}

    @property
    def tz(self) -> str:
        return self.get("schedule", "timezone", "Europe/Istanbul")

    @property
    def sources(self) -> list[dict]:
        return [s for s in (self.raw.get("sources") or []) if s and s.get("url")]

    # dizinler
    @property
    def data_dir(self) -> Path:
        return self.root / "data"

    @property
    def drafts_dir(self) -> Path:
        return self.root / "data" / "drafts"

    @property
    def posts_dir(self) -> Path:
        return self.root / "content" / "posts"

    @property
    def images_dir(self) -> Path:
        return self.root / "content" / "images"

    @property
    def out_dir(self) -> Path:
        return self.root / "_site"

    def post_url(self, slug: str) -> str:
        return f"{self.site_url}/haber/{slug}/"


def _derive_site_url(cfg_url: str) -> str:
    if cfg_url:
        return cfg_url.rstrip("/")
    env_url = os.environ.get("SITE_URL", "").strip()
    if env_url:
        return env_url.rstrip("/")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if "/" in repo:
        owner, name = repo.split("/", 1)
        owner = owner.lower()
        if name.lower() == f"{owner}.github.io":
            return f"https://{owner}.github.io"
        return f"https://{owner}.github.io/{name}"
    return "http://localhost:8000"


def load_config(path: Path | None = None) -> Config:
    path = path or (ROOT / "config.yaml")
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    site_url = _derive_site_url((raw.get("site") or {}).get("url", "") or "")
    base_path = urlsplit(site_url).path.rstrip("/")
    fixtures = os.environ.get("HABERBOT_FIXTURES")
    return Config(
        raw=raw,
        root=Path(os.environ["HABERBOT_ROOT"]) if os.environ.get("HABERBOT_ROOT") else ROOT,
        site_url=site_url,
        base_path=base_path,
        anthropic_key=os.environ.get("ANTHROPIC_API_KEY", "").strip(),
        telegram_token=os.environ.get("TELEGRAM_BOT_TOKEN", "").strip(),
        telegram_chat_id=os.environ.get("TELEGRAM_CHAT_ID", "").strip(),
        google_key=(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip(),
        mock=os.environ.get("HABERBOT_MOCK", "") == "1",
        fixtures_dir=Path(fixtures) if fixtures else None,
        force_collect=os.environ.get("FORCE_COLLECT", "").lower() == "true",
        force_build=os.environ.get("FORCE_BUILD", "").lower() == "true",
    )
