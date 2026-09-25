"""Kullanım:
    python -m haberbot run      # bir tur çalış (GitHub Actions bunu çağırır)
    python -m haberbot build    # sadece siteyi üret (_site/)
    python -m haberbot check    # ayarları ve bağlantıları kontrol et
"""
from __future__ import annotations

import os
import sys

from .app import App, write_github_output
from .config import load_config
from .site import SiteBuilder
from .util import hours_since, iso, log, now_utc, setup_logging


def main(argv: list[str]) -> int:
    setup_logging("-v" in argv)
    cmd = argv[0] if argv and not argv[0].startswith("-") else "run"
    cfg = load_config()
    log.info("Site adresi: %s", cfg.site_url)

    if cmd == "build":
        SiteBuilder(cfg).build()
        write_github_output("site_changed", "true")
        return 0

    if cmd == "check":
        return check(cfg)

    if cmd == "run":
        app = App(cfg)
        changed = app.run()
        in_ci = os.environ.get("GITHUB_ACTIONS") == "true"
        stale = hours_since(app.state.get("last_build")) >= 1  # "bugün N gelişme" gibi bilgiler saatte bir tazelensin
        if changed or cfg.force_build or stale or (not in_ci and not (cfg.out_dir / "index.html").exists()):
            SiteBuilder(cfg).build()
            app.state["last_build"] = iso(now_utc())
            app.store.save()
            changed = True
        write_github_output("site_changed", "true" if changed else "false")
        return 0

    print(__doc__)
    return 2


def check(cfg) -> int:
    ok = True
    print(f"Site adresi       : {cfg.site_url}")
    print(f"Kaynak sayısı     : {len(cfg.sources)}")
    print(f"GEMINI_API_KEY    : {'VAR' if cfg.google_key else 'YOK ✗'}")
    if cfg.anthropic_key:
        print("ANTHROPIC_API_KEY : VAR (isteğe bağlı)")
    print(f"TELEGRAM_BOT_TOKEN: {'VAR' if cfg.telegram_token else 'YOK ✗'}")
    print(f"TELEGRAM_CHAT_ID  : {cfg.telegram_chat_id or 'YOK (bota /start yaz)'}")
    ok &= bool((cfg.google_key or cfg.anthropic_key) and cfg.telegram_token and cfg.telegram_chat_id)
    if cfg.telegram_token and cfg.telegram_chat_id:
        from .telegram import Telegram, TelegramError
        try:
            Telegram(cfg.telegram_token).send_message(cfg.telegram_chat_id, "✅ Bağlantı testi başarılı. Sistem hazır.")
            print("Telegram          : mesaj gönderildi ✓")
        except TelegramError as e:
            print(f"Telegram          : HATA ✗ {e}")
            ok = False
    from .llm import LLMError, make_llm
    llm = make_llm(cfg)
    if llm:
        try:
            r = llm.json(cfg.get("ai", "triage_model"), "Reply in JSON.", "Say ok.",
                         {"type": "object", "properties": {"ok": {"type": "boolean"}},
                          "required": ["ok"], "additionalProperties": False}, max_tokens=200)
            print(f"Yapay zeka        : çalışıyor ✓ {r}")
        except LLMError as e:
            print(f"Yapay zeka        : HATA ✗ {e}")
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
