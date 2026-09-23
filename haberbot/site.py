"""Statik web sitesi üretici: content/posts/*.json → _site/"""
from __future__ import annotations

import html as htmlmod
import json
import re
import shutil
from datetime import datetime
from email.utils import format_datetime

import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .config import CATEGORIES, ROOT, Config, category_color, category_label
from .store import Store
from .util import clip, iso, local, log, now_utc, parse_iso, tr_date

ASSET_V = "4"
WHY_RE = re.compile(r"<p><strong>Neden önemli\?</strong>\s*(.*?)</p>", re.S)


def render_body(md: str) -> str:
    safe = htmlmod.escape(md or "", quote=False)
    out = markdown.markdown(safe, extensions=["sane_lists"], output_format="html")
    out = re.sub(r'href="(?!https?://)[^"]*"', 'href="#"', out)
    out = out.replace('<a href="http', '<a rel="noopener" target="_blank" href="http')
    out = WHY_RE.sub(r'<aside class="why"><strong>Neden önemli?</strong><p>\1</p></aside>', out)
    return out


def nobr_hyphen(title: str) -> str:
    """'GPT-6' gibi kısa tireli sözcüklerin satır sonunda bölünmesini engelle."""
    return re.sub(r"(?<=\w)-(?=\w)", "\u2011", title or "")


def reading_minutes(text: str) -> int:
    return max(1, round(len((text or "").split()) / 180))


class SiteBuilder:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.base = cfg.base_path
        self.env = Environment(
            loader=FileSystemLoader(str(ROOT / "templates")),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True, lstrip_blocks=True,
        )

    def _post_view(self, p: dict) -> dict:
        cfg, b = self.cfg, self.base
        pub = p.get("published_at")
        dt = parse_iso(pub) or now_utc()
        ext = "webp" if (cfg.images_dir / f"{p['id']}.webp").exists() else "jpg"
        has_og = (cfg.images_dir / f"{p['id']}-og.jpg").exists()
        return {
            **p,
            "url": f"{b}/haber/{p['slug']}/",
            "title_disp": nobr_hyphen(p.get("title", "")),
            "short_disp": nobr_hyphen(p.get("short_title") or p.get("title", "")),
            "kicker_disp": p.get("kicker") or category_label(p.get("category", "")),
            "hero_stat": (p.get("hero_stat") or "").strip(),
            "hero_stat_label": (p.get("hero_stat_label") or "").strip(),
            "ai_image": (p.get("image") or {}).get("source") == "ai",
            "img_alt": "Habere ait temsili görsel",
            "abs_url": cfg.post_url(p["slug"]),
            "img": f"{b}/img/{p['id']}.{ext}",
            "abs_img": f"{cfg.site_url}/img/{p['id']}.{ext}",
            "abs_og": f"{cfg.site_url}/img/{p['id']}-og.jpg" if has_og else f"{cfg.site_url}/static/og-default.jpg",
            "date_str": tr_date(pub, cfg.tz),
            "date_short": tr_date(pub, cfg.tz, with_time=False),
            "iso": dt.isoformat(),
            "rfc822": format_datetime(dt),
            "cat_label": category_label(p.get("category", "")),
            "cat_color": category_color(p.get("category", "")),
            "cat_url": f"{b}/kategori/{p.get('category', 'urunler')}/",
            "credits": list(dict.fromkeys(s["name"] for s in p.get("sources", []))),
            "minutes": reading_minutes(p.get("body", "")),
            "body_html": render_body(p.get("body", "")),
            "updated_str": tr_date(p.get("updated_at"), cfg.tz) if p.get("updated_at") else "",
        }

    def _write(self, rel: str, content: str) -> None:
        path = self.cfg.out_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def build(self) -> int:
        cfg, b = self.cfg, self.base
        out = cfg.out_dir
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)
        store = Store(cfg)
        posts = [self._post_view(p) for p in store.posts()]
        counts = {k: 0 for k in CATEGORIES}
        for p in posts:
            counts[p["category"]] = counts.get(p["category"], 0) + 1
        cats = [{"slug": k, "label": v[0], "color": v[1], "count": counts.get(k, 0),
                 "url": f"{b}/kategori/{k}/"} for k, v in CATEGORIES.items()]

        now_l = local(now_utc(), cfg.tz)
        site = {
            **cfg.site,
            "base": b,
            "url": cfg.site_url,
            "year": now_l.year,
            "categories": cats,
            "nav_categories": [c for c in cats if c["count"] > 0] or cats[:6],
            "built": tr_date(now_utc(), cfg.tz),
            "built_iso": iso(now_utc()),
            "today_count": sum(1 for p in posts if (local(p["published_at"], cfg.tz) or now_l).date() == now_l.date()),
            "og_image": f"{cfg.site_url}/static/og-default.jpg",
            "asset_v": ASSET_V,
        }
        ctx = {"site": site}

        # statik dosyalar ve görseller
        shutil.copytree(ROOT / "static", out / "static")
        (out / "img").mkdir()
        for p in posts:
            for name in (f"{p['id']}.webp", f"{p['id']}.jpg", f"{p['id']}-og.jpg"):
                src = cfg.images_dir / name
                if src.exists():
                    shutil.copy2(src, out / "img" / name)

        # ana sayfa + sayfalama
        per = int(cfg.site.get("posts_per_page", 18))
        pages = max(1, (len(posts) + per - 1) // per)
        for n in range(1, pages + 1):
            chunk = posts[(n - 1) * per: n * per]
            rel = "index.html" if n == 1 else f"sayfa/{n}/index.html"
            self._write(rel, self.env.get_template("index.html").render(
                **ctx, posts=chunk, page=n, pages=pages,
                prev_url=(f"{b}/" if n == 2 else f"{b}/sayfa/{n - 1}/") if n > 1 else None,
                next_url=f"{b}/sayfa/{n + 1}/" if n < pages else None,
                canonical=cfg.site_url + ("/" if n == 1 else f"/sayfa/{n}/")))

        # haber sayfaları
        for p in posts:
            related = [q for q in posts if q["category"] == p["category"] and q["id"] != p["id"]][:6]
            if len(related) < 8:
                related += [q for q in posts if q["id"] != p["id"] and q not in related][: 8 - len(related)]
            self._write(f"haber/{p['slug']}/index.html", self.env.get_template("article.html").render(
                **ctx, post=p, related=related, canonical=p["abs_url"]))

        # kategoriler
        for c in cats:
            cp = [p for p in posts if p["category"] == c["slug"]][:120]
            self._write(f"kategori/{c['slug']}/index.html", self.env.get_template("category.html").render(
                **ctx, cat=c, posts=cp, canonical=f"{cfg.site_url}/kategori/{c['slug']}/"))

        self._write("hakkinda/index.html", self.env.get_template("about.html").render(
            **ctx, canonical=f"{cfg.site_url}/hakkinda/",
            sources=[s for s in cfg.sources]))
        self._write("404.html", self.env.get_template("404.html").render(**ctx, canonical=cfg.site_url + "/"))

        # besleme, site haritası, robots, json
        self._write("feed.xml", self.env.get_template("feed.xml").render(
            **ctx, posts=posts[:40], now_rfc=format_datetime(now_utc())))
        self._write("sitemap.xml", self.env.get_template("sitemap.xml").render(**ctx, posts=posts))
        self._write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {cfg.site_url}/sitemap.xml\n")
        latest = [{"id": p["id"], "title": p["title"], "summary": p["summary"], "url": p["abs_url"],
                   "image": p["abs_img"], "og_image": p["abs_og"], "category": p["category"], "published_at": p["published_at"],
                   "sources": [{"name": s["name"], "url": s["url"]} for s in p.get("sources", [])]}
                  for p in posts[:50]]
        self._write("api/latest.json", json.dumps(latest, ensure_ascii=False, indent=1))
        (out / ".nojekyll").write_text("")
        log.info("Site üretildi: %d haber, %d sayfa → %s", len(posts), pages, out)
        return len(posts)
