"""SIMULATED data for a fictional 4-app Shopify portfolio (APP_A..APP_D), seed 42.

Nothing here is HeroSoftware data. The simulation is only *calibrated* on public facts:
country mix of public reviews, listing prices, launch dates, the relative rhythm of the apps,
review timing, German public holidays and Black Friday / Cyber Monday 2025.

Period 2025-11-01 -> 2026-10-31, daily. Timestamps stored in UTC; reports use Europe/Berlin.
Outputs: data/sim/*.parquet (+ data/_hidden_truth.csv, never published).
All assumptions are listed in docs/assumptions.md.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SIM = ROOT / "data" / "sim"
PUB = ROOT / "data" / "public"
rng = np.random.default_rng(42)

START, END = pd.Timestamp("2025-11-01"), pd.Timestamp("2026-10-31")
DAYS = pd.date_range(START, END, freq="D")
APPS = ["APP_A", "APP_B", "APP_C", "APP_D"]
LAUNCH = {"APP_A": "2023-04-04", "APP_B": "2025-05-05", "APP_C": "2025-07-25", "APP_D": "2026-06-19"}
CTRY = ["DE", "AT", "CH", "FR", "IT", "ES", "NL", "PL", "US", "GB", "OTHER"]
DACH = {"DE", "AT", "CH"}
MIX = {  # install share by country (assumption, see docs/assumptions.md)
    "APP_A": [.84, .05, .04, .012, .01, .01, .012, .008, .01, .008, .01],
    "APP_B": [.70, .05, .04, .05, .04, .04, .035, .03, .01, .005, .0],
    "APP_C": [.80, .06, .06, .01, .01, .01, .02, .0, .02, .01, .0],
    "APP_D": [.38, .04, .04, .05, .04, .05, .05, .03, .14, .10, .08],
}
SURF = ["app_store_search", "category_browse", "direct", "partner", "app_store_ads",
        "google_ads", "content", "email", "social"]
SRC_SHARE = {"app_store_search": .40, "category_browse": .22, "direct": .145, "partner": .05, "app_store_ads": 0,
             "google_ads": .065, "content": .06, "email": .02, "social": .04}
CONV = {"app_store_search": .12, "category_browse": .06, "direct": .25, "partner": .30, "app_store_ads": .05,
        "google_ads": .025, "content": .03, "email": .15, "social": .02}   # listing view -> install
MONTH_SEASON = {11: 1.0, 12: .95, 1: 1.0, 2: 1.0, 3: 1.10, 4: 1.15, 5: 1.15, 6: 1.05, 7: .95, 8: .95, 9: 1.05, 10: 1.05}

# hidden events (the truth the analysis has to recover)
TRANSLATION_START, TRANSLATION_LIFT = pd.Timestamp("2026-03-02"), 1.35
ADS_START, ADS_END, ADS_SHARE = pd.Timestamp("2026-04-06"), pd.Timestamp("2026-05-31"), 0.30
BRAND_INCREMENTAL = 0.15
HOLDOUT_START, HOLDOUT_END = pd.Timestamp("2026-08-03"), pd.Timestamp("2026-08-30")
REVIEW_TEST_START, REVIEW_TEST_END = pd.Timestamp("2026-02-01"), pd.Timestamp("2026-04-30")
BFCM_START, BFCM_END, BFCM_LIFT = pd.Timestamp("2025-11-24"), pd.Timestamp("2025-12-01"), 1.70
LINKEDIN_START, LINKEDIN_END = pd.Timestamp("2025-11-24"), pd.Timestamp("2025-12-14")
DUP_DAYS = [pd.Timestamp("2026-07-14"), pd.Timestamp("2026-07-15")]
META_START, META_END = pd.Timestamp("2026-09-14"), pd.Timestamp("2026-10-04")
CROSS_PROMO_START = pd.Timestamp("2026-07-15")


def holidays() -> set:
    f = PUB / "holidays_de.csv"
    return set(pd.to_datetime(pd.read_csv(f)["date"])) if f.exists() else set()


def base_rate(app: str, d: pd.Timestamp, country: str) -> float:
    """Expected organic installs per day for one app x country, before source split."""
    t = (d - START).days / 364
    if app == "APP_A":
        r = 10.5 - 2.0 * t
    elif app == "APP_B":
        r = 11.0
        if country in DACH and d >= pd.Timestamp("2026-03-01"):      # APP_B weakens in DACH from March
            r *= max(0.5, 1 - 0.5 * (d - pd.Timestamp("2026-03-01")).days / 120)
    elif app == "APP_C":
        r = 0.45
    else:
        if d < pd.Timestamp(LAUNCH["APP_D"]):
            return 0.0
        r = min(22.0, 4 + 18 * (d - pd.Timestamp(LAUNCH["APP_D"])).days / 88)
    return r * MIX[app][CTRY.index(country)]


def daily_traffic(hol: set) -> pd.DataFrame:
    rows = []
    for d in DAYS:
        season = MONTH_SEASON[d.month] * (0.75 if d.weekday() >= 5 else 1.07)
        if BFCM_START <= d <= BFCM_END:
            season *= BFCM_LIFT
        for app in APPS:
            for c in CTRY:
                lam = base_rate(app, d, c) * season
                if c == "DE" and d in hol:
                    lam *= 0.6
                if lam == 0:
                    continue
                if app == "APP_B" and c in ("FR", "IT") and d >= TRANSLATION_START:
                    lam *= TRANSLATION_LIFT
                for s in SURF:
                    li = lam * SRC_SHARE[s]
                    if s == "app_store_ads":
                        li = lam * ADS_SHARE if (app == "APP_A" and ADS_START <= d <= ADS_END) else 0
                    if s == "google_ads":
                        brand = li * 0.75
                        if c == "DE" and HOLDOUT_START <= d <= HOLDOUT_END:
                            # brand ads paused in DE: 85% of brand installs come anyway through 'direct'
                            rows.append((d, app, c, "direct", brand * (1 - BRAND_INCREMENTAL), brand * (1 - BRAND_INCREMENTAL) / CONV["direct"], "brand_shift"))
                            brand = 0
                        rows.append((d, app, c, s, brand, brand / CONV[s] if brand else 0, "brand"))
                        rows.append((d, app, c, s, li * 0.25, li * 0.25 / .05, "nonbrand"))
                        continue
                    if li > 0:
                        rows.append((d, app, c, s, li, li / CONV[s], ""))
    df = pd.DataFrame(rows, columns=["date", "app", "country", "surface", "lam_install", "lam_views", "sub"])
    df["listing_views"] = rng.poisson(df["lam_views"].to_numpy())
    p = np.clip(df["lam_install"] / df["lam_views"].replace(0, np.nan), 0, 1).fillna(0)
    df["installs"] = rng.binomial(df["listing_views"].to_numpy(), p.to_numpy())
    return df


def build():
    SIM.mkdir(parents=True, exist_ok=True)
    hol = holidays()
    tr = daily_traffic(hol)
    listing = (tr.groupby(["date", "app", "country", "surface"], as_index=False)["listing_views"].sum())

    # ---------- install events, merchants, subscriptions ----------
    inst = tr[tr.installs > 0].loc[tr.index.repeat(tr.installs)].reset_index(drop=True)
    n = len(inst)
    inst["merchant_id"] = [f"M{i:05d}" for i in range(1, n + 1)]
    # local Berlin time (business-hours weighted), stored in UTC
    hw = np.array([1, 1, 1, 1, 1, 2, 3, 5, 7, 8, 8, 8, 7, 7, 7, 7, 6, 6, 5, 4, 3, 3, 2, 2], float)
    hours = rng.choice(24, n, p=hw / hw.sum())
    local = inst["date"] + pd.to_timedelta(hours, "h") + pd.to_timedelta(rng.integers(0, 3600, n), "s")
    inst["ts_utc"] = local.dt.tz_localize("Europe/Berlin", nonexistent="shift_forward", ambiguous=False).dt.tz_convert("UTC").dt.tz_localize(None)
    camp = {"google_ads": None, "app_store_ads": "CMP004", "social": None, "content": "CMP007", "partner": "CMP008", "email": "CMP009"}
    inst["utm_campaign"] = [("CMP001" if c == "DE" else "CMP002") if (s == "google_ads" and sb == "brand") else
                            ("CMP003" if s == "google_ads" else camp.get(s))
                            for s, sb, c in zip(inst.surface, inst["sub"], inst.country)]
    utm = {"google_ads": "google", "app_store_ads": "shopify_app_store_ads", "social": "linkedin", "content": "blog",
           "partner": "agency", "email": "newsletter"}
    inst["utm_source"] = inst.surface.map(utm)
    # LinkedIn BFCM campaign: social installs in its window carry its campaign id (no true effect)
    m = (inst.surface == "social") & inst.date.between(LINKEDIN_START, LINKEDIN_END)
    inst.loc[m, "utm_campaign"] = "CMP005"
    inst.loc[(inst.surface == "social") & ~m, "utm_source"] = "social_organic"
    inst["source"] = inst.surface

    # merchant attributes
    plan_p = {"APP_C": [0, 0, 0, 1.0]}
    plans = np.array(["Basic", "Shopify", "Advanced", "Plus"])
    inst["shopify_plan"] = [plans[rng.choice(4, p=plan_p.get(a, [.42, .38, .12, .08]))] for a in inst.app]
    inst["gmv_band"] = np.where(inst.shopify_plan == "Plus", ">5M", rng.choice(["<100k", "100k-1M", "1M-5M"], n, p=[.45, .42, .13]))

    # quality: early uninstall, trial, paid
    early_p = np.where(inst.source == "app_store_ads", .41, np.where(inst.source == "partner", .05, .12))
    inst["uninst_48h"] = rng.random(n) < early_p
    base_conv = {("APP_A", True): .265, ("APP_A", False): .09, ("APP_B", True): .265, ("APP_B", False): .08,
                 ("APP_C", True): .30, ("APP_C", False): .12, ("APP_D", True): .305, ("APP_D", False): .09}
    pc = np.array([base_conv[(a, c in DACH)] for a, c in zip(inst.app, inst.country)])
    pc = np.where(inst.source == "app_store_ads", .06 / .24 * pc, pc)
    pc = np.where(inst.source == "partner", np.minimum(pc * 1.6, .6), pc)
    inst["trial"] = ~inst.uninst_48h & (rng.random(n) < .90)
    inst["paid"] = inst.trial & (rng.random(n) < pc)
    churn = {"APP_A": .045, "APP_B": .05, "APP_C": .03, "APP_D": .06}
    life_m = rng.geometric([churn[a] for a in inst.app])               # months of paid life
    inst["trial_start"] = inst.ts_utc.dt.normalize().where(inst.trial)
    inst["paid_start"] = (inst.trial_start + pd.Timedelta(days=14)).where(inst.paid)
    cancel_paid = inst.paid_start + pd.to_timedelta(life_m * 30, "D")
    cancel_trial = inst.trial_start + pd.Timedelta(days=14)
    inst["cancel_date"] = np.where(inst.paid, cancel_paid, np.where(inst.trial, cancel_trial, pd.NaT))
    inst["cancel_date"] = pd.to_datetime(inst["cancel_date"])
    inst.loc[inst.cancel_date > END, "cancel_date"] = pd.NaT
    price = {"APP_A": (0, "Pay per address"), "APP_C": (99, "Plus"), "APP_D": (19, "Starter")}
    mrr, plan_name, usage = [], [], []
    for a in inst.app:
        if a == "APP_B":
            hi = rng.random() < .4
            mrr.append(19.99 if hi else 9.99); plan_name.append("Pro" if hi else "Basic"); usage.append(0.0)
        else:
            mrr.append(price[a][0]); plan_name.append(price[a][1])
            usage.append(round(float(rng.lognormal(2.7, .6)), 2) if a == "APP_A" else
                         round(float(rng.lognormal(2.2, .7)), 2) if a == "APP_D" else 0.0)
    inst["mrr_usd"], inst["plan"], inst["usage_usd"] = mrr, plan_name, usage

    merchants = inst[["merchant_id", "country", "shopify_plan", "gmv_band"]].copy()
    subs = inst.loc[inst.trial, ["merchant_id", "app", "trial_start", "paid_start", "cancel_date", "plan", "mrr_usd", "usage_usd"]].copy()
    subs.loc[subs.paid_start.isna(), ["mrr_usd", "usage_usd"]] = 0.0
    subs = subs[subs.trial_start <= END]
    subs.loc[subs.paid_start > END, "paid_start"] = pd.NaT

    # ---------- raw install events (with the data problems) ----------
    ev = [inst[["merchant_id", "app", "ts_utc", "country", "source", "utm_source", "utm_campaign"]].assign(event="installed")]
    un48 = inst[inst.uninst_48h]
    ev.append(un48[["merchant_id", "app", "ts_utc", "country", "source", "utm_source", "utm_campaign"]]
              .assign(ts_utc=un48.ts_utc + pd.to_timedelta(rng.integers(1800, 47 * 3600, len(un48)), "s"), event="uninstalled"))
    leave = inst[inst.cancel_date.notna()]                       # churned payers, and 60% of non-converting trials
    leave = leave[rng.random(len(leave)) < np.where(leave.paid, 1.0, .6)]
    ev.append(leave[["merchant_id", "app", "country", "source", "utm_source", "utm_campaign"]]
              .assign(ts_utc=leave.cancel_date + pd.Timedelta(hours=10), event="uninstalled"))
    # quick re-installs within 24h (3% of installs): uninstall + install again, same merchant
    rq = inst[(~inst.uninst_48h) & (rng.random(n) < .03)]
    off = pd.to_timedelta(rng.integers(600, 20 * 3600, len(rq)), "s")
    ev.append(rq[["merchant_id", "app", "country", "source", "utm_source", "utm_campaign"]].assign(ts_utc=rq.ts_utc + off, event="uninstalled"))
    ev.append(rq[["merchant_id", "app", "country", "source", "utm_source", "utm_campaign"]]
              .assign(ts_utc=rq.ts_utc + off + pd.to_timedelta(rng.integers(300, 3 * 3600, len(rq)), "s"), event="installed"))
    events = pd.concat(ev, ignore_index=True)
    # webhook retry storm on 14-15 July 2026: duplicated 'installed' events
    dup_src = inst[inst.ts_utc.dt.normalize().isin(DUP_DAYS)]
    k = rng.poisson(1100 / max(len(dup_src), 1), len(dup_src))
    dups = dup_src.loc[dup_src.index.repeat(k), ["merchant_id", "app", "ts_utc", "country", "source", "utm_source", "utm_campaign"]]
    dups = dups.assign(ts_utc=dups.ts_utc + pd.to_timedelta(rng.integers(5, 240, len(dups)), "s"), event="installed")
    events = pd.concat([events, dups], ignore_index=True)
    events = events[events.ts_utc <= END + pd.Timedelta(hours=23)].sort_values("ts_utc").reset_index(drop=True)
    events.insert(0, "event_id", [f"E{i:07d}" for i in range(1, len(events) + 1)])

    # ---------- marketing spend ----------
    sp = []
    gads = tr[tr.surface == "google_ads"]
    for d in DAYS:
        g = gads[gads.date == d]
        for cmp_id, mask, cpc in (("CMP001", (g["sub"] == "brand") & (g.country == "DE"), .55),
                                  ("CMP002", (g["sub"] == "brand") & (g.country != "DE"), .60),
                                  ("CMP003", g["sub"] == "nonbrand", 1.35)):
            clicks = int(g.loc[mask, "listing_views"].sum())
            # the platform claims every install after a click (no holdout logic)
            claimed = int(g.loc[mask, "installs"].sum()) if cmp_id == "CMP003" else 0  # brand claims set below
            sp.append((d, "google_ads", cmp_id, round(clicks * cpc * rng.uniform(.9, 1.1), 2), clicks, claimed))
        if ADS_START <= d <= ADS_END:
            a = tr[(tr.date == d) & (tr.surface == "app_store_ads")]
            sp.append((d, "app_store_ads", "CMP004", round(int(a.listing_views.sum()) * 0.50, 2), int(a.listing_views.sum()), int(a.installs.sum())))
        if LINKEDIN_START <= d <= LINKEDIN_END:
            sp.append((d, "social", "CMP005", round(1500 / 21, 2), int(rng.poisson(60)), int(rng.poisson(1.2))))
        if META_START <= d <= META_END:
            sp.append((d, "social", "CMP006", round(2400 / 21, 2), int(rng.poisson(310)), int(rng.poisson(7))))
        if d.day == 1:
            sp.append((d, "content", "CMP007", 600.0 if d >= pd.Timestamp("2026-02-01") else 250.0, 0, 0))
            sp.append((d, "partner", "CMP008", 300.0, 0, 0))
            sp.append((d, "email", "CMP009", 150.0, 0, 0))
    spend = pd.DataFrame(sp, columns=["date", "channel", "campaign_id", "spend_eur", "clicks", "platform_reported_conversions"])
    # platform over-claims brand: it credits brand installs plus the organic brand searchers it 'touched'
    br = spend.campaign_id.isin(["CMP001", "CMP002"])
    per_day = spend.loc[br, "clicks"].to_numpy().astype(float)
    spend.loc[br, "platform_reported_conversions"] = rng.multinomial(410, per_day / per_day.sum())  # 410 claimed in total

    # partner bounty: EUR 50 per paying merchant from agencies (paid in the month of conversion)
    pb = inst[(inst.source == "partner") & inst.paid & (inst.paid_start <= END)]
    for mth, cnt in pb.groupby(pb.paid_start.dt.to_period("M")).size().items():
        spend.loc[len(spend)] = (mth.to_timestamp(), "partner", "CMP008", 50.0 * cnt, 0, 0)

    # ---------- e-mail events ----------
    em = []
    sid = 0
    for r in inst.itertuples():
        for k_, day in enumerate((0, 1, 3)):
            if r.uninst_48h and day > 0:
                break
            sid += 1
            o = rng.random() < .52
            em.append((f"S{sid:07d}", r.merchant_id, "onboarding", r.ts_utc + pd.Timedelta(days=day), o, o and rng.random() < .28))
        if not r.uninst_48h:
            sid += 1
            o = rng.random() < .45
            em.append((f"S{sid:07d}", r.merchant_id, "review_request", r.ts_utc + pd.Timedelta(days=5), o, o and rng.random() < .30))
        if r.app == "APP_B" and r.paid and r.ts_utc < END and r.ts_utc >= CROSS_PROMO_START - pd.Timedelta(days=200) and rng.random() < .5:
            sid += 1
            o = rng.random() < .40
            em.append((f"S{sid:07d}", r.merchant_id, "cross_promo", max(r.ts_utc, CROSS_PROMO_START), o, o and rng.random() < .12))
    for r in inst[inst.uninst_48h].sample(frac=.5, random_state=1).itertuples():
        sid += 1
        o = rng.random() < .25
        em.append((f"S{sid:07d}", r.merchant_id, "win_back", r.ts_utc + pd.Timedelta(days=21), o, o and rng.random() < .06))
    email = pd.DataFrame(em, columns=["send_id", "merchant_id", "journey", "sent_utc", "opened", "clicked"])
    email = email[email.sent_utc <= END + pd.Timedelta(hours=23)]

    # ---------- review prompts (EXP01) ----------
    rs = inst[~inst.uninst_48h][["merchant_id", "app", "ts_utc"]].copy()
    d0 = rs.ts_utc.dt.normalize()
    in_test = d0.between(REVIEW_TEST_START, REVIEW_TEST_END)
    treat = (d0 > REVIEW_TEST_END) | (in_test & (rng.random(len(rs)) < .5))
    rs["arm"] = np.where(d0 < REVIEW_TEST_START, "before", np.where(treat, "value_moment", "day_2"))
    rs["prompt_day"] = np.where(rs.arm == "value_moment", rng.integers(3, 13, len(rs)), 2)
    p_rev = np.where(rs.arm == "value_moment", .045 * 2.1, .045)
    rs["reviewed"] = rng.random(len(rs)) < p_rev
    rs["stars"] = np.where(rs.reviewed, rng.choice([5, 4, 3, 2, 1], len(rs), p=[.93, .05, .01, .005, .005]), np.nan)
    reviews_sim = rs.drop(columns=["ts_utc"])

    # ---------- experiments ----------
    exps = experiments_table()
    arms = experiment_arms()

    # ---------- FX ----------
    fxf = PUB / "ecb_eurusd_monthly.csv"
    fx = pd.read_csv(fxf) if fxf.exists() else pd.DataFrame({"month": pd.period_range("2025-11", "2026-10", freq="M").astype(str), "usd_per_eur": 1.10})

    out = {"listing_traffic": listing, "install_events": events, "merchants": merchants, "subscriptions": subs,
           "marketing_spend": spend, "email_events": email, "reviews_sim": reviews_sim, "experiments": exps,
           "experiment_arms": arms, "fx": fx}
    for k_, v in out.items():
        v.to_parquet(SIM / f"{k_}.parquet", index=False)
    truth = pd.DataFrame([
        ("1", "FR+IT listing translation APP_B from 2026-03-02", "installs x1.35 in FR/IT (DiD); naive before/after ~ +55% (spring seasonality)"),
        ("2", "App Store ads APP_A 2026-04-06..05-31", "+30% installs; 41% uninstall <48h; trial->paid 6% vs 24%"),
        ("3", "Google brand ads", f"{BRAND_INCREMENTAL:.0%} of brand installs incremental; platform claims 410; DE holdout {HOLDOUT_START.date()}..{HOLDOUT_END.date()}"),
        ("4", "Review prompt at first value moment from 2026-02-01", "review rate x2.1, stars unchanged"),
        ("5", "Data problems", f"{len(dups)} duplicated installed webhooks on 2026-07-14/15; {len(rq)} re-installs <24h; UTC vs Berlin month shift"),
        ("6", "BFCM 2025-11-24..12-01 + LinkedIn content", "+70% installs everywhere; LinkedIn campaign true effect 0"),
        ("7", "Simpson", "APP_D trial->paid lower overall than APP_B, higher in every country group"),
        ("8", "Meta ads test 3 weeks EUR 2,400", "true +8% trials; MDE ~25%; inconclusive"),
    ], columns=["event", "what", "truth"])
    truth.to_csv(ROOT / "data" / "_hidden_truth.csv", index=False)
    print(f"installs (true) {len(inst):,} | raw events {len(events):,} | dup webhooks {len(dups):,} | quick reinstalls {len(rq):,}")
    print(f"by app: {inst.app.value_counts().sort_index().to_dict()} | DE share {(inst.country == 'DE').mean():.1%}")


EXPERIMENTS = [
    # id, channel, app, title, hypothesis, I, C, E, design, start, end, primary metric, guardrail, decision, learned
    ("EXP01", "Email", "APP_A,APP_B", "Review request at first value moment",
     "We believe asking for a review at the first value moment instead of day 2, for new merchants, will raise the review rate, measured by reviews per active install",
     8, 7, 8, "Randomised 50/50 on new installs", "2026-02-01", "2026-04-30", "review rate", "average stars", "Scale",
     "Timing beats wording: the same ask at the value moment doubles reviews without moving stars."),
    ("EXP02", "Social", "APP_A", "LinkedIn content push in BFCM week",
     "We believe a LinkedIn content series promoting APP_A, for DACH merchants, will raise APP_A installs, measured by installs vs the apps not promoted",
     5, 4, 6, "Before/after + difference-in-differences vs apps not promoted (APP_B+APP_C)", "2025-11-24", "2025-12-14", "installs", "cost per install", "Rerun",
     "The jump was Black Friday, not LinkedIn: the apps not promoted rose as much (DiD ~0). Re-test off-season."),
    ("EXP03", "App Store", "APP_B", "Listing translated into French and Italian",
     "We believe a French and Italian listing, for FR/IT merchants, will raise installs, measured by installs vs ES/NL/PL controls",
     8, 6, 7, "Geo difference-in-differences (FR+IT vs ES+NL+PL)", "2026-03-02", "2026-06-30", "installs", "48h uninstall rate", "Scale",
     "Localisation works; the naive before/after overstates it (spring). Next: Spanish."),
    ("EXP04", "Paid", "APP_A", "Shopify App Store ads",
     "We believe App Store search ads, for merchants searching address validation, will raise paying merchants, measured by CAC per paying merchant",
     6, 5, 8, "Flighting + quality cohort vs organic", "2026-04-06", "2026-05-31", "paying merchants", "48h uninstall rate", "Kill",
     "Installs went up, paying merchants barely: 41% uninstall in 48h, 6% trial->paid. CAC 4x."),
    ("EXP05", "Paid", "All", "Google Ads brand: 4-week geo holdout",
     "We believe most brand-ad conversions would happen anyway, for merchants searching our name, measured by brand-intent traffic in a paused geo",
     7, 6, 9, "Geo holdout: brand ads off in half of the geo cells", "2026-08-03", "2026-08-30", "installs per brand search", "total installs", "Kill",
     "Only ~15% of the 410 claimed conversions are incremental: keep a defensive minimum, move budget."),
    ("EXP06", "Paid", "APP_D", "Meta prospecting ads (3 weeks)",
     "We believe Meta prospecting ads, for lookalike Shopify merchants, will raise trials, measured by trials per reached store vs holdout",
     6, 4, 6, "Audience holdout 50/50", "2026-09-14", "2026-10-04", "trials", "cost per trial", "Inconclusive",
     "+8% but the test could only see 25%: not a failure, not a win. A real read needs ~10x the sample."),
    ("EXP07", "Product", "APP_B->APP_D", "In-app cross-promotion to APP_D",
     "We believe an in-app banner, for paying APP_B merchants, will raise APP_D installs, measured by APP_D installs per merchant",
     7, 7, 8, "Randomised 50/50 on APP_B merchants", "2026-07-15", "2026-08-25", "APP_D install rate", "APP_B uninstall rate", "Scale",
     "Own base is the cheapest channel: more than doubles APP_D installs with no APP_B churn."),
    ("EXP08", "Email", "All", "Win-back e-mail after uninstall",
     "We believe a win-back e-mail 21 days after uninstall, for churned merchants, will raise re-installs, measured by re-install rate",
     4, 5, 8, "Randomised 50/50 on uninstalled merchants", "2026-01-10", "2026-04-30", "re-install rate", "unsubscribe rate", "Kill",
     "No effect at an MDE we cared about: stop, keep the slot for onboarding."),
    ("EXP09", "SEO", "APP_A", "SEO articles: Shopify address validation",
     "We believe 6 how-to articles, for merchants searching address problems, will raise installs from content, measured by content installs vs matched pages",
     7, 5, 5, "Matched-page comparison over 4 months", "2026-02-01", "2026-06-01", "content-sourced installs", "bounce rate", "Scale",
     "Slow but compounding: positive at 4 months. Judge SEO on a 4-month window, not 4 weeks."),
    ("EXP10", "Pricing", "APP_B", "Free plan on the pricing page",
     "We believe a free plan, for small merchants, will raise installs, measured by installs per listing view, with MRR at 60 days as guardrail",
     7, 5, 6, "Randomised pricing-page variant", "2026-05-04", "2026-07-05", "install rate", "MRR per install at 60 days", "Rerun",
     "More installs, flat MRR at 60 days: extend to 120 days before deciding."),
    ("EXP11", "Partners", "APP_A,APP_B", "Shopify agency partner programme",
     "We believe agencies, for their merchant clients, will bring high-quality installs, measured by trial->paid vs organic",
     6, 6, 5, "Cohort comparison vs organic", "2026-01-15", "2026-10-31", "trial->paid", "volume", "Scale",
     "Low volume, best quality: scale slowly by adding agencies, not budget."),
    ("EXP12", "Email", "All", "Onboarding e-mail sequence (day 0/1/3)",
     "We believe a 3-step onboarding sequence, for new trials, will raise trial->paid, measured by paid conversion at day 14",
     7, 7, 8, "Randomised 50/50 on new trials", "2025-12-01", "2026-02-15", "trial->paid", "unsubscribe rate", "Scale",
     "Activation e-mails pay back fast; keep and iterate on content."),
    ("EXP13", "App Store", "APP_A", "Screenshots with German captions",
     "We believe German captions, for DACH visitors, will raise listing conversion, measured by installs per listing view",
     5, 4, 8, "Before/after with EN listing views as control", "2026-05-11", "2026-06-07", "install rate", "-", "Kill",
     "No effect worth having: even the upper bound is below +10%. Stop polishing screenshots."),
    ("EXP14", "Paid", "APP_A", "Google non-brand: 'shopify address validation' ad group",
     "We believe a tight non-brand ad group, for merchants with address problems, will raise installs per click, measured by install rate per click",
     6, 6, 7, "Randomised ad-group split (Google experiments)", "2026-03-09", "2026-04-19", "install rate per click", "CPC", "Scale",
     "Intent keywords convert; move brand money here."),
    ("EXP15", "Social", "All", "Founder posts on LinkedIn",
     "We believe weekly founder posts, for DACH e-commerce managers, will raise listing visits, measured by social-sourced listing views",
     4, 3, 7, "Alternating weeks on/off", "2026-04-06", "2026-05-31", "social listing views", "-", "Inconclusive",
     "Signal too weak for the sample; keep as brand activity, not a growth channel."),
    ("EXP16", "Content", "APP_A", "YouTube tutorial videos",
     "We believe tutorials, for merchants evaluating apps, will raise installs, measured by video-sourced installs",
     4, 4, 3, "Before/after with matched control apps", "2026-03-01", "2026-05-31", "installs from video", "production cost", "Kill",
     "Costly to produce, no measurable effect: stop."),
    ("EXP17", "SEO", "APP_B", "Comparison page vs category leaders",
     "We believe an honest comparison page, for merchants comparing payment-rule apps, will raise installs, measured by content installs",
     7, 6, 6, "Matched-page comparison", "2026-04-01", "2026-07-31", "content-sourced installs", "-", "Scale",
     "Comparison intent converts well; add one per app."),
    ("EXP18", "App Store", "APP_A", "Reply to every review within 48 h",
     "We believe fast public replies, for listing visitors, will raise listing conversion, measured by installs per view",
     6, 4, 9, "Before/after with sister-app control", "2026-06-01", "2026-07-31", "install rate", "-", "Inconclusive",
     "Cheap and right for trust, but the effect is too small to measure in 2 months."),
    ("EXP19", "Pricing", "APP_D", "Trial shortened from 14 to 7 days",
     "We believe a 7-day trial, for new merchants, will raise trial->paid speed, measured by paid conversion",
     5, 5, 9, "Randomised 50/50", "2026-08-01", "2026-09-15", "trial->paid", "uninstall rate", "Kill",
     "Fewer merchants reach value in 7 days: conversion drops. Keep 14."),
    ("EXP20", "Pricing", "APP_D", "Usage-based pricing copy",
     "We believe clearer usage-pricing copy, for listing visitors, will raise install rate, measured by installs per view",
     5, 4, 9, "Randomised pricing-page variant", "2026-09-01", "2026-10-15", "install rate", "-", "Rerun",
     "Positive but not significant; rerun with 2x traffic."),
    ("EXP21", "Content", "All", "Answers in the Shopify Community forum",
     "We believe helpful answers, for merchants asking checkout questions, will raise installs, measured by referral installs",
     3, 3, 6, "Before/after", "2026-01-12", "2026-03-08", "referral installs", "time spent", "Kill",
     "Too little volume for the time it takes."),
    ("EXP22", "Email", "APP_C", "Newsletter cross-promo to Plus merchants",
     "We believe a newsletter feature, for Plus merchants of APP_A, will raise APP_C trials, measured by trial rate",
     4, 4, 8, "Randomised 50/50", "2026-02-02", "2026-03-01", "APP_C trial rate", "unsubscribe rate", "Kill",
     "Plus merchants in the base are few and not interested now: stop."),
    ("EXP23", "App Store", "APP_B", "Listing title with the main keyword",
     "We believe the keyword 'hide payment methods' in the title, for App Store searchers, will raise installs, measured by installs per view",
     7, 6, 9, "Before/after with sister-app control", "2026-06-08", "2026-07-19", "install rate", "-", "Scale",
     "The listing title is the cheapest lever we have."),
    ("EXP24", "Social", "All", "Posts in Facebook merchant groups",
     "We believe posts in merchant groups, for small DACH stores, will raise installs, measured by social installs",
     3, 3, 7, "Before/after", "2026-05-04", "2026-05-31", "social installs", "-", "Kill",
     "No effect, risk of looking spammy: stop."),
]

# arm-level counts for the experiments not read from the main tables: (unit, n per arm, base rate, true relative lift)
ARM_PARAMS = {
    "EXP05": ("brand searches (geo cells: ads on = control, ads off = treatment)", 26000, .034, -.15),
    "EXP06": ("reached stores", 72000, .0035, .08), "EXP07": ("APP_B merchants", 1100, .02, 1.2),
    "EXP08": ("uninstalled merchants", 4200, .030, .02), "EXP09": ("content sessions", 7000, .030, .40),
    "EXP10": ("listing views", 9000, .080, .22), "EXP11": ("trials", 260, .24, .70),
    "EXP12": ("trials", 1300, .22, .30), "EXP13": ("listing views", 6000, .12, .03),
    "EXP14": ("clicks", 2600, .040, .45), "EXP15": ("weeks x visits", 1800, .020, .10),
    "EXP16": ("video sessions", 2200, .020, -.05), "EXP17": ("content sessions", 4800, .030, .45),
    "EXP18": ("listing views", 7000, .12, .03), "EXP19": ("trials", 1600, .19, -.25),
    "EXP20": ("listing views", 5000, .08, .06), "EXP21": ("referral sessions", 3000, .020, .00),
    "EXP22": ("Plus merchants", 2500, .010, .00), "EXP23": ("listing views", 8000, .10, .20),
    "EXP24": ("group visitors", 3500, .015, .00),
}


def experiments_table() -> pd.DataFrame:
    cols = ["exp_id", "channel", "app", "title", "hypothesis", "ice_impact", "ice_confidence", "ice_ease", "design",
            "start_date", "end_date", "primary_metric", "guardrail", "decision", "learned"]
    df = pd.DataFrame(EXPERIMENTS, columns=cols)
    df["ice_score"] = df[["ice_impact", "ice_confidence", "ice_ease"]].mean(axis=1).round(2)
    return df


def experiment_arms() -> pd.DataFrame:
    r = np.random.default_rng(4242)
    rows = []
    for e, (unit, n_arm, p, lift) in ARM_PARAMS.items():
        rows.append((e, "control", unit, n_arm, int(r.binomial(n_arm, p))))
        rows.append((e, "treatment", unit, n_arm, int(r.binomial(n_arm, min(p * (1 + lift), 1)))))
    return pd.DataFrame(rows, columns=["exp_id", "arm", "unit", "units", "conversions"])


if __name__ == "__main__":
    build()
