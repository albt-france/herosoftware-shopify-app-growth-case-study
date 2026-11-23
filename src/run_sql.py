"""Run sql/01..10 and 99 in DuckDB on the public CSVs and the simulated parquet files, export every out_* table
to data/out/<name>.csv, then build the 24 experiment read-outs (data/out/experiment_readouts.csv).

Run:  python src/run_sql.py
"""
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ab_stats import Z, prop_test  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SIM, PUB, OUT = ROOT / "data" / "sim", ROOT / "data" / "public", ROOT / "data" / "out"
MIN_WORTHWHILE = 0.10   # smallest relative lift worth acting on (playbook)


def connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    for f in sorted(SIM.glob("*.parquet")):
        con.execute(f"CREATE OR REPLACE TABLE {f.stem} AS SELECT * FROM read_parquet('{f.as_posix()}')")
    for name, f in {"reviews_public": "reviews_public.csv", "listings": "listings.csv", "categories": "categories.csv",
                    "wayback": "wayback_rating_counts.csv", "eurostat": "eurostat_b2c_online_sales.csv"}.items():
        con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM read_csv_auto('{(PUB / f).as_posix()}', header=true)")
    con.execute("CREATE OR REPLACE TABLE fx AS SELECT CAST(month AS VARCHAR) AS month, usd_per_eur FROM fx")
    return con


def mde_rel(p: float, n: int, alpha=0.05, power=0.80) -> float:
    return (Z(1 - alpha / 2) + Z(power)) * np.sqrt(2 * p * (1 - p) / n) / p


def rule(lo: float, hi: float) -> str:
    if lo > 0:
        return "Scale"
    if hi < 0:
        return "Kill"
    if hi < MIN_WORTHWHILE:
        return "Kill"            # no effect we would care about is left in the interval
    return "Inconclusive"


def readouts(con) -> pd.DataFrame:
    exps = con.sql("SELECT * FROM experiments").df()
    arms = con.sql("SELECT * FROM experiment_arms").df()
    rows = {}
    for e, g in arms.groupby("exp_id"):
        c, t = g[g.arm == "control"].iloc[0], g[g.arm == "treatment"].iloc[0]
        r = prop_test(t.conversions, t.units, c.conversions, c.units)
        rows[e] = dict(unit=c.unit, n_control=int(c.units), n_treatment=int(t.units), rate_control=r["rate_c"],
                       rate_treatment=r["rate_t"], lift=r["rel"], ci_low=r["rel_low"], ci_high=r["rel_high"], p_value=r["p"],
                       mde_80=mde_rel(r["rate_c"], int(c.units)), source="experiment_arms")
    # EXP01: review prompt (randomised, main tables)
    rv = con.sql("SELECT * FROM out_exp01_reviews").df().set_index("arm")
    r = prop_test(rv.loc["value_moment", "reviews"], rv.loc["value_moment", "prompted"], rv.loc["day_2", "reviews"], rv.loc["day_2", "prompted"])
    rows["EXP01"] = dict(unit="new installs prompted", n_control=int(rv.loc["day_2", "prompted"]), n_treatment=int(rv.loc["value_moment", "prompted"]),
                         rate_control=r["rate_c"], rate_treatment=r["rate_t"], lift=r["rel"], ci_low=r["rel_low"], ci_high=r["rel_high"],
                         p_value=r["p"], mde_80=mde_rel(r["rate_c"], int(rv.loc["day_2", "prompted"])), source="reviews_sim")
    # EXP02 and EXP03: difference-in-differences on installs
    b = con.sql("SELECT * FROM out_bfcm_did").df().iloc[0]
    rows["EXP02"] = dict(unit="installs (DiD APP_A vs apps not promoted)", lift=b.did_lift, ci_low=b.did_ci_low, ci_high=b.did_ci_high,
                         naive=b.naive_lift, source="stg_installs")
    d = con.sql("SELECT * FROM out_exp03_did WHERE metric = 'installs'").df().iloc[0]
    rows["EXP03"] = dict(unit="installs (DiD FR+IT vs ES+NL+PL)", lift=d.did_lift, ci_low=d.did_ci_low, ci_high=d.did_ci_high,
                         naive=d.naive_before_after, source="stg_installs")
    # EXP04: paying merchants per install, ads vs organic in the same weeks
    q = con.sql("SELECT * FROM out_exp04_quality").df().set_index("cohort")
    r = prop_test(q.loc["App Store ads", "paying"], q.loc["App Store ads", "installs"], q.loc["Organic + other", "paying"], q.loc["Organic + other", "installs"])
    rows["EXP04"] = dict(unit="installs (paying per install, ads vs organic)", n_control=int(q.loc["Organic + other", "installs"]),
                         n_treatment=int(q.loc["App Store ads", "installs"]), rate_control=r["rate_c"], rate_treatment=r["rate_t"],
                         lift=r["rel"], ci_low=r["rel_low"], ci_high=r["rel_high"], p_value=r["p"], source="stg_installs")
    out = pd.DataFrame.from_dict(rows, orient="index").rename_axis("exp_id").reset_index()
    out = exps.merge(out, on="exp_id", how="left")
    out["rule_call"] = [rule(lo, hi) for lo, hi in zip(out.ci_low, out.ci_high)]
    why = {"EXP02": "Confounded by Black Friday: re-test off-season.",
           "EXP04": "Installs up, but paying per install far lower and CAC 4x: kill on cost, not on installs.",
           "EXP05": "Ads off lose only ~15% of brand installs: cut brand spend to a defensive minimum.",
           "EXP06": "Under-powered: the MDE is far above the effect seen.",
           "EXP10": "Installs up, MRR at 60 days flat (guardrail): extend to 120 days.",
           "EXP11": "Cohort comparison, not randomised: scale slowly.",
           "EXP08": "Under-powered, and the uninstalled base is too small to ever power it: stop.",
           "EXP13": "Upper bound below the +10% worth acting on.", "EXP15": "Under-powered.", "EXP18": "Under-powered.",
           "EXP16": "Under-powered and expensive to produce: stop.", "EXP21": "Under-powered, tiny volume: stop.",
           "EXP24": "Under-powered, tiny volume, brand risk: stop.",
           "EXP20": "Positive but not significant; cheap to rerun with 2x traffic.",
           "EXP22": "Too few Plus merchants to matter, whatever the lift."}
    out["note"] = out.exp_id.map(why).fillna("")
    return out


def write_log(ro: pd.DataFrame) -> None:
    """docs/experiment_log.csv + .md, generated from the read-outs (SIMULATED)."""
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    cols = ["exp_id", "channel", "app", "title", "hypothesis", "ice_score", "design", "start_date", "end_date", "primary_metric",
            "guardrail", "lift", "ci_low", "ci_high", "p_value", "mde_80", "rule_call", "decision", "note", "learned"]
    ro[cols].round(4).to_csv(docs / "experiment_log.csv", index=False)
    f = lambda v: "-" if pd.isna(v) else f"{v:+.0%}"  # noqa: E731
    lines = ["# Experiment log (SIMULATED)", "",
             "24 experiments run on the fictional portfolio APP_A-APP_D. **SIMULATED data, not HeroSoftware's figures.**",
             "Lift = relative change of the primary metric, 95% CI. `rule_call` = statistical call from the playbook rule; "
             "`decision` = the decision taken (a different one is explained in `note`). Full table: `experiment_log.csv`.", "",
             f"Decisions: {ro.decision.value_counts().to_dict()}", ""]
    for r in ro.itertuples():
        lines += [f"## {r.exp_id} - {r.title} ({r.channel}, {r.app})", "",
                  f"- **Hypothesis:** {r.hypothesis}.",
                  f"- **ICE:** {r.ice_impact}/{r.ice_confidence}/{r.ice_ease} -> {r.ice_score:.2f} | **Design:** {r.design} | **Dates:** {r.start_date} -> {r.end_date}",
                  f"- **Primary metric:** {r.primary_metric} | **Guardrail:** {r.guardrail}",
                  f"- **Result:** lift {f(r.lift)} (95% CI {f(r.ci_low)} to {f(r.ci_high)})"
                  + (f", MDE at 80% power {r.mde_80:.0%}" if not pd.isna(r.mde_80) else "")
                  + f" | rule: {r.rule_call} | **Decision: {r.decision}**" + (f" - {r.note}" if r.note else ""),
                  f"- **What we learned:** {r.learned}", ""]
    (docs / "experiment_log.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    con = connect()
    for f in sorted((ROOT / "sql").glob("*.sql")):
        con.execute(f.read_text(encoding="utf-8"))
    tests = con.sql("SELECT * FROM out_tests").df()
    for t in con.sql("SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'out_%'").fetchall():
        con.sql(f"SELECT * FROM {t[0]}").df().to_csv(OUT / f"{t[0][4:]}.csv", index=False)
    ro = readouts(con)
    ro.to_csv(OUT / "experiment_readouts.csv", index=False)
    write_log(ro)
    print(f"{len(list(OUT.glob('*.csv')))} tables exported to data/out/ | tests passed {int(tests.passed.sum())}/{len(tests)}")
    if not tests.passed.all():
        print(tests[~tests.passed].to_string(index=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
