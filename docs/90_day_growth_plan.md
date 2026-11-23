# 90-day growth plan

Five bets, ranked. Each comes with a budget, the test that will decide it, and the decision expected by day 90.
Evidence marked PUBLIC DATA comes from the Shopify App Store (observed 2026-11-23); SIMULATED evidence comes from the
fictional portfolio and shows the method, not HeroSoftware's figures.

| # | Bet | Evidence | Budget | Test | Decision expected |
|---|---|---|---|---|---|
| 1 | **Translated listings: German, French, Italian, then Spanish** | PUBLIC: 93.4% of reviews are German-speaking, listings declare English only. SIMULATED: FR+IT listing +38% installs vs controls (DiD), naive +50% | ~EUR 2,000 (translation, screenshots) | Geo DiD per language vs untranslated markets, 8 weeks, pre-trends checked | Scale to ES by day 60 if the CI is above +10%; Eurostat: ES 22.3% of enterprises sell online B2C, highest of the large markets |
| 2 | **Review request at the first value moment** | PUBLIC: 48.4% of reviews after days of use; PaymentHero without a review since 2026-02-24. SIMULATED: review rate x2.1, stars unchanged | Dev time only | Randomised 50/50 on new installs, 2 weekly cycles minimum, guardrail average stars | Roll out to all apps by day 45 |
| 3 | **Review reply policy on PaymentHero** (every review within 48 h, back-fill the 213) | PUBLIC: 0% replies vs 100% on AddressHero | 2 h per week | Before/after with sister-app control on install rate per view (directional) | Keep regardless (low cost, trust); report the effect honestly as small |
| 4 | **In-app cross-promotion towards Post Purchase Upsell Hero** | PUBLIC: Upsell Hero carries the review momentum (62 of 74 reviews since March 2026). SIMULATED: +182% APP_D installs from APP_B merchants | Dev time only | Randomised banner on 50% of paying merchants, guardrail uninstall rate | Scale by day 60 |
| 5 | **Comparison SEO pages** (one per app) + move brand-search money to intent keywords | PUBLIC: checkout leaders grow reviews steadily (Wayback). SIMULATED: comparison page +51% content installs; only ~11% of brand conversions incremental | EUR 600/month writing + reallocated brand budget | Matched-page comparison read at 4 months; brand geo holdout re-run | Pages live by day 30; first read at day 120, brand budget cut by day 30 |

## What we stop on day 1 (SIMULATED evidence)
- App Store ads (CAC ~4x the other paid channels, 41% uninstall in 48 h).
- Most of the Google brand budget (keep a defensive minimum).
- Win-back e-mails, YouTube tutorials, forum answers, Facebook groups (no effect at the volume we can reach).

## Rhythm
- Weekly: growth update (5 numbers, tests running, 1 decision, 1 risk).
- Every test: hypothesis, ICE, sample size before launch, no early read, one decision (playbook).
- Day 30 / 60 / 90: backlog re-scored, budget moved to what pays back in < 6 months.
