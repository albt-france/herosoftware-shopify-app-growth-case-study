"""Fetch a public URL once through polite.get and cache the body in data/raw/ (never re-fetched if cached)."""
import hashlib
import re
from pathlib import Path

import polite

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"


def cached(url: str, delay: float = polite.MIN_DELAY_S) -> str | None:
    RAW.mkdir(parents=True, exist_ok=True)
    name = re.sub(r"[^A-Za-z0-9]+", "_", url.split("//", 1)[-1])[:120] + "_" + hashlib.md5(url.encode()).hexdigest()[:6]
    f = RAW / (name + ".html")
    if f.exists():
        return f.read_text(encoding="utf-8")
    r = polite.get(url, delay=delay)
    if r is None or r.status_code != 200:
        print(f"[skip] {url} -> {None if r is None else r.status_code}")
        return None
    f.write_text(r.text, encoding="utf-8")
    return r.text
