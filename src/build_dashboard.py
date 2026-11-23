"""Build dashboard/index.html: a self-contained Plotly dashboard with 5 tabs (Overview, App Store shelf, Channels,
Experiments, Data quality). Plotly.js is inlined once; each chart carries a PUBLIC DATA or SIMULATED label.

Run:  python src/build_dashboard.py
"""
import json
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.offline import get_plotlyjs

sys.path.insert(0, str(Path(__file__).resolve().parent))
import facts  # noqa: E402
from charts import APP_COL, DEC_COL, LABEL  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT, DASH = ROOT / "data" / "out", ROOT / "dashboard"
BLUE, GREY, RED, ORANGE, GREEN = "#2A78D6", "#A3A19A", "#D03B3B", "#EB6834", "#1B7F55"
FOOT = "Independent case study based on public data · not affiliated with or endorsed by HeroSoftware GmbH or Shopify"


def o(n):
    return pd.read_csv(OUT / f"{n}.csv")


def fig_html(fig, tag, title, height=340):
    fig.update_layout(title=dict(text=title, x=0.01, font=dict(size=14)), height=height, margin=dict(l=50, r=20, t=50, b=40),
                      font=dict(family="Segoe UI, Arial", size=12, color="#2B2A27"), plot_bgcolor="white", paper_bgcolor="white",
                      legend=dict(orientation="h", y=-0.18))
    fig.update_xaxes(gridcolor="#EFEEE9")
    fig.update_yaxes(gridcolor="#EFEEE9")
    cls = "pub" if tag == "PUBLIC DATA" else "sim"
    return f'<div class="card"><span class="tag {cls}">{tag}</span>{fig.to_html(full_html=False, include_plotlyjs=False, config={"displaylogo": False})}</div>'


def tab_overview(F):
    P, S = F["public"], F["sim"]
    k = [("Public reviews", f"{P['reviews']}", f"4 apps, as observed on {F['collected']}", "PUBLIC DATA"),
         ("German-speaking reviews", f"{P['share_dach']:.1%}", f"Germany alone {P['share_germany']:.1%}", "PUBLIC DATA"),
         ("Translated listing (DiD)", f"{S['exp03']['did']:+.0%}", f"naive before/after {S['exp03']['naive']:+.0%}", "SIMULATED"),
         ("Brand conversions incremental", f"{S['brand']['share']:.0%}", f"of {S['brand']['claimed']} claimed", "SIMULATED")]
    tiles = "".join(f'<div class="card tile"><span class="tag {"pub" if t == "PUBLIC DATA" else "sim"}">{t}</span><div class="lab">{a}</div>'
                    f'<div class="big">{b}</div><div class="sub">{c}</div></div>' for a, b, c, t in k)
    d = S["decisions"]
    fig = go.Figure(go.Bar(x=list(d.keys()), y=list(d.values()), marker_color=[DEC_COL[x] for x in d], text=list(d.values()), textposition="outside"))
    recs = """<div class="card"><h3>Five bets for the first 90 days</h3><ol>
<li>Localise listings: FR and IT, then ES.</li><li>Ask for reviews at the first value moment.</li>
<li>Reply to every review on the payment-rules app.</li><li>Cross-promote inside the apps.</li>
<li>Comparison SEO pages; move brand-search budget to intent keywords.</li></ol>
<p class="note">Details: docs/90_day_growth_plan.md. Public facts on HeroSoftware are labelled PUBLIC DATA; everything about installs,
revenue, spend and experiments is SIMULATED for fictional apps A-D.</p></div>"""
    return f'<div class="grid4">{tiles}</div><div class="grid2">{fig_html(fig, "SIMULATED", "24 experiments by decision")}{recs}</div>'


def tab_shelf():
    m = o("reviews_monthly")
    fig1 = go.Figure([go.Bar(x=g.month, y=g.reviews, name=a, marker_color=APP_COL[a]) for a, g in m.groupby("app")])
    fig1.update_layout(barmode="stack")
    c = o("reviews_country")
    fig2 = go.Figure(go.Bar(y=c.country, x=c.share, orientation="h", marker_color=BLUE, text=[f"{v:.1%}" for v in c.share], textposition="outside"))
    fig2.update_yaxes(autorange="reversed")
    fig2.update_xaxes(tickformat=".0%")
    s = o("category_scatter")
    fig3 = go.Figure()
    names = {"marketing-and-conversion-checkout-checkout-other": "Checkout - Other", "orders-and-shipping-shipping-solutions-shipping": "Shipping",
             "store-management-security-fraud": "Fraud", "marketing-and-conversion-upsell-and-bundles-upsell-and-cross-sell": "Upsell and cross-sell"}
    for cat, g in s.groupby("category"):
        fig3.add_trace(go.Scatter(x=g.position, y=g.total_reviews, mode="markers", name=names.get(cat, cat),
                                  marker=dict(size=[14 if h else 6 for h in g.is_herosoftware], line=dict(width=[2 if h else 0 for h in g.is_herosoftware], color=INK)),
                                  text=g.handle, hovertemplate="%{text}<br>position %{x}<br>%{y} reviews"))
    fig3.update_yaxes(type="log", title="total reviews")
    fig3.update_xaxes(title="position shown (default order, observed once)")
    cs = o("category_summary")
    fig4 = go.Figure([go.Bar(x=cs.herosoftware_app, y=cs.free_plan_top30, name="top 30", marker_color=GREEN),
                      go.Bar(x=cs.herosoftware_app, y=cs.free_plan_rest, name="position 31+", marker_color=GREY)])
    fig4.update_yaxes(tickformat=".0%")
    t = o("reviews_by_app")[["app", "reviews", "avg_stars", "share_dach", "reply_rate", "last_review", "reviews_since_2026_03"]]
    table = t.to_html(index=False, classes="tbl", float_format=lambda v: f"{v:.3f}")
    return (f'<div class="grid2">{fig_html(fig1, "PUBLIC DATA", "Public reviews per month, by app")}{fig_html(fig2, "PUBLIC DATA", "Reviews by country (fewer than 5 grouped as Other)")}</div>'
            f'<div class="grid2">{fig_html(fig3, "PUBLIC DATA", "Category shelves: position vs reviews (big markers = HeroSoftware apps)", 380)}'
            f'{fig_html(fig4, "PUBLIC DATA", "Share of apps with a free plan, by HeroSoftware category")}</div>'
            f'<div class="card"><span class="tag pub">PUBLIC DATA</span><h3>Reviews by app</h3>{table}<p class="note">A review is an indirect signal, '
            f'not an install. No shop name, review text or reply text collected.</p></div>')


def tab_channels():
    s = o("channel_scorecard")
    p = s[s.spend_eur > 0].sort_values("cac_per_paying")
    col = [RED if c == "app_store_ads" else BLUE for c in p.channel]
    fig1 = go.Figure(go.Bar(y=p.channel.map(LABEL), x=p.cac_per_paying, orientation="h", marker_color=col, text=[f"EUR {v:,.0f}" for v in p.cac_per_paying], textposition="outside"))
    fig2 = go.Figure(go.Bar(y=p.channel.map(LABEL), x=p.payback_months, orientation="h", marker_color=col, text=[f"{v:.1f}" for v in p.payback_months], textposition="outside"))
    fig3 = go.Figure(go.Scatter(x=s.uninstall_48h_rate, y=s.trial_to_paid, mode="markers+text", text=s.channel.map(LABEL), textposition="top center",
                                marker=dict(size=(s.installs ** .5) * 1.2, color=[RED if c == "app_store_ads" else BLUE for c in s.channel], opacity=.7)))
    fig3.update_xaxes(tickformat=".0%", title="uninstalled within 48 h")
    fig3.update_yaxes(tickformat=".0%", title="trial -> paid")
    f = o("funnel_total")
    fig4 = go.Figure(go.Funnel(y=f.step, x=f.n, marker_color=BLUE))
    tbl = s[["channel", "installs", "uninstall_48h_rate", "trial_to_paid", "spend_eur", "cost_per_install", "cac_per_paying", "mrr_per_paying_d60", "payback_months"]]
    return (f'<div class="grid2">{fig_html(fig1, "SIMULATED", "CAC per paying merchant (EUR)")}{fig_html(fig2, "SIMULATED", "Payback (months)")}</div>'
            f'<div class="grid2">{fig_html(fig3, "SIMULATED", "Install quality by channel (size = installs)", 380)}{fig_html(fig4, "SIMULATED", "Funnel: listing views to paying at day 60", 380)}</div>'
            f'<div class="card"><span class="tag sim">SIMULATED</span><h3>Scorecard</h3>{tbl.to_html(index=False, classes="tbl", na_rep="-")}</div>')


def tab_experiments():
    r = o("experiment_readouts").sort_values("exp_id", ascending=False)
    fig1 = go.Figure()
    for d, g in r.groupby("decision"):
        fig1.add_trace(go.Scatter(x=g.lift, y=g.exp_id + " " + g.title.str[:40], mode="markers", name=d, marker=dict(color=DEC_COL[d], size=9),
                                  error_x=dict(type="data", symmetric=False, array=g.ci_high - g.lift, arrayminus=g.lift - g.ci_low, color=DEC_COL[d])))
    fig1.add_vline(x=0, line_color="#0B0B0B", line_width=1)
    fig1.update_xaxes(tickformat=".0%", range=[-1, 2.3], title="relative lift, 95% CI")
    fig1.update_yaxes(categoryorder="array", categoryarray=list(r.exp_id + " " + r.title.str[:40]))
    w = o("exp03_weekly")
    fig2 = go.Figure([go.Scatter(x=w.week, y=w.treated_fr_it, name="FR + IT (translated)", line_color=BLUE),
                      go.Scatter(x=w.week, y=w.control_es_nl_pl, name="ES + NL + PL (control)", line_color=GREY)])
    fig2.add_vline(x="2026-03-02", line_dash="dash")
    tbl = r.sort_values("exp_id")[["exp_id", "channel", "title", "ice_score", "design", "primary_metric", "lift", "ci_low", "ci_high", "rule_call", "decision", "learned"]]
    return (f'{fig_html(fig1, "SIMULATED", "24 experiments: lift, 95% CI and decision", 720)}'
            f'{fig_html(fig2, "SIMULATED", "EXP03: APP_B weekly installs, translated vs control countries")}'
            f'<div class="card"><span class="tag sim">SIMULATED</span><h3>Experiment log</h3>'
            f'{tbl.to_html(index=False, classes="tbl small", float_format=lambda v: f"{v:.2f}")}</div>')


def tab_quality(F):
    d = o("dq_daily")
    fig1 = go.Figure([go.Bar(x=d.date_utc, y=d.raw_installed, name="raw 'installed' webhooks", marker_color=RED, opacity=.4),
                      go.Bar(x=d.date_utc, y=d.clean_installs, name="clean installs", marker_color=BLUE)])
    fig1.update_layout(barmode="overlay")
    di = o("daily_installs")
    di = di[(di.date >= "2025-11-03") & (di.date <= "2025-12-21")]
    a = di[di.app == "APP_A"].groupby("date").installs.sum()
    b = di[di.app.isin(["APP_B", "APP_C"])].groupby("date").installs.sum()
    fig2 = go.Figure([go.Scatter(x=a.index, y=a.rolling(3, min_periods=1).mean(), name="APP_A (promoted on LinkedIn)", line_color=BLUE),
                      go.Scatter(x=b.index, y=b.rolling(3, min_periods=1).mean(), name="APP_B + APP_C (not promoted)", line_color=GREY)])
    fig2.add_vrect(x0="2025-11-24", x1="2025-12-01", fillcolor="#FBE9E0", line_width=0, annotation_text="Black Friday week")
    br = F["sim"]["brand"]
    fig3 = go.Figure(go.Bar(x=["Claimed by the platform", "Incremental (geo holdout)"], y=[br["claimed"], br["incremental"]], marker_color=[GREY, BLUE],
                            text=[br["claimed"], br["incremental"]], textposition="outside"))
    sm = o("simpson")
    sm = sm[sm.level != "country"]
    fig4 = go.Figure([go.Bar(x=g.segment, y=g.trial_to_paid, name=app, marker_color=GREY if app == "APP_B" else BLUE) for app, g in sm.groupby("app")])
    fig4.update_yaxes(tickformat=".0%")
    dq = o("dq_summary")[["item", "n"]]
    ms = o("dq_month_shift")
    return (f'<div class="grid2">{fig_html(fig1, "SIMULATED", "Webhook retries on 14-15 July 2026: raw vs clean")}'
            f'<div class="card"><span class="tag sim">SIMULATED</span><h3>Cleaning summary (sql/01_staging.sql)</h3>{dq.to_html(index=False, classes="tbl")}'
            f'<h3>Monthly installs, Europe/Berlin vs UTC dates</h3>{ms.to_html(index=False, classes="tbl small")}</div></div>'
            f'<div class="grid3">{fig_html(fig2, "SIMULATED", "False signal: LinkedIn push in Black Friday week")}{fig_html(fig3, "SIMULATED", "Google Ads brand: claimed vs incremental")}'
            f'{fig_html(fig4, "SIMULATED", "Simpson: trial -> paid, APP_B vs APP_D")}</div>')


INK = "#0B0B0B"
CSS = """body{margin:0;font-family:'Segoe UI',Arial,sans-serif;background:#F4F4F2;color:#0B0B0B}
header{padding:18px 28px 6px}h1{font-size:22px;margin:0}header p{margin:4px 0;color:#52514E;font-size:13px}
nav{padding:0 28px;display:flex;gap:6px;border-bottom:1px solid #E1E0D9}nav button{border:0;background:none;padding:10px 14px;font:inherit;
font-size:14px;color:#52514E;cursor:pointer;border-bottom:3px solid transparent}nav button.on{color:#0B0B0B;border-bottom-color:#2A78D6;font-weight:600}
section{display:none;padding:16px 28px}section.on{display:block}.card{background:#FCFCFB;border:1px solid #E1E0D9;border-radius:8px;padding:12px 14px;
margin-bottom:14px;position:relative;overflow-x:auto}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}.grid3{display:grid;
grid-template-columns:1fr 1fr 1fr;gap:14px}.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
.tag{position:absolute;right:10px;top:8px;font-size:10px;font-weight:700;letter-spacing:.06em;padding:3px 7px;border-radius:4px;z-index:2}
.pub{background:#E3EEFB;color:#1C5CAB}.sim{background:#FBE9E0;color:#9A3B12}.tile .lab{font-size:12px;font-weight:700;color:#52514E;margin-top:14px}
.tile .big{font-size:34px;font-weight:700}.tile .sub{font-size:12px;color:#52514E}.tbl{border-collapse:collapse;font-size:12.5px;width:100%}
.tbl th{text-align:left;border-bottom:1px solid #E1E0D9;color:#52514E;padding:4px 6px}.tbl td{border-bottom:1px solid #EFEEE9;padding:4px 6px}
.small{font-size:11.5px}.note{font-size:11.5px;color:#6B6A65}h3{margin:4px 0 8px;font-size:15px}footer{padding:10px 28px 24px;font-size:11px;color:#898781}"""


def main():
    F = facts.build()
    tabs = [("Overview", tab_overview(F)), ("App Store shelf", tab_shelf()), ("Channels", tab_channels()),
            ("Experiments", tab_experiments()), ("Data quality", tab_quality(F))]
    nav = "".join(f'<button data-t="t{i}" class="{"on" if i == 0 else ""}">{n}</button>' for i, (n, _) in enumerate(tabs))
    secs = "".join(f'<section id="t{i}" class="{"on" if i == 0 else ""}">{h}</section>' for i, (_, h) in enumerate(tabs))
    js = """document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{document.querySelectorAll('nav button,section').forEach(e=>e.classList.remove('on'));
b.classList.add('on');const s=document.getElementById(b.dataset.t);s.classList.add('on');s.querySelectorAll('.js-plotly-plot').forEach(p=>Plotly.Plots.resize(p));});"""
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HeroSoftware growth case study - dashboard</title><style>{CSS}</style><script>{get_plotlyjs()}</script></head><body>
<header><h1>HeroSoftware: where the next 1,000 merchants come from</h1><p>Public Shopify App Store data (collected {F['collected']}) + SIMULATED growth data
for a fictional 4-app portfolio (APP_A-APP_D). Simulated figures are never HeroSoftware's.</p></header><nav>{nav}</nav>{secs}
<footer>{FOOT}</footer><script>{js}</script></body></html>"""
    DASH.mkdir(exist_ok=True)
    (DASH / "index.html").write_text(html, encoding="utf-8")
    print(f"dashboard/index.html: {len(html) / 1e6:.1f} MB, {len(tabs)} tabs")


if __name__ == "__main__":
    main()
    _ = json
