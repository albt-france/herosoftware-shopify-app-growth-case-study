"""Build the 7-page PDF (report/HeroSoftware_growth_case_study.pdf): HTML pages (pdf_common) printed by headless Edge.
Every number comes from data/out/facts.json (public data + SQL outputs on simulated data).

Run:  python src/build_pdf.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import charts  # noqa: E402
import facts  # noqa: E402
from pdf_common import card, html_doc, img, page, print_pdf, tile  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "report"
AI_NOTE = ("AI-assisted workflow: I used Claude, mainly to write scripts faster. I drove the project: I defined the questions, "
           "chose and validated the data sources, made the analytical decisions and checked every result.")
TITLE = "HeroSoftware: where the next 1,000 merchants come from - a test-and-kill growth system for four Shopify apps"


def pct(x, d=0, sign=False):
    s = f"{x * 100:+.{d}f}%" if sign else f"{x * 100:.{d}f}%"
    return s.replace("-", "−")


def build(F) -> list[str]:
    P, S, col = F["public"], F["sim"], F["collected"]
    cat, apps = P["categories"], {a["short_name"]: a for a in F["apps"]}
    e03, e04, br, rv, bf, sp, me = S["exp03"], S["exp04"], S["brand"], S["reviews"], S["bfcm"], S["simpson"], S["meta"]
    sc = {r["channel"]: r for r in S["scorecard"]}
    eu = P["eurostat_2024"]
    dec = S["decisions"]
    src_pub = "Sources: Shopify App Store listings, reviews and category pages; hero.software; join.com"
    src_sim = "SIMULATED data for a fictional 4-app portfolio (APP_A-APP_D), seed 42; never HeroSoftware's figures"
    coll = f"collected {col}"
    pages = []

    # ---------- 0 Overview ----------
    qs = f"""<h2>Five questions</h2><ul class="qs" style="list-style:none;padding-left:0">
<li><b>1</b>Where does demand come from today? <span class="k">PUBLIC</span> {pct(P['share_dach'], 1)} of {P['reviews']} public reviews come from Germany, Austria and Switzerland.</li>
<li><b>2</b>Does each listing pull its weight on the shelf? <span class="k">PUBLIC</span> PaymentHero is 7th by reviews in its category but shown 30th; no reply to its reviews yet.</li>
<li><b>3</b>Which channels pay back? <span class="k">SIM</span> Partners, e-mail and content pay back in under 5 months; App Store ads take {sc['app_store_ads']['payback_months']:.0f}.</li>
<li><b>4</b>How do we know a test worked? <span class="k">SIM</span> Controls, holdouts and an MDE written down before launch, never a before/after alone.</li>
<li><b>5</b>What do we stop? <span class="k">SIM</span> {dec.get('Kill', 0)} of 24 tests killed: App Store ads, most of the brand budget, low-volume social.</li></ul>"""
    recs = f"""<h2>Five bets for the first 90 days</h2><ol>
<li><b>Localise the listings</b> (FR, IT, then ES): in the simulation a translated listing lifts installs by {pct(e03['did'], 0, True)} vs control countries. ES first among new markets: {eu['ES']:.1f}% of enterprises sell online to consumers (Eurostat 2024).</li>
<li><b>Ask for the review at the first value moment</b>, not on day 2: review rate ×{1 + rv['lift']:.1f} in the simulated test, stars unchanged.</li>
<li><b>Reply to every PaymentHero review</b> ({pct(P['reply_rate']['PaymentHero'])} today vs {pct(P['reply_rate']['AddressHero'])} on AddressHero).</li>
<li><b>Cross-promote inside the apps</b> (payment rules → post-purchase upsell): own base, near-zero cost.</li>
<li><b>Comparison SEO pages</b> per app, and move brand-search money to intent keywords.</li></ol>"""
    method = """<h2>Method in 3 lines</h2><p><b>Real:</b> 4 listings, 514 public reviews, 4 category shelves (2,568 apps), Eurostat, ECB.
<b>Simulated:</b> 12 months, 4 fictional apps, ~9,400 installs, 9 channels, 24 experiments with 8 hidden events to find.
<b>Tools:</b> Python, DuckDB SQL (11 scripts with tests), Excel tracker with live formulas, HTML dashboard.</p>"""
    body = f"""<div class="row c4 auto">{tile('PUBLIC REVIEWS', str(P['reviews']), f"4 apps, {pct(P['share_5_star'], 1)} five-star, as observed on {col}")}
{tile('GERMAN-SPEAKING', pct(P['share_dach'], 1), f"of reviews from DE, AT, CH ({pct(P['share_germany'], 1)} Germany alone)")}
{tile('TRANSLATED LISTING', pct(e03['did'], 0, True), f"SIMULATED: installs FR+IT vs control (DiD); naive read {pct(e03['naive'], 0, True)}")}
{tile('BRAND ADS THAT ARE INCREMENTAL', pct(br['share']), f"SIMULATED: of {br['claimed']} conversions claimed by the platform (geo holdout)")}</div>
<div class="row c2"><div class="stack">{card(qs)}{card(method, 'auto')}</div><div class="stack">{card(recs, 'auto')}{card(img('img/p2_reviews_monthly.png', 'The shelf in one chart: reviews per month (PUBLIC DATA)'), 'fc')}</div></div>"""
    pages.append(page(0, TITLE, "Four 'Built for Shopify' apps rated 4.9+, a review base that is 93% German-speaking, and one simulated year of "
                      "growth work showing how I would test channels, read results honestly, scale what works and kill what does not.",
                      "OVERVIEW", body, "Public data + simulated data (labelled on every visual)", coll))

    # ---------- 1 HeroSoftware and the job ----------
    rows = "".join(
        f"<tr><td><b>{n}</b><br><span class='note'>{a['listing_name']}</span></td><td>{a['launched']}</td>"
        f"<td>{a['rating']} ({a['rating_count']})</td><td>{a['pricing'].replace('. ', '<br>')}</td><td>{a['categories_display']}</td>"
        f"<td>{cat[n]['position']} of {cat[n]['apps']:,}</td></tr>"
        for n, a in apps.items())
    tab = f"""<h2>The four apps, as observed on the Shopify App Store on {col}</h2>
<table class="small"><tr><th>App</th><th>Launched</th><th>Rating (reviews)</th><th>Pricing</th><th>Category</th><th>Shown at</th></tr>{rows}</table>
<p class="note">All four carry the "Built for Shopify" badge. DiscountHero "only works with Shopify Plus". "Shown at" = position in the category's default
order (logged-out view), observed once; not Shopify's ranking algorithm.</p>"""
    comp = f"""<h2>The company, as stated</h2><ul>
<li>HeroSoftware GmbH, Idstein (Hesse), {F['company']['register']} (legal notice, hero.software).</li>
<li>11-50 employees (join.com company profile).</li>
<li>"Over 4,000 customers worldwide" (join.com company profile) and "over 3,500 Shopify merchants" (job ad), as stated by HeroSoftware.</li>
<li>Job ad on join.com created {F['company']['job_createdAt']}, updated {F['company']['job_updatedAt']}: permanent, full-time,
EUR {F['company']['job_salary_eur_per_year'].replace('-', ' - ')} per year, 100% remote within Germany.</li></ul>"""
    missions = [
        ("Test new channels; find what works for Shopify merchants, and what does not",
         "9 channels compared on CAC, payback and 60-day quality (p.3); 24 tests across Paid, SEO, Content, E-mail, Social, App Store, Partners (p.4)."),
        ("Run experiments, measure, draw clear conclusions",
         "Playbook: hypothesis, ICE, sample size and MDE before launch, guardrails, no peeking; every test ends in one of 4 decisions (p.4)."),
        ("Scale what works, stop what does not, clearly",
         f"{dec.get('Scale', 0)} scaled, {dec.get('Kill', 0)} killed, {dec.get('Rerun', 0)} rerun, {dec.get('Inconclusive', 0)} inconclusive; App Store ads and most brand spend stopped (p.4-5)."),
        ("Work on Paid, SEO, Content, E-mail and Social",
         "One-page playbook per channel with the first test, metric, cost and stop rule (docs/channel_playbooks.md)."),
        ("Do it yourself rather than coordinate or build reports",
         "Listing audit with 10 concrete fixes, test plans ready to launch, an Excel tracker that decides by formula (p.2, docs, excel)."),
    ]
    mt = "".join(f"<tr><td><b>{i + 1}.</b> {m}</td><td>{s}</td></tr>" for i, (m, s) in enumerate(missions))
    body = f"""<div class="row c32 auto">{card(tab)}{card(comp)}</div>
<div class="row c21">{card(f'<h2>The five missions of the job ad (translated from German), and what this study shows for each</h2><table><tr><th style="width:38%">Mission</th><th>In this study</th></tr>{mt}</table>')}<div class="stack">{card(img('img/p1_positions.png'), 'fc')}{card(img('img/p1_replies.png'), 'fc')}</div></div>"""
    pages.append(page(1, "A small team with four 4.9-rated apps, hiring someone who tests, decides and does the work",
                      "Published facts only: listings, legal notice, job ad. Customer counts are quoted as stated by HeroSoftware, with their source.",
                      "PUBLIC DATA", body, src_pub, coll))

    # ---------- 2 The App Store shelf ----------
    find = f"""<h2>What the listings and reviews show (growth levers, not criticism)</h2><ul class="small">
<li><b>Language:</b> all 4 listings declare "English" only, yet the short description is in German for AddressHero and PaymentHero and empty for DiscountHero.</li>
<li><b>Review rhythm:</b> {pct(P['share_may_jun_2025'], 1)} of all reviews ({P['may_jun_2025']}) were posted in May-June 2025, with days of 20 reviews,
consistent with a review-request push; public data cannot tell how reviews were requested.</li>
<li><b>Momentum:</b> last PaymentHero review on {P['last_review']['PaymentHero']}; since March 2026, {P['upsell_since_2026_03']} of {P['since_2026_03']} new reviews went to Post Purchase Upsell Hero.</li>
<li><b>Replies:</b> AddressHero {pct(P['reply_rate']['AddressHero'])}, Upsell Hero {pct(P['reply_rate']['Post Purchase Upsell Hero'])}, PaymentHero {pct(P['reply_rate']['PaymentHero'])},
DiscountHero {pct(P['reply_rate']['DiscountHero'])}; {P['replies_2026_11_09']} replies are dated 9 Nov 2026 (one catch-up session).</li>
<li><b>Timing:</b> {pct(P['share_tenure_days'], 1)} of reviews are written after a tenure counted in days: the prompt moment drives reviews.</li>
<li><b>Shelf:</b> in all 4 categories, apps shown in the top 30 have a free plan far more often (50-67%) than the rest (7-27%): correlation, not causation.</li></ul>
<p class="note">A review is an indirect signal, not an install; the review-per-install rate is unknown. Category order observed once, logged out.</p>"""
    body = f"""<div class="row c21">{card(img('img/p2_reviews_monthly.png'))}{card(img('img/p2_countries.png'))}</div>
<div class="row c3">{card(img('img/p2_category_scatter.png'))}{card(img('img/p2_free_plan.png'))}{card(find)}</div>"""
    pages.append(page(2, f"The shelf: {pct(P['share_dach'], 0)} of reviews are German-speaking, and PaymentHero is shown 30th while 7th by reviews",
                      f"Reviews and category pages as observed on the Shopify App Store on {col}. No shop name, review text or reply text was collected.",
                      "PUBLIC DATA", body, src_pub + "; countries with fewer than 5 reviews grouped as Other", coll))

    # ---------- 3 Channels ----------
    paid = [c for c in ("partner", "email", "content", "google_ads_nonbrand", "google_ads_brand", "app_store_ads")]
    tr = "".join(f"<tr><td>{charts.LABEL[c]}</td><td>{sc[c]['installs']:,}</td><td>{pct(sc[c]['uninstall_48h_rate'])}</td>"
                 f"<td>{pct(sc[c]['trial_to_paid'])}</td><td>EUR {sc[c]['cac_per_paying']:,.0f}</td>"
                 f"<td class='{'drop' if sc[c]['payback_months'] > 12 else 'ok'}'>{sc[c]['payback_months']:.1f}</td></tr>" for c in paid)
    organic = sum(sc[c]["installs"] for c in ("app_store_search", "category_browse", "direct"))
    allin = sum(r["installs"] for r in S["scorecard"])
    txt = f"""<h2>Read-out</h2><ul class="small">
<li><b>The App Store itself is the main channel:</b> search, category browse and direct bring {pct(organic / allin)} of installs at no media cost.
Listing work (language, title, reviews) is therefore the first growth lever.</li>
<li><b>What pays:</b> agency partners (best trial→paid, {pct(sc['partner']['trial_to_paid'])}), lifecycle e-mail and content pay back in under 5 months.</li>
<li><b>What does not:</b> App Store ads: {pct(sc['app_store_ads']['uninstall_48h_rate'])} uninstall within 48 h, CAC EUR {sc['app_store_ads']['cac_per_paying']:,.0f}
vs EUR {e04['cac_other_paid']:,.0f} for the other paid channels together.</li>
<li><b>Brand search</b> looks cheap per conversion only because the platform counts conversions that would have happened anyway (p.5).</li></ul>
<table class="small"><tr><th>Channel</th><th>Installs</th><th>Uninst. 48h</th><th>Trial→paid</th><th>CAC</th><th>Payback (m)</th></tr>{tr}</table>
<p class="note">Cohort: installs Nov 2025-Aug 2026, MRR at day 60 in EUR (ECB monthly rate). CAC = spend / paying merchants.</p>"""
    body = f"""<div class="row c21">{card(img('img/p3_cac_payback.png'))}{card(img('img/p3_funnel.png'))}</div>
<div class="row c12">{card(img('img/p3_quality.png'))}{card(txt)}</div>"""
    pages.append(page(3, "Where merchants come from: partners, e-mail and content pay back in under 5 months; App Store ads never do",
                      "Channel scorecard of the fictional portfolio: cost per install is not the point, cost per paying merchant and 60-day quality are.",
                      "SIMULATED", body, src_sim, "simulated period 2025-11-01 to 2026-10-31"))

    # ---------- 4 Test, scale or kill ----------
    t1 = f"""<h3>Translated listing (EXP03): scale</h3><p>FR+IT installs vs ES+NL+PL: naive before/after {pct(e03['naive'], 0, True)}
(spring helps everyone: controls {pct(e03['control'], 0, True)}). Difference-in-differences: <b>{pct(e03['did'], 0, True)}</b>
(95% CI {pct(e03['lo'], 0)} to {pct(e03['hi'], 0, True)}). Listing views, 14× more events, confirm it: {pct(e03['views_did'], 0, True)}
(CI {pct(e03['views_lo'], 0, True)} to {pct(e03['views_hi'], 0, True)}). Next: Spanish.</p>"""
    t2 = f"""<h3>App Store ads (EXP04): kill</h3><p>+{e04['installs_ads']} installs in 8 weeks, but {pct(e04['uninstall_ads'])} uninstall within 48 h
(organic {pct(e04['uninstall_org'])}) and trial→paid {pct(e04['t2p_ads'], 1)} vs {pct(e04['t2p_org'], 1)}. CAC EUR {e04['cac_ads']:,.0f}: about
{e04['cac_ads'] / e04['cac_other_paid']:.0f}× the other paid channels.</p>"""
    t3 = f"""<h3>Review prompt at the value moment (EXP01): scale</h3><p>Randomised: review rate {pct(rv['rate_day2'], 1)} → {pct(rv['rate_value'], 1)}
({pct(rv['lift'], 0, True)}, CI {pct(rv['lo'], 0, True)} to {pct(rv['hi'], 0, True)}); stars {rv['stars_day2']:.1f} vs {rv['stars_value']:.1f}, no drop.</p>"""
    t4 = f"""<h3>Meta prospecting, 3 weeks, EUR 2,400 (EXP06): inconclusive</h3><p>{pct(me['lift'], 0, True)} trials (p = {me['p']:.2f}) but the test could only see
{pct(me['mde'], 0)} (MDE). Not a failure, not a win. Seeing +8% needs ~{me['n_needed_8pct'] / 1000:,.0f}k reached stores per arm
(≈{me['weeks_needed_8pct']:.0f} weeks, EUR {me['budget_needed_8pct']:,.0f}): not worth it now.</p>"""
    body = f"""<div class="row c2"><div class="stack">{card(img('img/p4_forest.png'))}</div>
<div class="stack">{card(t1 + img('img/p4_exp03.png'), 'f13 fc')}<div class="row c2">{card(t2 + img('img/p4_exp04.png'), 'fc')}{card(t3 + t4)}</div></div></div>"""
    pages.append(page(4, f"Test, scale or kill: {dec.get('Scale', 0)} scaled, {dec.get('Kill', 0)} killed; translation works, App Store ads do not, "
                      "and 3 weeks of Meta prove nothing either way",
                      "Every test: hypothesis, ICE score, sample size and MDE before launch, a guardrail, one decision. Decision rules in docs/growth_experiment_playbook.md.",
                      "SIMULATED", body, src_sim, "24 experiments, Dec 2025 - Oct 2026"))

    # ---------- 5 Don't fool yourself ----------
    c1 = f"""<h3>Black Friday is not a channel</h3><p>LinkedIn push for APP_A launched 24 Nov 2025: APP_A installs {pct(bf['naive'], 0, True)} per day.
The apps not promoted rose {pct(bf['not_promoted'], 0, True)}. DiD {pct(bf['did'], 0, True)} (CI {pct(bf['lo'], 0, True)} to {pct(bf['hi'], 0, True)}):
no evidence it worked. Do not scale; re-test off-season.</p>"""
    c2 = f"""<h3>The platform grades its own homework</h3><p>Google Ads claims {br['claimed']} brand conversions. A 4-week geo holdout says only
{pct(br['share'])} are incremental (CI {pct(br['lo'])} to {pct(br['hi'])}): ≈{br['incremental']} merchants. Cost per incremental conversion
EUR {br['cost_incremental']:,.0f}, not EUR {br['cost_claimed']:,.0f}. Keep a defensive minimum, move the rest.</p>"""
    c3 = f"""<h3>Simpson's paradox</h3><p>APP_D converts worse overall ({pct(sp['d_all'], 1)} vs {pct(sp['b_all'], 1)} for APP_B) but better in DACH
({pct(sp['d_dach'], 1)} vs {pct(sp['b_dach'], 1)}) and outside ({pct(sp['d_non'], 1)} vs {pct(sp['b_non'], 1)}): {pct(sp['mix']['APP_D'])} of its trials come
from outside DACH, where everyone converts less. Compare like with like.</p>"""
    c4 = f"""<h3>Clean before you count</h3><p>{S['dup_removed']:,} duplicated "installed" webhooks (retries on 14-15 July 2026), {S['quick_reinstalls']}
re-installs within 24 h counted as new, and month totals that move when dates stay in UTC ({S['month_shift']} installs here).
Fixed in sql/01_staging.sql; logged in docs/data_issues_log.md.</p>"""
    body = f"""<div class="row c4">{card(c1 + img('img/p5_bfcm.png'), 'fc')}{card(c2 + img('img/p5_brand.png'), 'fc')}{card(c3 + img('img/p5_simpson.png'), 'fc')}{card(c4 + img('img/p5_duplicates.png'), 'fc')}</div>"""
    pages.append(page(5, "Don't fool yourself: Black Friday, platform attribution, Simpson's paradox and webhook retries all tell a better story than the truth",
                      "Four traps hidden in the simulated data, and the check that catches each one before it becomes a budget decision.",
                      "SIMULATED", body, src_sim, "checks in sql/05-08 and sql/99_tests.sql"))

    # ---------- 6 Methods, limits, AI ----------
    src = f"""<h2>Sources (all public, no login, no key)</h2><table class="small">
<tr><th>Source</th><th>Use</th><th>Collected</th></tr>
<tr><td>Shopify App Store: 4 listings (JSON-LD + page)</td><td>name, rating, launch, pricing, category, languages, description</td><td class='nw'>{col}</td></tr>
<tr><td>Shopify App Store: 514 public reviews</td><td>id, app, date, stars, country, tenure, reply date only</td><td class='nw'>{col}</td></tr>
<tr><td>Shopify App Store: 4 category shelves (2,568 apps)</td><td>position, rating, reviews, free plan</td><td class='nw'>{col}</td></tr>
<tr><td>Wayback Machine (CDX + snapshots)</td><td>review history of 2 category leaders (the archive refused further connections: not retried)</td><td class='nw'>{col}</td></tr>
<tr><td>Eurostat isoc_ec_eseln2 (2024)</td><td>share of enterprises (10+ staff) selling online to consumers</td><td class='nw'>{col}</td></tr>
<tr><td>ECB EUR/USD reference rates</td><td>convert simulated USD prices</td><td class='nw'>{col}</td></tr>
<tr><td>hero.software, legal notice; join.com job ad</td><td>company facts, job facts (no person named)</td><td class='nw'>{col}</td></tr></table>"""
    rules = """<h2>Collection rules</h2><ul class="small">
<li>robots.txt read first; apps.shopify.com disallows <code>*q=*</code>, so no search-result page and <b>no keyword ranking</b>.</li>
<li>At most 1 request every 1.5 s (2 s for the Wayback Machine), each page cached once; no retry loop, no workaround.</li>
<li>Neutral User-Agent, no contact details. No account, no app install, no test store, no form, no message.</li>
<li>Not collected: shop names, review texts, developer reply texts and signatures; countries under 5 reviews grouped.</li>
<li>German public holidays computed locally (the holiday API disallows automated clients).</li>
<li>Eurostat: free re-use with acknowledgement. ECB: re-use with source. Shopify pages: quoted as observed, no text republished.</li></ul>"""
    lim = """<h2>Limits</h2><ul class="small">
<li>A review is not an install; the review-per-install rate is unknown.</li>
<li>Category order observed once, logged out; it can be personalised and change daily.</li>
<li>Eurostat counts enterprises with 10+ staff, not Shopify merchants.</li>
<li>All installs, trials, revenue, spend and experiments are <b>SIMULATED</b> for fictional apps A-D; calibrated on public facts, never HeroSoftware's numbers.
The simulated country mix gives non-DACH markets more weight than the reviews, so that country tests have volume (docs/assumptions.md).</li>
<li>No LinkedIn company data, no Google Trends, no paid tools (BuiltWith, Sensor Tower, SimilarWeb).</li></ul>"""
    ai = f"""<h2>Methods & AI note</h2><p class="small">Python (pandas, SciPy), DuckDB SQL with assertions (sql/99_tests.sql), Excel with live formulas,
Plotly dashboard; one notebook re-runs everything. No LLM is called in the study.</p><blockquote>{AI_NOTE}</blockquote>"""
    body = f"""<div class="row c2">{card(src)}<div class="stack">{card(rules)}{card(img('img/p6_eurostat.png'), 'fc')}</div></div>
<div class="row c2 auto">{card(lim)}{card(ai)}</div>"""
    pages.append(page(6, "Methods, limits and AI note: public pages read politely, simulated data labelled everywhere, every number re-computable",
                      "How to re-run: python src/collect_public.py → simulate_growth.py → run_sql.py → build_excel.py → build_dashboard.py → build_pdf.py",
                      "MIXED · PUBLIC DATA + SIMULATED", body, "Sources listed above", coll))
    return pages


def main():
    charts.main()
    F = facts.build()
    REPORT.mkdir(exist_ok=True)
    html = REPORT / "_report.html"
    html.write_text(html_doc(TITLE, build(F)), encoding="utf-8")
    n = print_pdf(html, REPORT / "HeroSoftware_growth_case_study.pdf", TITLE)
    print(f"PDF: {n} pages -> report/HeroSoftware_growth_case_study.pdf")


if __name__ == "__main__":
    main()
