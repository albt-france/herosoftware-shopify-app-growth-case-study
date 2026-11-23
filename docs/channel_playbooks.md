# Channel playbooks

Half a page per channel: the first test to launch, the metric, the cost, and the stop rule. Costs and results quoted
from the simulation are **SIMULATED** (fictional apps A-D).

## Paid (Google Ads, App Store ads, Meta)
- **First test:** non-brand Google Ads on high-intent queries ("shopify address validation", "hide payment methods
  shopify"), one tight ad group per app, randomised ad-group split (Google experiments).
- **Metric:** CAC per paying merchant and payback; installs only as a leading indicator.
- **Cost:** EUR 1,000-1,500 per app per month to start.
- **Stop rule:** payback > 12 months after 8 weeks, or 48 h uninstall > 25%. Brand search: keep a defensive minimum
  and re-test incrementality with a geo holdout twice a year (SIMULATED holdout: ~11% of claimed brand conversions are
  incremental). App Store ads: off until listing conversion improves (SIMULATED CAC EUR 349, payback 31 months).

## SEO
- **First test:** one comparison page per app ("PaymentHero vs alternatives", honest table) and 6 how-to articles on
  the problems the apps solve, in German and English.
- **Metric:** content-sourced installs and trial -> paid, read at **4 months** (SEO is slow).
- **Cost:** ~EUR 600 per month of writing + review time.
- **Stop rule:** no page in the top 20 for its target query after 4 months -> rewrite once, then stop.

## Content
- **First test:** 3 short case studies with German merchants (problem, setup, result), reused on the listing,
  LinkedIn and in onboarding e-mails.
- **Metric:** listing views from content links, install rate per view.
- **Cost:** 2-3 days per case study.
- **Stop rule:** < 1% of installs from content after 3 months. Never judge content in Black Friday week (EXP02).

## E-mail (lifecycle)
- **First test:** onboarding sequence day 0/1/3 driving the first value moment; review request at that moment.
- **Metric:** trial -> paid, review rate; guardrail unsubscribe rate.
- **Cost:** tool ~EUR 150 per month + set-up time.
- **Stop rule:** no lift at the planned MDE after 2 weekly cycles and the planned sample. SIMULATED: onboarding +24%
  trial -> paid (scale), win-back neutral (kill).

## Social
- **First test:** founder/team posts on LinkedIn (DACH e-commerce managers), switchback weeks on/off.
- **Metric:** social-sourced listing views and installs.
- **Cost:** 2 hours per week.
- **Stop rule:** treat as brand activity if installs from social stay < 3% after 8 weeks; do not buy LinkedIn ads
  on the strength of a launch-week spike.

## App Store (listing optimisation)
- **First test:** translated listing (German first, then FR/IT/ES) and keyword-first listing names.
- **Metric:** installs per listing view by country, read with a geo difference-in-differences (no A/B in the App Store).
- **Cost:** translation + screenshots, ~2 days per language.
- **Stop rule:** DiD CI entirely below +10% after 8 weeks -> do not translate further languages. SIMULATED: FR+IT +38%
  installs (DiD), naive +50%.

## Partners (Shopify agencies)
- **First test:** partner kit (demo store, one-pager, EUR 50 bounty per paying merchant) for 5 DACH agencies.
- **Metric:** paying merchants per partner per month, trial -> paid vs organic.
- **Cost:** bounty + EUR 300 per month of partner time.
- **Stop rule:** a partner with no install in 3 months leaves the programme. SIMULATED: best quality channel
  (trial -> paid 42%), low volume: scale by adding agencies, not budget.
