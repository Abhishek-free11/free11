# FREE11 — Product Requirements Document
<!-- Last updated: March 2026 — Production Security Audit completed. Critical vulnerabilities patched. DB indexes added. -->

## What is FREE11?

FREE11 is a free skill-based gaming and rewards platform. Users play cricket predictions, card games, daily quests, and puzzles — earn FREE Coins — then redeem them for real groceries, vouchers, and digital rewards.

**Tagline:** "Play Games. Earn Real Rewards."

**Monetization:**
- AdMob engagement revenue (banner + rewarded ads, 20 coins/watch, 5/day)
- Sponsored brand pools (20% platform cut)
- FREE Bucks in-app purchases (₹49 / ₹149 / ₹499 / ₹999)
- Commerce commission (8–12% on redemptions)
- Loyalty breakage economics (>10% coins never redeemed)

---

## Legal & Regulatory Compliance
- Compliant with **Promotion and Regulation of Online Gaming Act, 2025**: Pure skill-based entertainment; zero monetary deposits, stakes, wagering, or cash-outs.
- Does not qualify as an "online money game" — all rewards are promotional benefits earned through engagement, not convertible to cash.
- `SkillDisclaimerModal` displayed on: Shop, Sponsored Pools, Quest modal, Predict, LiveMatch, Landing footer.
- **Exact disclaimer text:** "FREE11 is a skill-based sports prediction platform. No deposits or cash wagering. Rewards are promotional benefits only."
- **Fraud Engine** active: device hash detection, duplicate account flagging, ban/unban system.
- **Geo-fence middleware**: India-only restriction enforced at API level.
- **Rate limiter**: API rate limiting active (in-memory fallback when Redis unavailable).
- All redemptions are promotional only; no encashable value.
- FREE Coins: non-withdrawable, no monetary value, 180-day rolling expiry.
- FREE Bucks: purchasable, non-withdrawable, no monetary value.

---

## Core Requirements
- **Zero Cash Risk**: No deposits, no cash outs. Earn via skill, redeem for products.
- **Online Gaming Act, 2025 Compliant**: Skill-based only, no gambling mechanics.
- **Mobile-First PWA**: Works offline, installable on Android/iOS.
- **Free-to-Play**: Users earn real rewards through engagement; FREE Bucks optional.

---

## Tech Stack
- **Frontend**: React 18, Tailwind CSS, Framer Motion, PWA (service worker + manifest), i18n 8 languages (en, hi, ta, bn, te, kn, mr, ml)
- **Backend**: FastAPI (Python), Motor (async MongoDB), APScheduler, Redis
- **Database**: MongoDB
- **AI**: Google Gemini Flash via `emergentintegrations` (Emergent LLM Key)
- **Payments**: Razorpay (TEST MODE → live keys needed) + Cashfree (pending compliance approval)
- **Notifications**: Firebase FCM (live), Resend email (live, DNS pending)
- **Analytics**: Sentry (live)
- **Ads**: AdMob (live)
- **Auth**: JWT + Google OAuth2 (Emergent-managed) + Firebase Phone Auth
- **Cricket Data**: EntitySport (live)
- **Gift Cards**: Reloadly (USD live, INR blocked), Xoxoday (mocked)
- **Commerce**: ONDC/Zepto/BigBasket/Amazon/Flipkart (all mocked/providers ready)

---

## Design System
- **Primary**: Metallic Gold #C6A052, Highlight Gold #E0B84F
- **Base**: Deep Charcoal #0F1115, Graphite Dark #1B1E23
- **Neutrals**: Steel Silver #BFC3C8, Soft Grey #8A9096
- **Fonts**: Bebas Neue (headings), Oswald (numbers), Noto Sans (body)
- **Navigation**: Mobile-first bottom nav (Home/Play/Games/Earn/Profile)

---

## FREE Bucks Packages (In-App Purchase via Razorpay)

| Package ID | Label | Price | FREE Bucks | Bonus |
|---|---|---|---|---|
| starter | Starter Pack | ₹49 | 50 | 0 |
| popular | Popular Pack | ₹149 | 160 | +10 |
| value | Value Pack | ₹499 | 550 | +50 |
| mega | Mega Pack | ₹999 | 1,200 | +200 |

- Payment via **Razorpay** (TEST MODE — live keys needed)
- **Cashfree** as fallback (pending compliance approval)
- Neither FREE Bucks nor FREE Coins can be withdrawn as cash

---

## Key DB Schema

### Existing Collections
| Collection | Key Fields |
|---|---|
| users | coins_balance, free_bucks, xp, level, streak_days, last_checkin, prediction_streak, wishlist_product_id, coin_expiry_date (180d rolling) |
| matches | EntitySport data + prediction state |
| predictions | user_id, match_id, choice, result, coins_awarded |
| contests | type, entry_fee (0=free), prize_pool, participants |
| products | name, coin_price, category, daily_cap, image_url |
| redemptions | user_id, product_id, status, voucher_code, partner_label |
| coin_transactions | user_id, amount, type (earn/spend), source, created_at |
| ledger | Unified transaction ledger (merged with coin_transactions) |
| daily_puzzles | AI-generated via Gemini Flash |
| weekly_reports | User performance summaries |
| quest_sessions | id, user_id, date, status, ad_claimed, ration_viewed, coins_earned |
| router_orders | id, user_id, provider_id, sku, coins_used, status, partner_label |
| sponsored_pools | id, brand_name, title, sku_tie, prize_pool, platform_cut, participants |
| sponsored_entries | pool_id, user_id, points, joined_at |
| freebucks_purchases | user_id, package_id, amount, bucks, payment_status, razorpay_order_id |
| clans | name, members, total_coins, rank |
| missions | user_id, type, progress, claimed |
| spin_wheel | user_id, last_spin, history |

### DB Indexes (Added March 2026)
| Collection | Index | Purpose |
|---|---|---|
| users | email (unique, sparse) | Prevent duplicate emails, fast login lookup |
| users | id (unique) | Fast user lookup by internal ID |
| coin_transactions | user_id | Fast transaction history |
| coin_transactions | (user_id, timestamp DESC) | Paginated transaction history |
| predictions | user_id | Fast user prediction lookup |
| predictions | (user_id, match_id) | Per-match prediction lookup |
| redemptions | user_id | Fast redemption history |
| redemptions | (user_id, order_date DESC) | Paginated order history |
| missions | (user_id, type) | Mission status lookup |
| router_orders | user_id | Router order lookup |

---

## Key API Endpoints

### Auth
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/send-otp
- POST /api/auth/verify-otp
- POST /api/auth/google-oauth
- POST /api/auth/phone-verify *(Firebase phone auth)*
- GET /api/auth/me

### Cricket & Predictions
- GET /api/v2/matches/live
- POST /api/v2/predictions
- GET /api/v2/contests/join
- GET /api/v2/crowd-meter

### Games
- POST /api/v2/earn/rummy-win (+50 coins/day)
- POST /api/v2/earn/teen-patti-win (+40 coins/day)
- POST /api/v2/earn/poker-win (+60 coins/day)
- POST /api/v2/earn/solitaire-win (+25 coins/day)
- GET /api/v2/games/card-leaderboard
- GET /api/v2/games/card-streak

### Economy
- GET /api/coins/balance
- GET /api/coins/transactions
- POST /api/coins/checkin *(atomic race-condition safe)*
- POST /api/games/spin
- POST /api/games/scratch
- POST /api/games/quiz
- GET /api/tasks, POST /api/tasks/complete

### Payments
- GET /api/razorpay/status
- POST /api/razorpay/create-order
- POST /api/razorpay/verify
- GET /api/v2/freebucks/packages
- POST /api/cashfree/create-order

### Shop & Rewards
- GET /api/products
- POST /api/products *(admin only — fixed March 2026)*
- POST /api/redemptions *(atomic stock+coin deduction)*
- GET /api/redemptions

### Quest & Router
- GET /api/v2/quest/status
- POST /api/v2/quest/offer, /claim-ad, /ration-viewed, /dismiss
- GET /api/v2/router/tease, POST /api/v2/router/settle *(atomic coin deduction)*, GET /api/v2/router/skus

### KPIs & Admin *(all require admin auth — fixed March 2026)*
- GET /api/admin/analytics *(admin only)*
- GET /api/admin/beta-metrics *(admin only)*
- GET /api/admin/brand-roas *(admin only)*
- GET /api/v2/kpis *(admin only)*
- GET /api/v2/kpis/cohort-csv

---

## External Integrations Status

| Integration | Status | Notes |
|---|---|---|
| EntitySport | LIVE | Cricket data, match scores |
| Redis | LIVE | Crowd Meter + Router caching. Rate limiter has in-memory fallback |
| Sentry | LIVE | Error monitoring |
| Gemini Flash | LIVE | AI puzzle (Emergent LLM Key) |
| Google Auth | LIVE | Emergent-managed OAuth2 |
| Firebase FCM | LIVE | send_each (fixed from send_all) |
| Firebase Phone Auth | LIVE | Added Feb 2026 |
| Resend Email | LIVE | API key active; DNS verification pending |
| AdMob | LIVE | User's own API keys |
| Razorpay | TEST MODE | Test keys only; live keys needed for production |
| Cashfree | PENDING | Awaiting compliance approval from Cashfree team |
| Reloadly (USD) | LIVE | Swype/Razer gift cards working |
| Reloadly (INR) | BLOCKED | Product IDs 18678, 18677, 15714 need enabling by Reloadly |
| Xoxoday | MOCKED | Awaiting API key + catalog |
| ONDC / Zepto | MOCKED | Smart router simulated |
| Amazon Affiliate | MOCKED | Provider ready, no live key |
| Flipkart Affiliate | MOCKED | Provider ready, no live key |
| Airtime (Recharge) | LIVE | Mobile recharge via partner API |

---

## Prioritized Backlog

### P0 — Production (Do Now — User Action Required)
- [ ] Switch Razorpay test keys → live keys (user must provide rzp_live_* keys to .env)
- [ ] Complete Resend DNS verification (user must add DNS records at resend.com/domains)
- [ ] Cashfree: await compliance approval + activate live keys
- [ ] Update assetlinks.json with SHA-256 from signed APK (user must run keytool on keystore)
- [ ] Deploy latest code to free11.com (git pull + build + restart on production server)
- [ ] Add REACT_APP_FIREBASE_APP_ID to frontend/.env (currently empty)
- [ ] Google Play: Complete identity verification + closed test (20 testers × 14 days)

### P1 — Soon
- [ ] Reloadly INR: contact support to enable product IDs 18678, 18677, 15714
- [ ] Woohoo or Gyftr integration (India-first gift card alternative to Reloadly INR)
- [ ] FCM push campaigns ("Predict live!")
- [ ] Better product images in Shop
- [ ] Fix Xoxoday voucher redeem to use atomic coin deduction (currently non-atomic, low risk since mocked)
- [ ] Add router settle per-user rate limit to in-memory fallback (currently Redis-only)

### P2 — Future
- [ ] Refactor v2_routes.py (1300+ lines → smaller domain routers)
- [ ] iOS App (WKWebView wrapper)
- [ ] Live ONDC/Zepto router (replace mocked providers)
- [ ] Xoxoday integration (API key + catalog needed)
- [ ] Squad vs Squad Battles
- [ ] UTM tracking for growth/reels
- [ ] Advanced cohort retention analytics
- [ ] Cashfree live integration (pending compliance)

---

## Security Audit Results (March 2026)

### Fixed
- ✅ `/api/admin/analytics` — Now requires admin auth (was public)
- ✅ `/api/admin/beta-metrics` — Now requires admin auth (was public)
- ✅ `/api/admin/brand-roas` — Now requires admin auth (was public)
- ✅ `POST /api/products` — Now requires admin role (was any authenticated user)
- ✅ `POST /api/coins/checkin` — Atomic check-in (was race-condition exploitable)
- ✅ `POST /api/redemptions` — Atomic stock+coin deduction (was two-step vulnerable)
- ✅ Rate limiter — In-memory fallback when Redis unavailable (was pass-through)
- ✅ DB indexes — 10 critical indexes added for performance at scale

### Known Remaining (P1)
- ⚠️ `POST /api/v2/vouchers/redeem` — Non-atomic coin deduction (low risk: Xoxoday MOCKED)
- ⚠️ Router settle per-user rate limit only works with Redis (no in-memory fallback)
- ⚠️ FIREBASE_APP_ID empty in frontend .env (affects FCM push notifications)

---

## Test Credentials
- **Admin**: admin@free11.com / Admin@123
- **Test User**: test_redesign_ui26@free11test.com / Test@1234

---

## CHANGELOG

### March 2026 — Activation Trigger + Streak-at-Risk Notifications
- **`send_activation_trigger_campaign`** (new): targets users registered 20-28h ago with 0 predictions → personalized FCM push + in-app notification; idempotent via `activation_push_sent` DB flag; runs every scheduler tick
- **`send_streak_reminder_campaign`** enhanced: upgraded to 3+ day streak (was 2+), 20h inactivity window (was 23h), personalized copy with `hours_left` countdown, fires at 20:00 AND 22:00 IST
- **In-app notification center**: All campaigns also write to `db.notifications` (same collection as existing `GET /api/v2/notifications` endpoint)
- **Notification bell**: Added to top Navbar with animated unread badge (polls 60s), `data-testid=notification-bell-btn`
- **`NotificationPanel.js`**: Slide-in panel (Framer Motion), shows last 20 notifications with type-specific icons/colors, marks all read on open (1.2s delay), deep-links to relevant pages
- **Admin test trigger**: `POST /api/v2/notifications/trigger-test` — inserts test activation + streak notifications instantly for admin testing (admin-only, 403 for non-admin)

### March 2026 — UI/UX Redesign (45-Second First-Prediction Journey)
- **QuickPredict inline component** (`Dashboard.js`): Live match with YES/NO boundary prediction buttons is now the FIRST element above the fold. New users see the prediction opportunity in <2 seconds after opening the app.
- **Content reorder**: Dashboard now shows QuickPredict → IPLCarousel → OnboardingChecklist → User Header → Check-in (was: IPLCarousel → Checklist → Banner → Header → ... → Live Match → at bottom)
- **Post-prediction state**: After submission, QuickPredict transitions to a "See All Matches →" confirmation card (handles both success and oracle-mismatch gracefully)
- **OnboardingChecklist enhanced**: Framer Motion animated progress bar + icon-per-step, improved visual hierarchy
- **FirstPredictionBanner enhanced**: Animated shimmer sweep, Framer Motion entrance, more urgent copy
- **Bottom navigation simplified**: 4 tabs only — Home | Predict | Rewards | Profile (removed Games, Missions)
- **Predict tab elevated**: Gold pill button style (larger) to prime tap intent
- **Analytics tracking**: `initSessionTimer()` fires on Dashboard mount, `trackFirstPredictionTime(duration_seconds)` fires after first successful prediction → feeds `/admin/analytics-360` metrics
- **Session tracking**: All events now include `session_id` + `platform` (user-agent)
- **New backend route**: `GET /api/admin/analytics-360` — admin-only (401/403 enforced)
  - Queries 10+ MongoDB collections in parallel
  - Filters real external users (excludes all test/seed/admin accounts)
  - Returns: high_level summary, per-user 360° profiles, 6-stage funnel, DAU 7d, top events, monetization data
- **CSV export**: `GET /api/admin/analytics-360/export/csv` — streaming CSV, auth-protected
- **New frontend page**: `src/pages/AdminAnalytics.js` at `/admin/analytics`
  - 5 tabs: Overview | Users | Funnel | Events | Monetization
  - Sortable user table with per-row expand (predictions, coins history, orders)
  - Native CSV export for all tables (fetch+Blob pattern for auth)
  - Bar charts (DAU, top events, coins by source) via Recharts
  - Per-user drop-off funnel stage labeling
- **Security fix**: Both analytics endpoints properly enforce admin JWT auth (fixed during testing)
- **Tracking improvement**: `src/utils/analytics.js` now includes `session_id` and `platform` (UA) in all tracked events
- **Navigation**: "Analytics 360°" button added to AdminV2 control panel header

### March 2026 — Phase 1-6 Platform Upgrade (Production-Ready)
- **Phase 1 Security**:
  - X-Request-ID + X-Response-Time tracing middleware on all responses
  - Global standardized 422 error handler (clean JSON envelope)
  - Global 500 error handler with request_id for traceability
- **Phase 2 Performance**:
  - `GET /api/products` now paginated: `{products:[], total:N, skip:N, limit:N}` + search param + Redis cache
  - `GET /api/coins/transactions` now paginated: `{transactions:[], total:N, skip:N, limit:N}`
  - Frontend api.js and Shop.js updated for paginated response shapes
- **Phase 3 Refactoring**:
  - `v2_routes.py` reduced from 1329 lines → 35-line aggregator
  - 5 new domain-specific route files: `routes/v2_contests.py`, `routes/v2_earn.py`, `routes/v2_matches.py`, `routes/v2_commerce.py`, `routes/v2_engagement.py`
  - `v2_engines.py` centralizes engine instances; no circular imports
- **Phase 4 Testing**:
  - New comprehensive test suite: `/app/backend/tests/test_platform_v2.py` (48 tests, 100% pass)
  - Covers: auth, security, race conditions, pagination, validation, DB indexes, V2 route health
- **Phase 5 User Activation**:
  - `FirstPredictionBanner` component: hero nudge for users with 0 predictions (with 3-step explainer + CTA to live match)
  - `OnboardingChecklist` component: 4-step guided onboarding (checkin, predict, shop, game) with progress bar + dismiss
  - Both components use session storage for dismiss — correct ephemeral behavior
- **Phase 6 Production Readiness**:
  - Startup env validation: crashes on missing MONGO_URL/DB_NAME; warns on weak JWT, CORS=*, test Razorpay
  - `v2_routes.py` streamlined to fail-fast on bad import

### March 2026 — Production Security Audit & Hardening (previous)
- **Security Audit** conducted: 5 critical vulnerabilities found and patched
- **Admin endpoints secured**: `/api/admin/analytics`, `/api/admin/beta-metrics`, `/api/admin/brand-roas` — now require admin auth
- **Product creation secured**: `POST /api/products` now requires `is_admin=true`
- **Check-in race condition fixed**: Atomic `find_one_and_update` prevents double awards
- **Redemption race condition fixed**: Atomic stock + coin deduction with rollback
- **Rate limiter hardened**: In-memory fallback added (no longer pass-through without Redis)
- **DB indexes added**: 10 indexes across 6 collections for 300k-user scale
- **Test suite created**: 31 security tests passing at `/app/backend/tests/test_security_audit_53.py`

### Feb–March 2026 — PWA Polish + Auth + Play Store + Full Audit
- Android TWA build errors resolved; signed AAB generated
- Firebase Phone Auth added (Login.js + /api/auth/phone-verify)
- FCM fix: send_all → send_each (deployment blocker resolved)
- ScrollToTop component (fixes page scroll on navigation)
- PWA Install button added to Profile page
- Leaderboard admin/seed user filtering
- Hardcoded brand names removed from UI
- All fake stats removed from entire app
- Play Store listing updated: multi-game focus, no fake numbers, correct IAP info
- PRD fully audited and synced with codebase (Feb 2026)

### December 2025 — Full i18n Translations + SEO Overhaul
- Complete translations for all 8 Indian languages
- Comprehensive SEO strategy implemented
- 25 FAQ entries with Schema.org FAQPage for rich snippets
- Enhanced sitemap.xml with all blog articles

### Phase Final — Multi-game Launch Ready
- Card Games: Rummy, Teen Patti, Poker, Solitaire
- Quest Engine, Smart Router, Sponsored Pools
- SEO: Blog, structured data, robots.txt, sitemap.xml
- Legal pages: Terms, Privacy, Disclaimer, Responsible Play, Refund Policy

### Phase 8 — Integrations
- AdMob rewarded ads (20 coins, 5/day)
- Resend Email OTP (HTML template)
- Firebase FCM push
- Razorpay test payments (FREE Bucks), Wallet history page

### Phase 7
- Referral double-payout fix, "TBA vs TBA" bug fix
- Wishlist Tracker, Streak "Hot Hand" multiplier, Live Crowd Meter, AI Daily Puzzle, Weekly Report Card
- Full UI/UX redesign: gold/charcoal, Bebas Neue, bottom nav

### Phase 1–6 (Pre-session)
- Full auth (OTP, WebAuthn, JWT), cricket data, prediction engine, fantasy builder
- Contest system, coin economy, shop + redemptions
- Leaderboards, duels, social feed, admin panel, PWA, i18n 8 langs, KYC, referrals, clans
