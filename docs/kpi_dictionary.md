# KPI dictionary

Exact definitions used in the SQL (`sql/`), the Excel tracker and the dashboard. Dates are reported in
**Europe/Berlin**; raw timestamps are stored in UTC.

| KPI | Definition | Source / SQL |
|---|---|---|
| Listing view | One view of an app's Shopify App Store listing, by surface (search, category, direct, partner, ads, Google, content, e-mail, social) | `listing_traffic` |
| Raw install event | One `installed` webhook received | `install_events` |
| **Net install** | First `installed` event per merchant x app, after removing webhook retries (same merchant/app/event < 10 min apart) and re-installs < 24 h after an uninstall | `01_staging.sql` -> `stg_installs` |
| Uninstall < 48 h | Net install whose final uninstall happens within 48 h | `stg_installs.uninstalled_48h` |
| **Trial** | Subscription with a `trial_start` (14-day free trial) | `subscriptions` |
| **Paying merchant** | Subscription with a `paid_start` (trial converted) | `subscriptions` |
| Trial -> paid | Paying merchants / trials, trials fully observed (started >= 14 days before period end) | `08_simpson.sql`, `03` |
| Paying at day 60 | Paying merchant whose subscription is not cancelled 60 days after install | `02`, `03` |
| **MRR (EUR)** | (plan price + usage charges, USD) / ECB monthly USD per EUR of the paid-start month | `03_channel_scorecard.sql` |
| MRR per paying at day 60 | Sum of MRR of merchants paying at day 60 / their number | `03` |
| Cost per install | Channel spend / net installs of the channel | `03` |
| **CAC** | Channel spend / paying merchants acquired by the channel (same cohort months) | `03` |
| **Payback (months)** | CAC / MRR per paying merchant at day 60 | `03` |
| Retention month k | Share of an install cohort still installed 30 x (k+1) days after install | `04_cohort_retention.sql` |
| **Review rate** | Reviews / installs still active at the prompt day | `05_experiment_readout.sql` (EXP01) |
| Incremental share | 1 - (conversion rate with ads off / with ads on) in a geo holdout | `06_attribution_vs_holdout.sql` |
| Lift | Treated rate / control rate - 1; DiD lift = (T_post/T_pre)/(C_post/C_pre) - 1 | `05`, `07`, `run_sql.py` |
| MDE | Smallest relative lift a test detects with 80% power at alpha 5% (two-sided) | Excel `Sample_Size` |
| ICE | Average of Impact, Confidence, Ease (1-10 each) | Excel `Backlog` |

Public-data indicators (PUBLIC DATA, as observed on the Shopify App Store on 2026-11-23):

| Indicator | Definition |
|---|---|
| Public reviews | Reviews listed on the app's review pages; an indirect signal, **not** a number of installs |
| Reply rate | Share of reviews with a developer reply date |
| Shown position | Position of the app card in the category's default order, logged-out view, one observation |
| Rank by reviews | Rank of the app by "total reviews" within the category |
