"""Matplotlib charts for the PDF (report/img/*.png). One function per chart, every number read from data/out or
data/public. Each chart carries a 'PUBLIC DATA' or 'SIMULATED' mark. Style: Segoe UI, blue for data, grey for
comparison, red for alerts.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mtick  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT, PUB, IMG = ROOT / "data" / "out", ROOT / "data" / "public", ROOT / "report" / "img"
BLUE, LIGHT, GREY, RED, INK, MUTED, GRID = "#2A78D6", "#A9C9EE", "#A3A19A", "#D03B3B", "#0B0B0B", "#52514E", "#E1E0D9"
GREEN, ORANGE, PURPLE = "#1B7F55", "#EB6834", "#6B4FBB"
APP_COL = {"AddressHero": BLUE, "PaymentHero": ORANGE, "Post Purchase Upsell Hero": GREEN, "DiscountHero": PURPLE}
DEC_COL = {"Scale": GREEN, "Kill": RED, "Rerun": ORANGE, "Inconclusive": GREY}
plt.rcParams.update({
    "font.family": "Segoe UI", "font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": MUTED,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "figure.facecolor": "white", "axes.facecolor": "white", "legend.frameon": False,
    "axes.titlesize": 11, "axes.titleweight": "semibold", "axes.titlecolor": INK, "axes.titlelocation": "left",
})


def o(name):
    return pd.read_csv(OUT / f"{name}.csv")


def save(fig, name, tag):
    fig.text(0.995, 0.01, tag, ha="right", va="bottom", fontsize=7.5, fontweight="bold",
             color="#1C5CAB" if tag == "PUBLIC DATA" else "#9A3B12")
    fig.tight_layout()
    fig.savefig(IMG / f"{name}.png", dpi=170)
    plt.close(fig)


def reviews_monthly():
    m = o("reviews_monthly")
    p = m.pivot(index="month", columns="app", values="reviews").fillna(0)
    p = p.reindex(pd.period_range(p.index.min(), "2026-11", freq="M").astype(str), fill_value=0)
    fig, ax = plt.subplots(figsize=(7.2, 3.1))
    bottom = np.zeros(len(p))
    for a in ["AddressHero", "PaymentHero", "Post Purchase Upsell Hero", "DiscountHero"]:
        if a in p:
            ax.bar(range(len(p)), p[a], bottom=bottom, color=APP_COL[a], label=a, width=.8)
            bottom += p[a].to_numpy()
    ticks = [i for i, x in enumerate(p.index) if x.endswith(("-01", "-07"))]
    ax.set_xticks(ticks, [p.index[i] for i in ticks])
    ax.set_title("Public reviews per month, by app")
    ax.set_ylabel("reviews")
    ax.legend(fontsize=8, ncol=2)
    save(fig, "p2_reviews_monthly", "PUBLIC DATA")


def countries():
    c = o("reviews_country").sort_values("reviews")
    fig, ax = plt.subplots(figsize=(3.6, 3.1))
    ax.barh(c.country, c.share, color=[BLUE if x == "Germany" else LIGHT for x in c.country])
    for y, v in enumerate(c.share):
        ax.text(v + .01, y, f"{v:.1%}", va="center", fontsize=8.5, color=INK)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(1))
    ax.set_xlim(0, 1.05)
    ax.set_title("Reviews by country (<5 = Other)")
    save(fig, "p2_countries", "PUBLIC DATA")


def category_scatter():
    s = o("category_scatter")
    s = s[s.category == "marketing-and-conversion-checkout-checkout-other"]
    fig, ax = plt.subplots(figsize=(4.4, 3.1))
    ax.scatter(s.position, s.total_reviews, s=22, c=[GREEN if f else GREY for f in s.free_plan], alpha=.8)
    h = s[s.is_herosoftware]
    ax.scatter(h.position, h.total_reviews, s=80, c=ORANGE, zorder=3)
    for _, r in h.iterrows():
        ax.annotate("PaymentHero: position 30,\n7th by reviews", (r.position, r.total_reviews), xytext=(r.position + 3, r.total_reviews + 170),
                    fontsize=8, color=INK, arrowprops=dict(arrowstyle="-", color=MUTED))
    ax.set_yscale("symlog", linthresh=10)
    ax.set_xlabel("position in category (default order, observed once)")
    ax.set_ylabel("total reviews")
    ax.set_title("Checkout - Other: position vs reviews")
    ax.text(.98, .97, "green = free plan", transform=ax.transAxes, ha="right", va="top", fontsize=8, color=GREEN)
    save(fig, "p2_category_scatter", "PUBLIC DATA")


def free_plan():
    c = o("category_summary")
    short = {"Post Purchase Upsell Hero": "Upsell", "AddressHero": "Shipping", "PaymentHero": "Checkout", "DiscountHero": "Fraud"}
    c["lab"] = c.herosoftware_app.map(short)
    x = np.arange(len(c))
    fig, ax = plt.subplots(figsize=(3.8, 3.1))
    ax.bar(x - .2, c.free_plan_top30, .4, color=GREEN, label="top 30")
    ax.bar(x + .2, c.free_plan_rest, .4, color=GREY, label="position 31+")
    ax.set_xticks(x, c.lab)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1))
    ax.set_title("Share of apps with a free plan")
    ax.legend(fontsize=8)
    save(fig, "p2_free_plan", "PUBLIC DATA")


LABEL = {"partner": "Agency partners", "google_ads_brand": "Google Ads brand", "content": "Content / SEO",
         "app_store_ads": "App Store ads", "google_ads_nonbrand": "Google Ads non-brand", "email": "E-mail",
         "app_store_search": "App Store search", "category_browse": "Category browse", "direct": "Direct", "social": "Social (organic)"}


def scorecard():
    s = o("channel_scorecard")
    p = s[s.spend_eur > 0].sort_values("cac_per_paying")
    fig, axs = plt.subplots(1, 2, figsize=(7.6, 3.0), gridspec_kw={"width_ratios": [1.2, 1]})
    ax = axs[0]
    cols = [RED if c == "app_store_ads" else (ORANGE if c == "google_ads_brand" else BLUE) for c in p.channel]
    ax.barh(p.channel.map(LABEL), p.cac_per_paying, color=cols)
    for y, v in enumerate(p.cac_per_paying):
        ax.text(v + 6, y, f"EUR {v:,.0f}", va="center", fontsize=8.5)
    ax.set_title("CAC per paying merchant")
    ax.set_xlim(0, p.cac_per_paying.max() * 1.3)
    ax = axs[1]
    ax.barh(p.channel.map(LABEL), p.payback_months, color=cols)
    for y, v in enumerate(p.payback_months):
        ax.text(v + .5, y, f"{v:.1f}", va="center", fontsize=8.5)
    ax.set_yticks([])
    ax.set_title("Payback (months)")
    ax.set_xlim(0, p.payback_months.max() * 1.25)
    save(fig, "p3_cac_payback", "SIMULATED")


def quality():
    s = o("channel_scorecard").sort_values("installs", ascending=False)
    fig, ax = plt.subplots(figsize=(4.6, 3.0))
    ax.scatter(s.uninstall_48h_rate, s.trial_to_paid, s=s.installs / 8, c=[RED if c == "app_store_ads" else BLUE for c in s.channel], alpha=.75)
    for _, r in s.iterrows():
        if r.channel in ("app_store_ads", "partner", "email", "app_store_search"):
            ax.annotate(LABEL[r.channel], (r.uninstall_48h_rate, r.trial_to_paid), xytext=(5, 4), textcoords="offset points", fontsize=8)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(1))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1))
    ax.set_xlabel("uninstalled within 48 h")
    ax.set_ylabel("trial -> paid")
    ax.set_title("Install quality by channel (size = installs)")
    save(fig, "p3_quality", "SIMULATED")


def funnel():
    f = o("funnel_total")
    fig, ax = plt.subplots(figsize=(3.6, 3.0))
    steps = f.step.tolist()[1:]
    vals = f.n.tolist()[1:]
    ax.barh(steps[::-1], vals[::-1], color=BLUE)
    for y, v in enumerate(vals[::-1]):
        ax.text(v + 80, y, f"{v:,.0f}", va="center", fontsize=8.5)
    ax.set_xlim(0, max(vals) * 1.25)
    ax.set_title("Funnel, installs to day 60")
    ax.grid(axis="y", visible=False)
    save(fig, "p3_funnel", "SIMULATED")


def forest():
    r = o("experiment_readouts").sort_values("exp_id", ascending=False)
    fig, ax = plt.subplots(figsize=(6.0, 5.6))
    y = np.arange(len(r))
    lift = r.lift.clip(-1, 2)
    ax.hlines(y, r.ci_low.clip(-1, 2.2), r.ci_high.clip(-1, 2.2), color=[DEC_COL[d] for d in r.decision], lw=2.2)
    ax.scatter(lift, y, color=[DEC_COL[d] for d in r.decision], zorder=3, s=22)
    ax.axvline(0, color=INK, lw=.8)
    ax.set_yticks(y, [f"{e}  {t if len(t) <= 38 else t[:37] + chr(8230)}" for e, t in zip(r.exp_id, r.title)], fontsize=7.6)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(1))
    ax.set_xlim(-1, 2.2)
    ax.set_title("24 experiments: relative lift and 95% CI")
    for d, c in DEC_COL.items():
        ax.plot([], [], color=c, lw=3, label=d)
    ax.legend(fontsize=8, loc="lower right")
    save(fig, "p4_forest", "SIMULATED")


def exp03():
    w = o("exp03_weekly")
    w["week"] = pd.to_datetime(w.week)
    w = w[(w.week >= "2025-12-01") & (w.week <= "2026-06-29")]
    fig, ax = plt.subplots(figsize=(4.6, 2.8))
    ax.plot(w.week, w.treated_fr_it.rolling(3, min_periods=1).mean(), color=BLUE, lw=2, label="FR + IT (translated)")
    ax.plot(w.week, w.control_es_nl_pl.rolling(3, min_periods=1).mean(), color=GREY, lw=2, label="ES + NL + PL (control)")
    ax.axvline(pd.Timestamp("2026-03-02"), color=INK, ls="--", lw=.8)
    ax.text(pd.Timestamp("2026-03-05"), ax.get_ylim()[1] * .95, "listing translated", fontsize=8, va="top")
    ax.set_title("APP_B weekly installs (3-week average)")
    ax.legend(fontsize=8, loc="upper left")
    save(fig, "p4_exp03", "SIMULATED")


def exp04():
    q = o("exp04_quality")
    fig, axs = plt.subplots(1, 2, figsize=(4.4, 2.8))
    for ax, col, t in ((axs[0], "uninstall_48h", "Uninstall < 48 h"), (axs[1], "trial_to_paid", "Trial -> paid")):
        ax.bar(["Ads", "Organic"], q.set_index("cohort").loc[["App Store ads", "Organic + other"], col], color=[RED, BLUE])
        for x, v in enumerate(q.set_index("cohort").loc[["App Store ads", "Organic + other"], col]):
            ax.text(x, v + .01, f"{v:.0%}", ha="center", fontsize=9)
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1))
        ax.set_ylim(0, .5)
        ax.set_title(t, fontsize=10)
    save(fig, "p4_exp04", "SIMULATED")


def bfcm():
    d = o("daily_installs")
    d["date"] = pd.to_datetime(d.date)
    d = d[(d.date >= "2025-11-03") & (d.date <= "2025-12-21")]
    g = d.assign(grp=np.where(d.app == "APP_A", "APP_A (promoted)", np.where(d.app.isin(["APP_B", "APP_C"]), "APP_B + APP_C (not promoted)", "x")))
    g = g[g.grp != "x"].groupby(["date", "grp"]).installs.sum().unstack()
    fig, ax = plt.subplots(figsize=(4.4, 4.0))
    ax.axvspan(pd.Timestamp("2025-11-24"), pd.Timestamp("2025-12-01"), color="#FBE9E0")
    ax.text(pd.Timestamp("2025-11-24"), ax.get_ylim()[1], " Black Friday week", fontsize=8, va="top")
    ax.plot(g.index, g.iloc[:, 0].rolling(3, min_periods=1).mean(), color=BLUE, lw=2, label=g.columns[0])
    ax.plot(g.index, g.iloc[:, 1].rolling(3, min_periods=1).mean(), color=GREY, lw=2, label=g.columns[1])
    ax.set_title("Daily installs (3-day average)")
    ax.legend(fontsize=7.5, loc="lower left")
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d %b"))
    save(fig, "p5_bfcm", "SIMULATED")


def brand():
    b = o("brand_holdout").iloc[0]
    fig, ax = plt.subplots(figsize=(4.4, 4.0))
    vals = [b.claimed, b.incremental_conversions]
    ax.bar(["Claimed by\nthe platform", "Incremental\n(geo holdout)"], vals, color=[GREY, BLUE])
    for x, v in enumerate(vals):
        ax.text(x, v + 8, f"{v:,.0f}", ha="center", fontsize=10, fontweight="bold")
    ax.set_title("Google Ads brand, 12 months")
    ax.set_ylim(0, b.claimed * 1.2)
    save(fig, "p5_brand", "SIMULATED")


def simpson():
    s = o("simpson")
    seg = [("overall", "all", "All"), ("region", "DACH", "DACH"), ("region", "non-DACH", "non-DACH")]
    fig, ax = plt.subplots(figsize=(4.4, 4.0))
    x = np.arange(len(seg))
    for k, (app, col) in enumerate((("APP_B", GREY), ("APP_D", BLUE))):
        v = [float(s[(s.level == lv) & (s.segment == sg) & (s.app == app)].trial_to_paid.iloc[0]) for lv, sg, _ in seg]
        ax.bar(x + (k - .5) * .38, v, .38, color=col, label=app)
        for xi, vi in zip(x + (k - .5) * .38, v):
            ax.text(xi, vi + .006, f"{vi:.0%}", ha="center", fontsize=8.5)
    ax.set_xticks(x, [lab for *_, lab in seg])
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1))
    ax.set_title("Trial -> paid: APP_D wins in each region")
    ax.legend(fontsize=8)
    save(fig, "p5_simpson", "SIMULATED")


def duplicates():
    d = o("dq_daily")
    d["date_utc"] = pd.to_datetime(d.date_utc)
    fig, ax = plt.subplots(figsize=(4.4, 4.0))
    ax.bar(d.date_utc, d.raw_installed, color=RED, alpha=.35, label="raw 'installed' webhooks")
    ax.bar(d.date_utc, d.clean_installs, color=BLUE, label="clean installs")
    ax.set_title("Webhook retries, 14-15 July 2026")
    ax.legend(fontsize=8)
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d %b"))
    ax.tick_params(axis="x", labelsize=8)
    save(fig, "p5_duplicates", "SIMULATED")


def positions():
    c = o("category_summary")
    fig, ax = plt.subplots(figsize=(4.6, 2.5))
    y = np.arange(len(c))
    ax.hlines(y, c.hero_review_rank, c.hero_position, color=GRID, lw=3)
    ax.scatter(c.hero_review_rank, y, color=BLUE, s=40, zorder=3, label="rank by number of reviews")
    ax.scatter(c.hero_position, y, color=ORANGE, s=40, zorder=3, label="position shown")
    ax.set_yticks(y, c.herosoftware_app.str.replace("Post Purchase ", ""))
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(mtick.ScalarFormatter())
    ax.set_xlabel("rank in its category (log scale, 1 = first)")
    ax.set_title("Shown position vs review rank, per app")
    ax.legend(fontsize=7.5, loc="lower right")
    save(fig, "p1_positions", "PUBLIC DATA")


def replies():
    b = o("reviews_by_app").sort_values("reviews")
    fig, ax = plt.subplots(figsize=(4.6, 2.3))
    ax.barh(b.app.str.replace("Post Purchase ", ""), b.reply_rate, color=[BLUE if v > .5 else RED for v in b.reply_rate])
    for y, (v, n) in enumerate(zip(b.reply_rate, b.reviews)):
        ax.text(max(v, 0) + .02, y, f"{v:.0%} of {n} reviews", va="center", fontsize=8.5)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(1))
    ax.set_xlim(0, 1.45)
    ax.set_title("Share of reviews with a developer reply")
    save(fig, "p1_replies", "PUBLIC DATA")


def eurostat():
    e = o("eurostat").dropna().sort_values("pct_enterprises_selling_online_b2c")
    fig, ax = plt.subplots(figsize=(3.6, 2.6))
    ax.barh(e.geo, e.pct_enterprises_selling_online_b2c, color=[BLUE if g in ("ES", "NL", "SE") else LIGHT for g in e.geo])
    for y, v in enumerate(e.pct_enterprises_selling_online_b2c):
        ax.text(v + .3, y, f"{v:.1f}%", va="center", fontsize=8.5)
    ax.set_xlim(0, 27)
    ax.set_title("Enterprises selling online to consumers, 2024")
    save(fig, "p6_eurostat", "PUBLIC DATA")


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    for fn in (reviews_monthly, countries, category_scatter, free_plan, scorecard, quality, funnel, forest, exp03, exp04,
               bfcm, brand, simpson, duplicates, eurostat, positions, replies):
        fn()
    print(len(list(IMG.glob("*.png"))), "charts in report/img/")


if __name__ == "__main__":
    main()
