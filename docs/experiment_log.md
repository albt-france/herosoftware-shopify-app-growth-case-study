# Experiment log (SIMULATED)

24 experiments run on the fictional portfolio APP_A-APP_D. **SIMULATED data, not HeroSoftware's figures.**
Lift = relative change of the primary metric, 95% CI. `rule_call` = statistical call from the playbook rule; `decision` = the decision taken (a different one is explained in `note`). Full table: `experiment_log.csv`.

Decisions: {'Scale': 9, 'Kill': 9, 'Rerun': 3, 'Inconclusive': 3}

## EXP01 - Review request at first value moment (Email, APP_A,APP_B)

- **Hypothesis:** We believe asking for a review at the first value moment instead of day 2, for new merchants, will raise the review rate, measured by reviews per active install.
- **ICE:** 8/7/8 -> 7.67 | **Design:** Randomised 50/50 on new installs | **Dates:** 2026-02-01 -> 2026-04-30
- **Primary metric:** review rate | **Guardrail:** average stars
- **Result:** lift +111% (95% CI +33% to +189%), MDE at 80% power 62% | rule: Scale | **Decision: Scale**
- **What we learned:** Timing beats wording: the same ask at the value moment doubles reviews without moving stars.

## EXP02 - LinkedIn content push in BFCM week (Social, APP_A)

- **Hypothesis:** We believe a LinkedIn content series promoting APP_A, for DACH merchants, will raise APP_A installs, measured by installs vs the apps not promoted.
- **ICE:** 5/4/6 -> 5.00 | **Design:** Before/after + difference-in-differences vs apps not promoted (APP_B+APP_C) | **Dates:** 2025-11-24 -> 2025-12-14
- **Primary metric:** installs | **Guardrail:** cost per install
- **Result:** lift -14% (95% CI -38% to +19%) | rule: Inconclusive | **Decision: Rerun** - Confounded by Black Friday: re-test off-season.
- **What we learned:** The jump was Black Friday, not LinkedIn: the apps not promoted rose as much (DiD ~0). Re-test off-season.

## EXP03 - Listing translated into French and Italian (App Store, APP_B)

- **Hypothesis:** We believe a French and Italian listing, for FR/IT merchants, will raise installs, measured by installs vs ES/NL/PL controls.
- **ICE:** 8/6/7 -> 7.00 | **Design:** Geo difference-in-differences (FR+IT vs ES+NL+PL) | **Dates:** 2026-03-02 -> 2026-06-30
- **Primary metric:** installs | **Guardrail:** 48h uninstall rate
- **Result:** lift +38% (95% CI -4% to +98%) | rule: Inconclusive | **Decision: Scale**
- **What we learned:** Localisation works; the naive before/after overstates it (spring). Next: Spanish.

## EXP04 - Shopify App Store ads (Paid, APP_A)

- **Hypothesis:** We believe App Store search ads, for merchants searching address validation, will raise paying merchants, measured by CAC per paying merchant.
- **ICE:** 6/5/8 -> 6.33 | **Design:** Flighting + quality cohort vs organic | **Dates:** 2026-04-06 -> 2026-05-31
- **Primary metric:** paying merchants | **Guardrail:** 48h uninstall rate
- **Result:** lift -85% (95% CI -98% to -71%) | rule: Kill | **Decision: Kill** - Installs up, but paying per install far lower and CAC 4x: kill on cost, not on installs.
- **What we learned:** Installs went up, paying merchants barely: 41% uninstall in 48h, 6% trial->paid. CAC 4x.

## EXP05 - Google Ads brand: 4-week geo holdout (Paid, All)

- **Hypothesis:** We believe most brand-ad conversions would happen anyway, for merchants searching our name, measured by brand-intent traffic in a paused geo.
- **ICE:** 7/6/9 -> 7.33 | **Design:** Geo holdout: brand ads off in half of the geo cells | **Dates:** 2026-08-03 -> 2026-08-30
- **Primary metric:** installs per brand search | **Guardrail:** total installs
- **Result:** lift -11% (95% CI -20% to -3%), MDE at 80% power 13% | rule: Kill | **Decision: Kill** - Ads off lose only ~15% of brand installs: cut brand spend to a defensive minimum.
- **What we learned:** Only ~15% of the 410 claimed conversions are incremental: keep a defensive minimum, move budget.

## EXP06 - Meta prospecting ads (3 weeks) (Paid, APP_D)

- **Hypothesis:** We believe Meta prospecting ads, for lookalike Shopify merchants, will raise trials, measured by trials per reached store vs holdout.
- **ICE:** 6/4/6 -> 5.33 | **Design:** Audience holdout 50/50 | **Dates:** 2026-09-14 -> 2026-10-04
- **Primary metric:** trials | **Guardrail:** cost per trial
- **Result:** lift +6% (95% CI -12% to +23%), MDE at 80% power 24% | rule: Inconclusive | **Decision: Inconclusive** - Under-powered: the MDE is far above the effect seen.
- **What we learned:** +8% but the test could only see 25%: not a failure, not a win. A real read needs ~10x the sample.

## EXP07 - In-app cross-promotion to APP_D (Product, APP_B->APP_D)

- **Hypothesis:** We believe an in-app banner, for paying APP_B merchants, will raise APP_D installs, measured by APP_D installs per merchant.
- **ICE:** 7/7/8 -> 7.33 | **Design:** Randomised 50/50 on APP_B merchants | **Dates:** 2026-07-15 -> 2026-08-25
- **Primary metric:** APP_D install rate | **Guardrail:** APP_B uninstall rate
- **Result:** lift +182% (95% CI +47% to +317%), MDE at 80% power 84% | rule: Scale | **Decision: Scale**
- **What we learned:** Own base is the cheapest channel: more than doubles APP_D installs with no APP_B churn.

## EXP08 - Win-back e-mail after uninstall (Email, All)

- **Hypothesis:** We believe a win-back e-mail 21 days after uninstall, for churned merchants, will raise re-installs, measured by re-install rate.
- **ICE:** 4/5/8 -> 5.67 | **Design:** Randomised 50/50 on uninstalled merchants | **Dates:** 2026-01-10 -> 2026-04-30
- **Primary metric:** re-install rate | **Guardrail:** unsubscribe rate
- **Result:** lift -5% (95% CI -28% to +18%), MDE at 80% power 34% | rule: Inconclusive | **Decision: Kill** - Under-powered, and the uninstalled base is too small to ever power it: stop.
- **What we learned:** No effect at an MDE we cared about: stop, keep the slot for onboarding.

## EXP09 - SEO articles: Shopify address validation (SEO, APP_A)

- **Hypothesis:** We believe 6 how-to articles, for merchants searching address problems, will raise installs from content, measured by content installs vs matched pages.
- **ICE:** 7/5/5 -> 5.67 | **Design:** Matched-page comparison over 4 months | **Dates:** 2026-02-01 -> 2026-06-01
- **Primary metric:** content-sourced installs | **Guardrail:** bounce rate
- **Result:** lift +29% (95% CI +8% to +51%), MDE at 80% power 25% | rule: Scale | **Decision: Scale**
- **What we learned:** Slow but compounding: positive at 4 months. Judge SEO on a 4-month window, not 4 weeks.

## EXP10 - Free plan on the pricing page (Pricing, APP_B)

- **Hypothesis:** We believe a free plan, for small merchants, will raise installs, measured by installs per listing view, with MRR at 60 days as guardrail.
- **ICE:** 7/5/6 -> 6.00 | **Design:** Randomised pricing-page variant | **Dates:** 2026-05-04 -> 2026-07-05
- **Primary metric:** install rate | **Guardrail:** MRR per install at 60 days
- **Result:** lift +34% (95% CI +22% to +47%), MDE at 80% power 14% | rule: Scale | **Decision: Rerun** - Installs up, MRR at 60 days flat (guardrail): extend to 120 days.
- **What we learned:** More installs, flat MRR at 60 days: extend to 120 days before deciding.

## EXP11 - Shopify agency partner programme (Partners, APP_A,APP_B)

- **Hypothesis:** We believe agencies, for their merchant clients, will bring high-quality installs, measured by trial->paid vs organic.
- **ICE:** 6/6/5 -> 5.67 | **Design:** Cohort comparison vs organic | **Dates:** 2026-01-15 -> 2026-10-31
- **Primary metric:** trial->paid | **Guardrail:** volume
- **Result:** lift +44% (95% CI +8% to +81%), MDE at 80% power 40% | rule: Scale | **Decision: Scale** - Cohort comparison, not randomised: scale slowly.
- **What we learned:** Low volume, best quality: scale slowly by adding agencies, not budget.

## EXP12 - Onboarding e-mail sequence (day 0/1/3) (Email, All)

- **Hypothesis:** We believe a 3-step onboarding sequence, for new trials, will raise trial->paid, measured by paid conversion at day 14.
- **ICE:** 7/7/8 -> 7.33 | **Design:** Randomised 50/50 on new trials | **Dates:** 2025-12-01 -> 2026-02-15
- **Primary metric:** trial->paid | **Guardrail:** unsubscribe rate
- **Result:** lift +24% (95% CI +7% to +40%), MDE at 80% power 20% | rule: Scale | **Decision: Scale**
- **What we learned:** Activation e-mails pay back fast; keep and iterate on content.

## EXP13 - Screenshots with German captions (App Store, APP_A)

- **Hypothesis:** We believe German captions, for DACH visitors, will raise listing conversion, measured by installs per listing view.
- **ICE:** 5/4/8 -> 5.67 | **Design:** Before/after with EN listing views as control | **Dates:** 2026-05-11 -> 2026-06-07
- **Primary metric:** install rate | **Guardrail:** -
- **Result:** lift -1% (95% CI -10% to +9%), MDE at 80% power 14% | rule: Kill | **Decision: Kill** - Upper bound below the +10% worth acting on.
- **What we learned:** No effect worth having: even the upper bound is below +10%. Stop polishing screenshots.

## EXP14 - Google non-brand: 'shopify address validation' ad group (Paid, APP_A)

- **Hypothesis:** We believe a tight non-brand ad group, for merchants with address problems, will raise installs per click, measured by install rate per click.
- **ICE:** 6/6/7 -> 6.33 | **Design:** Randomised ad-group split (Google experiments) | **Dates:** 2026-03-09 -> 2026-04-19
- **Primary metric:** install rate per click | **Guardrail:** CPC
- **Result:** lift +42% (95% CI +8% to +76%), MDE at 80% power 38% | rule: Scale | **Decision: Scale**
- **What we learned:** Intent keywords convert; move brand money here.

## EXP15 - Founder posts on LinkedIn (Social, All)

- **Hypothesis:** We believe weekly founder posts, for DACH e-commerce managers, will raise listing visits, measured by social-sourced listing views.
- **ICE:** 4/3/7 -> 4.67 | **Design:** Alternating weeks on/off | **Dates:** 2026-04-06 -> 2026-05-31
- **Primary metric:** social listing views | **Guardrail:** -
- **Result:** lift -21% (95% CI -58% to +16%), MDE at 80% power 64% | rule: Inconclusive | **Decision: Inconclusive** - Under-powered.
- **What we learned:** Signal too weak for the sample; keep as brand activity, not a growth channel.

## EXP16 - YouTube tutorial videos (Content, APP_A)

- **Hypothesis:** We believe tutorials, for merchants evaluating apps, will raise installs, measured by video-sourced installs.
- **ICE:** 4/4/3 -> 3.67 | **Design:** Before/after with matched control apps | **Dates:** 2026-03-01 -> 2026-05-31
- **Primary metric:** installs from video | **Guardrail:** production cost
- **Result:** lift +10% (95% CI -37% to +57%), MDE at 80% power 62% | rule: Inconclusive | **Decision: Kill** - Under-powered and expensive to produce: stop.
- **What we learned:** Costly to produce, no measurable effect: stop.

## EXP17 - Comparison page vs category leaders (SEO, APP_B)

- **Hypothesis:** We believe an honest comparison page, for merchants comparing payment-rule apps, will raise installs, measured by content installs.
- **ICE:** 7/6/6 -> 6.33 | **Design:** Matched-page comparison | **Dates:** 2026-04-01 -> 2026-07-31
- **Primary metric:** content-sourced installs | **Guardrail:** -
- **Result:** lift +51% (95% CI +18% to +84%), MDE at 80% power 34% | rule: Scale | **Decision: Scale**
- **What we learned:** Comparison intent converts well; add one per app.

## EXP18 - Reply to every review within 48 h (App Store, APP_A)

- **Hypothesis:** We believe fast public replies, for listing visitors, will raise listing conversion, measured by installs per view.
- **ICE:** 6/4/9 -> 6.33 | **Design:** Before/after with sister-app control | **Dates:** 2026-06-01 -> 2026-07-31
- **Primary metric:** install rate | **Guardrail:** -
- **Result:** lift +5% (95% CI -4% to +14%), MDE at 80% power 13% | rule: Inconclusive | **Decision: Inconclusive** - Under-powered.
- **What we learned:** Cheap and right for trust, but the effect is too small to measure in 2 months.

## EXP19 - Trial shortened from 14 to 7 days (Pricing, APP_D)

- **Hypothesis:** We believe a 7-day trial, for new merchants, will raise trial->paid speed, measured by paid conversion.
- **ICE:** 5/5/9 -> 6.33 | **Design:** Randomised 50/50 | **Dates:** 2026-08-01 -> 2026-09-15
- **Primary metric:** trial->paid | **Guardrail:** uninstall rate
- **Result:** lift -34% (95% CI -44% to -24%), MDE at 80% power 19% | rule: Kill | **Decision: Kill**
- **What we learned:** Fewer merchants reach value in 7 days: conversion drops. Keep 14.

## EXP20 - Usage-based pricing copy (Pricing, APP_D)

- **Hypothesis:** We believe clearer usage-pricing copy, for listing visitors, will raise install rate, measured by installs per view.
- **ICE:** 5/4/9 -> 6.00 | **Design:** Randomised pricing-page variant | **Dates:** 2026-09-01 -> 2026-10-15
- **Primary metric:** install rate | **Guardrail:** -
- **Result:** lift +7% (95% CI -7% to +22%), MDE at 80% power 20% | rule: Inconclusive | **Decision: Rerun** - Positive but not significant; cheap to rerun with 2x traffic.
- **What we learned:** Positive but not significant; rerun with 2x traffic.

## EXP21 - Answers in the Shopify Community forum (Content, All)

- **Hypothesis:** We believe helpful answers, for merchants asking checkout questions, will raise installs, measured by referral installs.
- **ICE:** 3/3/6 -> 4.00 | **Design:** Before/after | **Dates:** 2026-01-12 -> 2026-03-08
- **Primary metric:** referral installs | **Guardrail:** time spent
- **Result:** lift +10% (95% CI -32% to +53%), MDE at 80% power 57% | rule: Inconclusive | **Decision: Kill** - Under-powered, tiny volume: stop.
- **What we learned:** Too little volume for the time it takes.

## EXP22 - Newsletter cross-promo to Plus merchants (Email, APP_C)

- **Hypothesis:** We believe a newsletter feature, for Plus merchants of APP_A, will raise APP_C trials, measured by trial rate.
- **ICE:** 4/4/8 -> 5.33 | **Design:** Randomised 50/50 | **Dates:** 2026-02-02 -> 2026-03-01
- **Primary metric:** APP_C trial rate | **Guardrail:** unsubscribe rate
- **Result:** lift +26% (95% CI -49% to +102%), MDE at 80% power 91% | rule: Inconclusive | **Decision: Kill** - Too few Plus merchants to matter, whatever the lift.
- **What we learned:** Plus merchants in the base are few and not interested now: stop.

## EXP23 - Listing title with the main keyword (App Store, APP_B)

- **Hypothesis:** We believe the keyword 'hide payment methods' in the title, for App Store searchers, will raise installs, measured by installs per view.
- **ICE:** 7/6/9 -> 7.33 | **Design:** Before/after with sister-app control | **Dates:** 2026-06-08 -> 2026-07-19
- **Primary metric:** install rate | **Guardrail:** -
- **Result:** lift +24% (95% CI +13% to +35%), MDE at 80% power 13% | rule: Scale | **Decision: Scale**
- **What we learned:** The listing title is the cheapest lever we have.

## EXP24 - Posts in Facebook merchant groups (Social, All)

- **Hypothesis:** We believe posts in merchant groups, for small DACH stores, will raise installs, measured by social installs.
- **ICE:** 3/3/7 -> 4.33 | **Design:** Before/after | **Dates:** 2026-05-04 -> 2026-05-31
- **Primary metric:** social installs | **Guardrail:** -
- **Result:** lift +5% (95% CI -33% to +44%), MDE at 80% power 53% | rule: Inconclusive | **Decision: Kill** - Under-powered, tiny volume, brand risk: stop.
- **What we learned:** No effect, risk of looking spammy: stop.
