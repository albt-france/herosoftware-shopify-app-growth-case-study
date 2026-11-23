# Growth experiment playbook

How every growth test is planned, run, read and closed. Written **before** the tests; the read-outs in
`experiment_log.md` (SIMULATED) follow it. The Excel tracker (`excel/growth_experiment_tracker.xlsx`) implements
the sample-size and decision rules with live formulas.

## 1. Hypothesis template

> **We believe** <change> **for** <audience> **will** <effect> **measured by** <primary metric>, **without hurting** <guardrail>.

Example: *We believe asking for a review at the first value moment instead of day 2, for new merchants, will raise
the review rate, measured by reviews per active install, without hurting the average star rating.*

## 2. Prioritise with ICE

Impact, Confidence, Ease, each scored 1-10; **ICE = average of the three**. Re-score when new evidence arrives.
Scoring guide: Impact 8+ = could move monthly paying merchants by 5%+; Confidence 8+ = backed by data from our own
apps; Ease 8+ = live in under a week by one person.

## 3. Size the test before launch (sample size and MDE)

- Write down the **baseline rate**, the **minimum detectable effect (MDE)** worth acting on, alpha 5% (two-sided),
  power 80%.
- Units per arm: `n = (z_a/2 + z_b)^2 (p1 q1 + p2 q2) / (p2 - p1)^2` (sheet `Sample_Size`).
- If the traffic cannot reach `n` in 8 weeks, **do not run it as an A/B test**: use a bigger lever, a geo test, or
  accept that the read will be directional.

| Baseline | MDE (relative) | Units per arm |
|---|---|---|
| 0.37% trial per reached store (Meta) | 25% | 76,046 |
| 0.37% trial per reached store (Meta) | 8% | 686,772 |
| 24% trial -> paid | 15% | 2,315 |
| 8% install per listing view | 20% | 4,918 |
| 4.5% review rate | 50% | 1,643 |

## 4. Run it

- **Minimum duration: 2 full weekly cycles**, even when `n` is reached earlier (weekday/weekend mix).
- Avoid launch weeks that overlap Black Friday / Cyber Monday, Christmas or a German public holiday, or use a
  control that goes through the same days.
- **No early read.** Results are looked at once, at the planned end date. If a test must be monitored (risk), use
  pre-set stopping bounds, not "stop at the first p < 0.05".
- Guardrails checked weekly: **uninstall within 48 h**, **support tickets per 100 installs**, **average star rating**.
  A guardrail break stops the test whatever the primary metric says.

## 5. When the App Store does not allow an A/B test

The Shopify App Store has no split testing for listings. Use, in this order:
1. **Geo difference-in-differences**: change the listing for one language/market, compare with similar markets that
   did not change (EXP03: FR+IT vs ES+NL+PL). Check that pre-trends are parallel.
2. **Sister-app control**: change one app's listing, use a sister app in the same weeks as control (EXP18, EXP23).
3. **Switchback**: alternate weeks on/off for things that can be switched (founder posts, EXP15).
4. **Holdouts for paid media**: pause a channel in a random half of the geo cells (EXP05) to measure incrementality.

## 6. Read it

- Report the **relative lift with its 95% CI**, the p-value, and the MDE the test could actually see.
- Compare with the right counterfactual (control group, control markets, unexposed apps), never a before/after alone.
- Segment only on segments written down before launch; beware Simpson's paradox when the mix differs between groups.

## 7. Decide: Scale / Kill / Rerun / Inconclusive

| Decision | Rule | Example (SIMULATED) |
|---|---|---|
| **Scale** | CI lower bound > 0 and guardrails OK | EXP01 review prompt, EXP03 translation |
| **Kill** | CI upper bound < 0, or CI upper bound < the minimum worthwhile lift (10%), or a guardrail/CAC breaks | EXP04 App Store ads, EXP19 7-day trial |
| **Rerun** | the design was confounded (season, overlap) or a guardrail needs a longer window | EXP02 LinkedIn in BFCM week, EXP10 free plan |
| **Inconclusive** | CI includes 0 **and** the effect worth having: the test was too small | EXP06 Meta, EXP18 review replies |

Inconclusive is **not** a failure: write the sample needed to decide, and choose whether it is worth buying.
"Kill" can also be a business call when a test is under-powered and the channel can never reach the volume needed
(EXP08, EXP16, EXP21, EXP24): say so explicitly in the log.

## 8. Close it

One line in `experiment_log.md`: decision + "what we learned". Update the backlog ICE scores. Share it in the weekly
update (`weekly_growth_update.md`).

---

## Commented corrections: three decisions to make yourself first (SIMULATED)

*Try to decide Scale / Kill / Rerun / Inconclusive before reading the answer.*

**A. App Store ads for APP_A (EXP04).** Installs rose by 170 in 8 weeks. Tempting: "Scale, it brings installs".
**Answer: Kill.** 41% of ad installs uninstall within 48 h (12% organic) and trial -> paid is 5.4% vs 25.1%.
CAC per paying merchant is EUR 349, about 4x the EUR 86 of the other paid channels together; payback 31 months.
The metric that matters is paying merchants per euro, not installs.

**B. LinkedIn content push in Black Friday week (EXP02).** APP_A installs +44% per day in launch week.
Tempting: "Scale, it worked". **Answer: Rerun off-season, do not scale.** The apps that were not promoted rose +68%
in the same days: the jump is Black Friday. Difference-in-differences: -14% (95% CI -38% to +19%), no evidence of
an effect. The design was confounded, so the right call is a clean re-test, not a kill of LinkedIn forever.

**C. Meta prospecting ads, 3 weeks, EUR 2,400 (EXP06).** Trials +6% vs holdout, p = 0.52. Tempting: "Kill, it
failed". **Answer: Inconclusive.** With 72,000 reached stores per arm the test could only detect a 24% lift (MDE);
a +8% effect, if real, was invisible by design. Seeing +8% needs ~690,000 stores per arm (about 29 weeks, roughly
EUR 23,000 at the same cost per reach). Decision: do not buy that test now; better levers (translation, reviews,
partners) come first.
