# Simulation assumptions (SIMULATED data)

`src/simulate_growth.py`, seed 42, daily data 2025-11-01 -> 2026-10-31. Fictional apps **APP_A** (address
validation), **APP_B** (payment rules), **APP_C** (discount-code fraud, Shopify Plus only), **APP_D** (post-purchase
upsell, launched 2026-06-19). Merchants `M00001...`, campaigns `CMP001...`, experiments `EXP01...EXP24`.
**None of these numbers are HeroSoftware's.** Every value below is an assumption.

## Calibrated on public facts
| Item | Public fact | Used as |
|---|---|---|
| Launch dates | listings | APP_A..APP_D launch dates |
| Prices | listings | APP_A pay per address (usage), APP_B $9.99/$19.99, APP_C $99, APP_D $19 + usage |
| Relative rhythm | review rhythm | APP_B weakens in DACH from March 2026 (to 50% by July); APP_D ramps from launch to ~22 installs/day |
| Review timing | 48.4% of reviews after days of use | review prompt at day 2 (before) vs value moment day 3-12 (after) |
| Calendar | German nation-wide holidays, BFCM 2025 (28 Nov / 1 Dec) | DE installs x0.6 on holidays; BFCM week 24 Nov-1 Dec x1.70 everywhere |
| FX | ECB monthly EUR/USD | USD prices converted to EUR |

## Assumptions (not calibrated)
| Item | Value |
|---|---|
| Base installs/day | APP_A 10.5 -> 8.5 (linear), APP_B 11, APP_C 0.45, APP_D 4 -> 22 |
| Country mix | APP_A DE 84%; APP_B DE 70%; APP_D DE 38% (more international). **Deliberately more non-DACH than the 85% DE of public reviews**, so that country tests have volume. Overall DE ~66% |
| Seasonality | monthly factors 0.95-1.15 (spring high); weekend x0.75, weekdays x1.07 |
| Source mix (organic) | App Store search 40%, category 22%, direct 14.5%, Google Ads 6.5% (75% brand), content 6%, partner 5%, social 4%, e-mail 2% |
| View -> install | search 12%, category 6%, direct 25%, partner 30%, App Store ads 5%, Google 2.5% (brand, many navigational clicks), content 3%, e-mail 15%, social 2% |
| Uninstall < 48 h | 12% organic, 41% App Store ads, 5% partners |
| Trial rate | 90% of installs kept 48 h |
| Trial -> paid | DACH 26.5-30.5%, non-DACH 8-12% by app; App Store ads x0.25; partners x1.6 |
| Paid churn | monthly 3-6% by app (geometric lifetime) |
| Review rate | 4.5% of active installs at day 2; x2.1 at the value moment; stars P(5)=93% unchanged |
| Spend | Google brand CPC EUR 0.55-0.60, non-brand EUR 1.35, App Store ads EUR 0.50 per view, content EUR 250 -> 600/month, partners EUR 300/month + EUR 50 per paying merchant, e-mail tool EUR 150/month, LinkedIn EUR 1,500, Meta EUR 2,400 |
| Data problems | ~1,100 duplicated webhooks on 14-15 July 2026; 3% quick re-installs |

## The 8 hidden events (to be recovered by the analysis)
1. FR+IT listing translation for APP_B from 2026-03-02: installs x1.35 (spring makes the naive read larger).
2. App Store ads for APP_A, 2026-04-06 -> 05-31: +30% installs, 41% uninstall < 48 h, trial -> paid 6% vs 24%.
3. Google brand: only 15% of brand installs incremental; the platform claims 410 conversions; 4-week geo holdout.
4. Review prompt moved to the value moment from 2026-02-01 (randomised until 04-30): review rate x2.1.
5. Webhook duplicates, quick re-installs, UTC/Berlin shift.
6. BFCM week +70% for everything; the LinkedIn push launched that week has no true effect.
7. Simpson: APP_D converts better than APP_B in each region but worse overall (more non-DACH trials).
8. Meta test, 3 weeks, EUR 2,400: true +8% on trials, MDE ~25%: inconclusive.

Arm-level results of the experiments not read from the main tables are drawn from binomial distributions with the
true lifts in `ARM_PARAMS` (seed 4242). The truth file is never published.
