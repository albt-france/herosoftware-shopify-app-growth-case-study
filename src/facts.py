"""Collect every number quoted in the PDF, README, dashboard and docs into data/out/facts.json, read only from
data/public (PUBLIC DATA) and data/out (SQL outputs on SIMULATED data). Nothing is typed by hand.

Run:  python src/facts.py   (called by build_pdf.py and build_dashboard.py)
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT, PUB = ROOT / "data" / "out", ROOT / "data" / "public"


def o(name):
    return pd.read_csv(OUT / f"{name}.csv")


def build() -> dict:
    lst = pd.read_csv(PUB / "listings.csv")
    tot = o("reviews_totals").iloc[0]
    by_app = o("reviews_by_app").set_index("app")
    cat = o("category_summary").set_index("herosoftware_app")
    eu = o("eurostat").set_index("geo")["pct_enterprises_selling_online_b2c"]
    company = json.loads((PUB / "company_facts.json").read_text(encoding="utf-8"))
    did = o("exp03_did").set_index("metric")
    q = o("exp04_quality").set_index("cohort")
    sc = o("channel_scorecard").set_index("channel")
    paid_other = sc.loc[["partner", "google_ads_brand", "content", "google_ads_nonbrand", "email"]]
    brand = o("brand_holdout").iloc[0]
    bf, bfw = o("bfcm_did").iloc[0], o("bfcm_week").iloc[0]
    simp = o("simpson")
    sm = lambda lvl, seg, app: float(simp[(simp.level == lvl) & (simp.segment == seg) & (simp.app == app)].trial_to_paid.iloc[0])  # noqa: E731
    rv = o("exp01_reviews").set_index("arm")
    ro = o("experiment_readouts").set_index("exp_id")
    dq = o("dq_summary").set_index("k")["n"]
    f = {
        "collected": str(tot.collected),
        "company": company,
        "apps": lst[["short_name", "listing_name", "launched", "rating", "rating_count", "pricing", "categories_display",
                     "description_language", "description_len", "languages", "built_for_shopify", "n_screenshots"]].to_dict("records"),
        "public": {
            "reviews": int(tot.reviews), "share_5_star": float(tot.share_5_star), "share_germany": float(tot.share_germany),
            "share_dach": float(tot.share_dach), "share_tenure_days": float(tot.share_tenure_in_days),
            "may_jun_2025": int(tot.may_jun_2025), "share_may_jun_2025": round(float(tot.may_jun_2025) / float(tot.reviews), 3),
            "replies_2026_11_09": int(tot.replies_2026_11_09), "since_2026_03": int(tot.since_2026_03),
            "upsell_since_2026_03": int(by_app.loc["Post Purchase Upsell Hero", "reviews_since_2026_03"]),
            "upsell_share_germany": float(by_app.loc["Post Purchase Upsell Hero", "share_germany"]),
            "reply_rate": by_app["reply_rate"].to_dict(), "last_review": by_app["last_review"].to_dict(),
            "categories": {a: {"slug": r.category, "apps": int(r.apps_listed), "position": int(r.hero_position),
                               "review_rank": int(r.hero_review_rank), "apps_50_plus": int(r.apps_50_plus_reviews),
                               "median_reviews": float(r.median_reviews), "free_top30": float(r.free_plan_top30),
                               "free_rest": float(r.free_plan_rest), "ad_cards": int(r.ad_cards)} for a, r in cat.iterrows()},
            "eurostat_2024": {k: (None if pd.isna(v) else float(v)) for k, v in eu.items()},
        },
        "sim": {
            "installs": int(dq.loc[4]), "raw_installed": int(dq.loc[1]), "dup_removed": int(dq.loc[2]),
            "quick_reinstalls": int(dq.loc[3]), "month_shift": int(dq.loc[5]),
            "exp03": {"naive": float(did.loc["installs", "naive_before_after"]), "did": float(did.loc["installs", "did_lift"]),
                      "lo": float(did.loc["installs", "did_ci_low"]), "hi": float(did.loc["installs", "did_ci_high"]),
                      "views_did": float(did.loc["listing_views", "did_lift"]), "views_lo": float(did.loc["listing_views", "did_ci_low"]),
                      "views_hi": float(did.loc["listing_views", "did_ci_high"]), "control": float(did.loc["installs", "control_change"])},
            "exp04": {"uninstall_ads": float(q.loc["App Store ads", "uninstall_48h"]), "uninstall_org": float(q.loc["Organic + other", "uninstall_48h"]),
                      "t2p_ads": float(q.loc["App Store ads", "trial_to_paid"]), "t2p_org": float(q.loc["Organic + other", "trial_to_paid"]),
                      "cac_ads": float(sc.loc["app_store_ads", "cac_per_paying"]),
                      "cac_other_paid": round(float(paid_other.spend_eur.sum() / paid_other.paying.sum()), 0),
                      "installs_ads": int(q.loc["App Store ads", "installs"])},
            "brand": {"claimed": int(brand.claimed), "share": float(brand.incremental_share), "lo": float(brand.incr_ci_low),
                      "hi": float(brand.incr_ci_high), "incremental": int(brand.incremental_conversions), "spend": float(brand.spend_eur),
                      "cost_claimed": float(brand.cost_per_claimed), "cost_incremental": float(brand.cost_per_incremental)},
            "reviews": {"rate_day2": float(rv.loc["day_2", "review_rate"]), "rate_value": float(rv.loc["value_moment", "review_rate"]),
                        "stars_day2": float(rv.loc["day_2", "avg_stars"]), "stars_value": float(rv.loc["value_moment", "avg_stars"]),
                        "lift": float(ro.loc["EXP01", "lift"]), "lo": float(ro.loc["EXP01", "ci_low"]), "hi": float(ro.loc["EXP01", "ci_high"])},
            "bfcm": {"week_lift": float(bfw.bfcm_week_lift), "naive": float(bf.naive_lift), "not_promoted": float(bf.not_promoted_change),
                     "did": float(bf.did_lift), "lo": float(bf.did_ci_low), "hi": float(bf.did_ci_high)},
            "simpson": {"b_all": sm("overall", "all", "APP_B"), "d_all": sm("overall", "all", "APP_D"),
                        "b_dach": sm("region", "DACH", "APP_B"), "d_dach": sm("region", "DACH", "APP_D"),
                        "b_non": sm("region", "non-DACH", "APP_B"), "d_non": sm("region", "non-DACH", "APP_D"),
                        "mix": o("simpson_mix").set_index("app").non_dach_share_of_trials.to_dict()},
            "meta": {"lift": float(ro.loc["EXP06", "lift"]), "lo": float(ro.loc["EXP06", "ci_low"]), "hi": float(ro.loc["EXP06", "ci_high"]),
                     "mde": float(ro.loc["EXP06", "mde_80"]), "n": int(ro.loc["EXP06", "n_control"]), "p": float(ro.loc["EXP06", "p_value"]),
                     "rate": float(ro.loc["EXP06", "rate_control"])},
            "decisions": ro.decision.value_counts().to_dict(),
            "scorecard": sc.reset_index().to_dict("records"),
        },
    }
    # sample size needed for the Meta test to see +8% (80% power, alpha 5%)
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from ab_stats import sample_size_prop
    f["sim"]["meta"]["n_needed_8pct"] = int(sample_size_prop(f["sim"]["meta"]["rate"], 0.08))
    f["sim"]["meta"]["weeks_needed_8pct"] = round(f["sim"]["meta"]["n_needed_8pct"] / f["sim"]["meta"]["n"] * 3, 0)
    f["sim"]["meta"]["budget_needed_8pct"] = round(2400 * f["sim"]["meta"]["n_needed_8pct"] / f["sim"]["meta"]["n"], -2)
    (OUT / "facts.json").write_text(json.dumps(f, indent=2, default=str), encoding="utf-8")
    return f


if __name__ == "__main__":
    F = build()
    print("facts.json:", len(json.dumps(F)), "chars")
