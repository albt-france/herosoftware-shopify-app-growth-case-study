# App Store listing audit (PUBLIC DATA)

The 4 HeroSoftware listings compared with the first 5 apps of their category, **as observed on the Shopify App Store
on 2026-11-23** (logged-out view, default category order). The order can be personalised and change daily: it is an
observation, not Shopify's ranking algorithm. Written as growth opportunities: all 4 apps are "Built for Shopify"
and rated 4.9 or more, which is the hardest part.

## What was looked at

| | AddressHero | PaymentHero | DiscountHero | Post Purchase Upsell Hero |
|---|---|---|---|---|
| Listing name | Address Validator AddressHero | Payment Rules Hide PaymentHero | Fraud Protection DiscountHero | Post Purchase Upsell Hero |
| Launched | 2023-04-04 | 2025-05-05 | 2025-07-25 | 2026-06-19 |
| Rating (reviews) | 4.9 (235) | 4.9 (213) | 5.0 (3) | 4.9 (63) |
| Pricing | Free to install, free trial | From $9.99/month, free trial | $99/month, free trial, Shopify Plus only | $19/month + usage, free trial |
| Free plan label | no ("Free to install") | no | no | no |
| Languages declared | English | English | English | English |
| Short description (JSON-LD) | German | German | empty | English |
| Integrations named ("Works with") | Checkout, Customer accounts, Shopify Admin, Klaviyo | Checkout, Shopify Admin | Checkout, Shopify Admin | Checkout, Shopify Flow, Shopify Admin, Judge.me, Klaviyo Reviews, Reviews.io |
| Screenshots | 5 | 4 | 5 | 6 |
| Developer replies to reviews | 100% | 0% | 0% | 98% |
| Last review | 2026-08-07 | 2026-02-24 | 2026-07-01 | 2026-11-11 |
| Category / shown at | Shipping: 7 of 914 | Checkout - Other: 30 of 402 | Fraud: 123 of 250 | Upsell and cross-sell: 66 of 1,002 |
| Rank by number of reviews in category | 25 | 7 | 70 | 151 |

Category leaders (positions 1-5) and their review counts:

- **Shipping:** packlink-pro (945), parcelpanel (3,233), globe (161), 17track (4,629), pirate-ship (189). 4 of 5 show a free plan or "Free to install".
- **Checkout - Other:** blockify-checkout-rules (324), smart-checkout-rules (872), shipfy-delivery-customization (161), checkout-blocks (224), kip-customize-payment-methods (120). All 5 show "Free" or "Free plan available".
- **Fraud:** blockify (1,890), easy-block-customer-ip-country (109), disputifier (140), mida-fraud-ip-blocker (586), chargeback-io (136).
- **Upsell and cross-sell:** smart-automatic-discounts (685), kaching-post-purchase-upsell (456), simple-bundles (849), essential-cart-drawer (1,252), cart-upsell (1,683). All 5 show "Free" or a free plan.

Across the 4 categories, apps shown in the top 30 have a free plan in 50-67% of cases vs 7-27% for positions 31+
(correlation only: popular apps may add free plans, not the other way round). No "Ad" card was detected in the
logged-out view. Two Wayback snapshots series (checkout leaders) show steady review growth: blockify-checkout-rules
28 -> 310 reviews (Nov 2024 -> Oct 2026), smart-checkout-rules 6 -> 611 (Oct 2024 -> Aug 2026).

Reviews: 85.0% Germany, 93.4% Germany + Austria + Switzerland; 59.9% of all reviews were posted in May-June 2025, with
days of 20 reviews, consistent with a review-request push; public data cannot tell how reviews were requested.
48.4% of reviews are written after a tenure counted in days.

## 10 concrete actions, by effort and impact

| # | Action | Effort | Impact | Why (public evidence) |
|---|---|---|---|---|
| 1 | Replace the German short descriptions of AddressHero and PaymentHero with English ones (the listing language) and fill DiscountHero's | XS | High | The description is the snippet many surfaces show; today it does not match the declared language |
| 2 | Reply to every PaymentHero review, then keep a 48 h reply rule on all apps | S | Medium | 0% replies on 213 reviews vs 100% on AddressHero; replies are visible trust signals |
| 3 | Translate the listings into German first, then French, Italian, Spanish (Shopify supports listing translations) | M | High | 93.4% of reviewers are German-speaking but the listings declare English only |
| 4 | Move the review prompt to the first value moment (first corrected address, first hidden payment method) | S | High | 48.4% of reviews come within days of install: the prompt moment drives volume |
| 5 | Restart a steady review flow on PaymentHero (no review since 2026-02-24) through the in-app prompt | S | High | Momentum moved to Upsell Hero (62 of 74 reviews since March 2026) |
| 6 | Test a free plan (or a clearly labelled free tier) on PaymentHero and AddressHero | M | Medium | All 5 checkout leaders show a free option; free-plan apps dominate the top 30 |
| 7 | Put the main keyword at the start of each listing name ("Hide payment methods", "Address validation") and in the subtitle | XS | Medium | Name and subtitle are the strongest on-page relevance signals in the App Store |
| 8 | Name more integrations where real (Flow, Klaviyo, Gorgias, ERP/WMS for AddressHero) | S | Low-Medium | Upsell Hero lists 6 integrations, PaymentHero and DiscountHero 2 |
| 9 | Make the "Shopify Plus only" requirement of DiscountHero part of the pitch (Plus merchants' fraud cost) and add use-case screenshots | S | Low | 3 reviews in 16 months; the audience is narrow, the message must be precise |
| 10 | Cross-link the four apps (in-app and on hero.software) with one-click install paths | S | Medium | The same merchants need address, payment and upsell tools; own base is the cheapest channel |

Limits: no keyword ranking (robots.txt disallows `*q=*` search pages), category order observed once, a review is not
an install.
