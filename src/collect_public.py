"""Collect the public data used in the case study (one polite pass, cached in data/raw/).

Sources (all public, no login, no key):
  1. Shopify App Store listings of the 4 HeroSoftware apps (JSON-LD + visible fields)
  2. Public reviews of the 4 apps (only: review id, app, date, stars, country, tenure, reply date)
  3. Category pages (all pages of each app's primary category, default order, logged-out view)
  4. Wayback Machine snapshots of the top-5 competitors' listings (ratingCount over time)
  5. Eurostat isoc_ec_eseln2 (enterprises selling online to consumers, 2024)
  6. German nation-wide public holidays, computed locally (date.nager.at disallows bots in robots.txt)
  7. ECB EUR/USD monthly reference rates (data-api.ecb.europa.eu)
  8. Company and job facts (hero.software, legal notice, join.com): numbers and dates only, no names

Privacy rules applied at ingestion: the shop name, the review text and the developer reply text (and
its signature) are never stored. robots.txt of apps.shopify.com disallows '*q=*', so no search-result
page is ever requested. At most one request every 1.5 s (2 s for the Wayback Machine).

Run:  python src/collect_public.py
If data/raw/ is empty and data/public/*.csv exist (the delivered cache), the script re-uses them.
"""
import html
import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cache_fetch import RAW, cached  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "data" / "public"
APPS = {"addresshero": "AddressHero", "paymenthero": "PaymentHero", "discounthero": "DiscountHero",
        "post-purchase-upsell-hero": "Post Purchase Upsell Hero"}
STORE = "https://apps.shopify.com"
COLLECTED = datetime.now().strftime("%Y-%m-%d")
DATE_RE = re.compile(r"^(?:Edited )?(January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}$")


def lines_of(fragment: str) -> list[str]:
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", fragment, flags=re.S)
    t = html.unescape(re.sub(r"<[^>]+>", "\n", t))
    return [x.strip() for x in t.split("\n") if x.strip()]


def after(lines, key, n=1):
    for i, x in enumerate(lines):
        if x == key:
            return lines[i + 1:i + 1 + n]
    return []


def pdate(s):
    return datetime.strptime(s.replace("Edited ", ""), "%B %d, %Y").strftime("%Y-%m-%d")


# ---------- 1. listings ----------
def parse_listing(handle: str, page: str) -> dict:
    ld = {}
    for blob in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S):
        d = json.loads(blob)
        if d.get("@type") == "SoftwareApplication":
            ld = d
    L = lines_of(page)
    cats = []
    for u in re.findall(r'href="https://apps.shopify.com/categories/([^"/?]+)/all\?surface_detail=[^"]*surface_type=app_details', page):
        if u not in cats:
            cats.append(u)
    desc = (ld.get("description") or "").strip()
    german = bool(re.search(r"\b(der|die|das|und|mit|für|deine|dein|Kunden|Versand)\b", desc))
    works = []
    for i, x in enumerate(L):
        if x == "Works with":
            for y in L[i + 1:i + 12]:
                if y in ("Categories", "Show features", "Pricing", "Rating", "Developer") or len(y) > 40:
                    break
                works.append(y)
            break
    return {
        "handle": handle, "short_name": APPS[handle], "listing_name": ld.get("name"),
        "rating": float(ld.get("aggregateRating", {}).get("ratingValue", "nan")),
        "rating_count": int(ld.get("aggregateRating", {}).get("ratingCount", 0)),
        "launched": pdate(after(L, "Launched")[0]) if after(L, "Launched") else None,
        "pricing": (after(L, "Pricing") or [""])[0],
        "categories_display": " | ".join(after(L, "Categories", 1)),
        "category_slugs": "|".join(cats),
        "languages": (after(L, "Languages") or [""])[0],
        "works_with": "|".join(works),
        "built_for_shopify": "Built for Shopify" in L,
        "description_len": len(desc), "description_language": "empty" if not desc else ("de" if german else "en"),
        "n_screenshots": len(set(re.findall(r"app-store/listing_images/[^/]+/desktop_screenshot/[^\"?]+", page))),
        "collected": COLLECTED,
    }


# ---------- 2. reviews ----------
def parse_reviews(handle: str, page: str) -> list[dict]:
    out = []
    starts = [m.start() for m in re.finditer(r'data-review-content-id="', page)]
    for k, s in enumerate(starts):
        blk = page[s:starts[k + 1] if k + 1 < len(starts) else s + 40000]
        rid = re.match(r'data-review-content-id="(\d+)"', blk).group(1)
        stars = re.search(r'aria-label="(\d) out of 5 stars"', blk)
        L = lines_of(blk)
        use = [i for i, x in enumerate(L) if x.endswith("using the app")]
        rep = [i for i, x in enumerate(L) if x.endswith(" replied")]
        stop = rep[0] if rep else len(L)                                # dates after 'replied' are reply dates
        dates = [i for i, x in enumerate(L[:stop]) if DATE_RE.match(x) and not x.startswith("Edited")] or                 [i for i, x in enumerate(L[:stop]) if DATE_RE.match(x)]  # 'Edited <date>' only when no original date
        rec = {"review_id": rid, "app": APPS[handle], "handle": handle,
               "review_date": pdate(L[dates[0]]) if dates else None,
               "date_is_edited": bool(dates) and L[dates[0]].startswith("Edited"),   # only the edit date is shown
               "stars": int(stars.group(1)) if stars else None,
               "country": L[use[0] - 1] if use else None,      # line before tenure; shop name (2 lines up) is NOT kept
               "tenure": L[use[0]] if use else None,
               "reply_date": pdate(L[rep[0] + 1]) if rep and rep[0] + 1 < len(L) and DATE_RE.match(L[rep[0] + 1]) else None}
        out.append(rec)
    return out


def tenure_days(t):
    if not isinstance(t, str):
        return None
    m = re.search(r"(About |Almost |Over )?(\d+|a|an|one) (minute|hour|day|week|month|year)s?", t, re.I)
    if not m:
        return None
    n = 1 if m.group(2).lower() in ("a", "an", "one") else int(m.group(2))
    return n * {"minute": 0, "hour": 0, "day": 1, "week": 7, "month": 30, "year": 365}[m.group(3).lower()]


# ---------- 3. categories ----------
def parse_category(slug: str, page: str, page_no: int) -> list[dict]:
    rows = []
    starts = [m.start() for m in re.finditer(r'data-app-card-handle-value="', page)]
    for k, s in enumerate(starts):
        blk = page[s:starts[k + 1] if k + 1 < len(starts) else s + 15000]
        h = re.match(r'data-app-card-handle-value="([^"]+)"', blk).group(1)
        name = re.search(r'data-app-card-name-value="([^"]*)"', blk)
        pos = re.search(r'data-app-card-intra-position-value="(\d+)"', blk)
        L = lines_of(blk[blk.find(">") + 1:])
        rating = next((float(x) for i, x in enumerate(L[:-1]) if re.fullmatch(r"\d\.\d", x) and L[i + 1].startswith("out of 5")), None)
        tot = next((int(re.sub(r"\D", "", x)) for x in L if x.endswith("total reviews")), 0)
        price = next((L[i + 1] for i, x in enumerate(L[:-1]) if x == "•"), None)
        is_ad = bool(re.search(r"surface_type=(ad|search_ad)|>\s*Ad\s*<", blk))
        rows.append({"category": slug, "page": page_no, "intra_position": int(pos.group(1)) if pos else None,
                     "handle": h, "name": html.unescape(name.group(1)) if name else None, "rating": rating,
                     "total_reviews": tot, "price_label": price, "free_plan": bool(price and "Free plan" in price),
                     "is_ad": is_ad, "is_herosoftware": h in APPS, "collected": COLLECTED})
    return rows


def collect_category(slug: str) -> pd.DataFrame:
    first = cached(f"{STORE}/categories/{slug}/all?page=1")
    if first is None:
        return pd.DataFrame()
    m = re.search(r"([\d,]+) apps", first)
    n_apps = int(m.group(1).replace(",", "")) if m else 24
    rows = parse_category(slug, first, 1)
    for p in range(2, math.ceil(n_apps / 24) + 1):
        pg = cached(f"{STORE}/categories/{slug}/all?page={p}")
        if pg:
            rows += parse_category(slug, pg, p)
    df = pd.DataFrame(rows).drop_duplicates("handle").reset_index(drop=True)
    df["position"] = range(1, len(df) + 1)
    df["n_apps_stated"] = n_apps
    return df


# ---------- 4. Wayback ----------
def wayback(handle: str, max_points: int = 8) -> list[dict]:
    cdx = cached(f"https://web.archive.org/cdx/search/cdx?url=apps.shopify.com/{handle}&output=json"
                 f"&filter=statuscode:200&collapse=timestamp:6", delay=2.0)
    if not cdx:
        return []
    rows = json.loads(cdx)[1:] if cdx.strip().startswith("[") else []
    stamps = [r[1] for r in rows]
    if len(stamps) > max_points:  # evenly spaced, always keep first and last
        idx = sorted({round(i * (len(stamps) - 1) / (max_points - 1)) for i in range(max_points)})
        stamps = [stamps[i] for i in idx]
    out = []
    for ts in stamps:
        pg = cached(f"https://web.archive.org/web/{ts}/https://apps.shopify.com/{handle}", delay=2.0)
        if not pg:
            continue
        m = re.search(r'"ratingCount"\s*:\s*"?(\d+)', pg)
        if not m:  # no JSON-LD in this snapshot: skip the point
            continue
        out.append({"handle": handle, "snapshot": f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}", "rating_count": int(m.group(1))})
    return out


# ---------- 5-7. Eurostat, holidays, company ----------
def eurostat() -> pd.DataFrame:
    url = ("https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/isoc_ec_eseln2?format=JSON&lang=EN"
           "&geo=DE&geo=AT&geo=FR&geo=IT&geo=ES&geo=NL&geo=PL&geo=SE&time=2024"
           "&indic_is=E_AWS_B2C&unit=PC_ENT&size_emp=GE10&nace_r2=C10-S951_X_K")
    d = json.loads(cached(url))
    ids, sizes = d["id"], d["size"]
    strides = [math.prod(sizes[i + 1:]) for i in range(len(sizes))]
    geo_idx = d["dimension"]["geo"]["category"]["index"]
    gpos = ids.index("geo")
    rows = []
    for geo, gi in geo_idx.items():
        flat = str(gi * strides[gpos])  # every other dimension has size 1 after filtering
        rows.append({"geo": geo, "year": 2024, "pct_enterprises_selling_online_b2c": d["value"].get(flat),
                     "source": "Eurostat isoc_ec_eseln2 (E_AWS_B2C, PC_ENT, GE10, C10-S951_X_K)", "collected": COLLECTED})
    return pd.DataFrame(rows)


def easter(y: int) -> datetime:
    a, b, c = y % 19, y // 100, y % 100
    d, e = b // 4, b % 4
    g = (8 * b + 13) // 25
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 19 * l_) // 433
    return datetime(y, (h + l_ - 7 * m + 90) // 25, (h + l_ - 7 * m + 33 * ((h + l_ - 7 * m + 90) // 25) + 19) % 32)


def holidays() -> pd.DataFrame:
    """Nation-wide German public holidays, computed locally (date.nager.at disallows automated clients in robots.txt)."""
    from datetime import timedelta
    rows = []
    for y in (2025, 2026):
        e = easter(y)
        fixed = {f"{y}-01-01": "New Year's Day", f"{y}-05-01": "Labour Day", f"{y}-10-03": "German Unity Day",
                 f"{y}-12-25": "Christmas Day", f"{y}-12-26": "St. Stephen's Day"}
        moving = {e - timedelta(2): "Good Friday", e + timedelta(1): "Easter Monday",
                  e + timedelta(39): "Ascension Day", e + timedelta(50): "Whit Monday"}
        rows += [{"date": k, "name": v} for k, v in fixed.items()]
        rows += [{"date": k.strftime("%Y-%m-%d"), "name": v} for k, v in moving.items()]
    return pd.DataFrame(rows).sort_values("date")


def ecb_fx() -> pd.DataFrame:
    """ECB reference rate USD per EUR, monthly average (used to convert simulated USD prices)."""
    txt = cached("https://data-api.ecb.europa.eu/service/data/EXR/M.USD.EUR.SP00.A?format=csvdata"
                 "&startPeriod=2025-11&endPeriod=2026-10")
    if not txt:
        return pd.DataFrame()
    from io import StringIO
    d = pd.read_csv(StringIO(txt))
    return d.rename(columns={"TIME_PERIOD": "month", "OBS_VALUE": "usd_per_eur"})[["month", "usd_per_eur"]]


def company_facts() -> dict:
    """Numbers and dates only. Person names on these pages are never parsed or stored."""
    facts = {"collected": COLLECTED}
    legal = cached("https://hero.software/legal-notice") or ""
    m = re.search(r"HRB\s*\d+", legal)
    facts["register"] = ("Amtsgericht Wiesbaden, " + m.group(0)) if m else None
    facts["city"] = "Idstein (Hesse), Germany" if "Idstein" in legal else None
    job = cached("https://join.com/companies/hero1095/16942436-growth-marketer-in-100-remote") or ""
    if "__NEXT_DATA__" in job:
        for k in ("createdAt", "updatedAt"):
            mm = re.search(rf'"{k}"\s*:\s*"(\d{{4}}-\d\d-\d\d)T', job)   # first dated value = this job
            facts[f"job_{k}"] = mm.group(1) if mm else None
        for k in ("remoteType", "employmentType"):
            mm = re.search(rf'"{k}"\s*:\s*"([A-Z_]+)"', job)
            facts[f"job_{k}"] = mm.group(1) if mm else None
        lo = re.search(r'"salaryAmountFrom"\s*:\s*\{"amount"\s*:\s*(\d+)', job)
        hi = re.search(r'"salaryAmountTo"\s*:\s*\{"amount"\s*:\s*(\d+)', job)
        facts["job_salary_eur_per_year"] = f"{int(lo.group(1)) // 100}-{int(hi.group(1)) // 100}" if lo and hi else None
        facts["job_mentions_3500_merchants"] = "3.500" in job
    return facts


def main():
    PUB.mkdir(parents=True, exist_ok=True)
    have_raw = any(p.suffix == ".html" for p in RAW.glob("*")) if RAW.exists() else False
    if not have_raw and (PUB / "reviews_public.csv").exists():
        print("data/raw/ is empty: using the delivered public CSVs in data/public/ (no request sent).")
        return
    listings = [parse_listing(h, cached(f"{STORE}/{h}")) for h in APPS]
    lst = pd.DataFrame(listings)
    lst.to_csv(PUB / "listings.csv", index=False)

    revs = []
    for h in APPS:
        n_pages = math.ceil(int(lst.loc[lst.handle == h, "rating_count"].iloc[0]) / 10)
        for p in range(1, n_pages + 1):
            pg = cached(f"{STORE}/{h}/reviews?sort_by=newest&page={p}")
            if pg:
                revs += parse_reviews(h, pg)
    rv = pd.DataFrame(revs).drop_duplicates("review_id")
    rv["tenure_days"] = rv["tenure"].map(tenure_days)
    rv["collected"] = COLLECTED
    rv.to_csv(PUB / "reviews_public.csv", index=False)
    print(f"reviews: {len(rv)} (listing sum {lst.rating_count.sum()})")

    cats = []
    primary = {h: s.split("|")[0] for h, s in zip(lst.handle, lst.category_slugs) if s}
    for h, slug in primary.items():
        df = collect_category(slug)
        df["primary_of"] = APPS[h]
        cats.append(df)
        print(f"category {slug}: {len(df)} apps")
    cat = pd.concat(cats, ignore_index=True)
    cat.to_csv(PUB / "categories.csv", index=False)

    wb = []
    for slug, g in (cat.groupby("category") if not (PUB / "wayback_rating_counts.csv").exists() else []):
        top = g[~g.is_herosoftware].nsmallest(5, "position").handle.tolist()
        for h in top + [x for x in g[g.is_herosoftware].handle]:
            wb += [dict(r, category=slug) for r in wayback(h)]
    if wb:  # single pass: the Wayback step never re-runs once its CSV exists (no retry loop)
        pd.DataFrame(wb).to_csv(PUB / "wayback_rating_counts.csv", index=False)

    eurostat().to_csv(PUB / "eurostat_b2c_online_sales.csv", index=False)
    holidays().to_csv(PUB / "holidays_de.csv", index=False)
    ecb_fx().to_csv(PUB / "ecb_eurusd_monthly.csv", index=False)
    (PUB / "company_facts.json").write_text(json.dumps(company_facts(), indent=2), encoding="utf-8")
    print("done:", ", ".join(sorted(p.name for p in PUB.glob("*"))))


if __name__ == "__main__":
    main()
