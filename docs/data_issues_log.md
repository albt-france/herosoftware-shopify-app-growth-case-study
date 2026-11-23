# Data issues log

Every problem found in the data, how it was detected, how it is fixed, and the impact. Simulated issues are part of
the SIMULATED data on purpose; public-data issues are real.

| # | Data | Issue | Detected by | Fix | Impact |
|---|---|---|---|---|---|
| 1 | SIMULATED `install_events` | **Webhook retries on 2026-07-14/15**: 1,133 duplicated `installed` events (same merchant/app, seconds apart) | Daily raw vs clean installs spike x20 (`out_dq_daily`) | `01_staging.sql`: an event of the same merchant/app/type < 10 min after the previous one is a retry; dropped | Without the fix, July installs are overstated by ~1,100 and any July test reads as a success |
| 2 | SIMULATED `install_events` | **Re-installs within 24 h** counted as new installs (227) | `LAG()` over merchant x app: `installed` < 24 h after `uninstalled` | `01_staging.sql`: not a new install; the paired uninstall is not churn | Inflated installs and churn |
| 3 | SIMULATED `install_events` | **UTC vs Europe/Berlin**: installs near midnight move to another day/month | Month totals differ by date basis (`out_dq_month_shift`) | All reporting dates converted with `timezone('Europe/Berlin', ts AT TIME ZONE 'UTC')` | Small here (4 installs change month) but it breaks month-end reconciliations |
| 4 | SIMULATED `marketing_spend` | Platform-reported brand conversions (410) include merchants who would have installed anyway | Geo holdout (EXP05) | Use incremental conversions (~11%) for CAC decisions | Brand CAC understated ~9x |
| 5 | PUBLIC reviews | 9 reviews show only an "Edited <date>", not the original date | Parser: review date found after the reply, then flag | `date_is_edited` flag; kept in totals, excluded from the monthly rhythm | Without it, one 2025 review looked like an October 2026 review |
| 6 | PUBLIC reviews | The reply date is also a date in the review block | Last AddressHero review appeared as 2026-11-09 (a reply date) | Review date = first date before the "replied" line | Wrong "last review" dates |
| 7 | PUBLIC reviews | Tenure in minutes/hours ("2 minutes using the app") not parsed | 47 null `tenure_days` | Minutes and hours mapped to 0 days | Share of early reviews understated |
| 8 | PUBLIC listings | JSON-LD description is in German for 2 apps even with `?locale=fr`; empty for DiscountHero | Manual check of the field | Reported as an audit finding, not "fixed" | - |
| 9 | PUBLIC Wayback Machine | Connections refused after ~20 requests | HTTP connection errors | Not retried (collection rule); only 2 competitors' history kept | Limited history; stated in the limits |
| 10 | PUBLIC holidays | date.nager.at robots.txt disallows automated clients for the API | `robots.txt` check | Nation-wide German holidays computed locally (Easter algorithm) | None |
| 11 | PUBLIC Eurostat | JSON-stat values are indexed by a flat key computed from `id` and `size`; AT may be missing | Index check | Index computed from strides; AT present for 2024 | None |
