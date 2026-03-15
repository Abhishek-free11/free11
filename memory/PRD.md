# FREE11 — Product Requirements Document
<!-- Last updated: Feb 2026 — Firebase config complete, dynamic home page, real card games, PWA nudges restored, full production config done -->

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
- **Database**: MongoDB (managed by Emergent in production)
- **AI**: Google Gemini Flash via `emergentintegrations` (Emergent LLM Key)
- **Payments**: Razorpay (TEST MODE — live keys needed) + Cashfree (pending compliance)
- **Notifications**: Firebase FCM (live), Resend email (live, DNS verified ✅)
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
- **Navigation**: Mobile-first 5-tab bottom nav (Home | Predict | Games | Rewards | Profile)

---

## Production URLs
- **Live app**: https://free11.com
- **WWW**: https://www.free11.com
- **Sandbox/Preview**: https://activation-engine.preview.emergentagent.com
- **Hosting**: Emergent (managed MongoDB + infra)

---

## FREE Bucks Packages (In-App Purchase via Razorpay)

| Package ID | Label | Price | FREE Bucks | Bonus |
|---|---|---|---|---|
| starter | Starter Pack | ₹49 | 50 | 0 |
| popular | Popular Pack | ₹149 | 160 | +10 |
| value | Value Pack | ₹499 | 550 | +50 |
| mega | Mega Pack | ₹999 | 1,200 | +200 |

- Payment via **Razorpay** (TEST MODE — live keys still needed)
- **Cashfree** as fallback (pending compliance approval)
- Neither FREE Bucks nor FREE Coins can be withdrawn as cash

---

## Key DB Schema

### Existing Collections
| Collection | Key Fields |
|---|---|
| users | coins_balance, free_bucks, xp, level, streak_days, last_checkin, prediction_streak, wishlist_product_id, coin_expiry_date (180d rolling), activation_push_sent |
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
| notifications | user_id, type, title, message, link, is_read, created_at |

### DB Indexes
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
- GET /api/v2/es/matches?status=3 *(EntitySport live)*
- GET /api/v2/es/match/:id/live *(live scorecard data)*
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
- POST /api/products *(admin only)*
- POST /api/redemptions *(atomic stock+coin deduction)*
- GET /api/redemptions

### Quest & Router
- GET /api/v2/quest/status
- POST /api/v2/quest/offer, /claim-ad, /ration-viewed, /dismiss
- GET /api/v2/router/tease, POST /api/v2/router/settle, GET /api/v2/router/skus

### Notifications
- GET /api/v2/notifications
- POST /api/v2/notifications/trigger-test *(admin only)*

### Admin & Analytics
- GET /api/admin/analytics *(admin only)*
- GET /api/admin/analytics-360 *(admin only — 10+ collection aggregation)*
- GET /api/admin/analytics-360/export/csv *(admin only — streaming CSV)*
- GET /api/admin/beta-metrics *(admin only)*
- GET /api/admin/brand-roas *(admin only)*
- GET /api/v2/kpis *(admin only)*
- GET /api/v2/kpis/cohort-csv

---

## External Integrations Status

| Integration | Status | Notes |
|---|---|---|
| EntitySport | ✅ LIVE | Cricket data, match scores, live scorecard |
| Redis | ✅ LIVE | Crowd Meter + Router caching. In-memory fallback active |
| Sentry | ✅ LIVE | Error monitoring |
| Gemini Flash | ✅ LIVE | AI puzzle (Emergent LLM Key) |
| Google Auth | ✅ LIVE | Emergent-managed OAuth2 |
| Firebase FCM | ✅ LIVE | send_each (fixed from send_all) |
| Firebase Phone Auth | ✅ LIVE | Added Feb 2026 |
| Firebase App ID | ✅ LIVE | `1:725923627857:web:8f5781a890c37c24679d01` |
| Firebase VAPID Key | ✅ LIVE | Web push certificates configured |
| Firebase Auth Domains | ✅ LIVE | free11.com, www.free11.com, all preview URLs authorized |
| Resend Email | ✅ LIVE | API key active + DNS verified |
| AdMob | ✅ LIVE | User's own API keys |
| Razorpay | ⚠️ TEST MODE | Test keys only — live keys needed for real payments |
| Cashfree | 🔴 PENDING | Awaiting compliance approval from Cashfree team |
| Reloadly (USD) | ✅ LIVE | Swype/Razer gift cards working |
| Reloadly (INR) | 🔴 BLOCKED | Product IDs 18678, 18677, 15714 need enabling by Reloadly |
| Xoxoday | 🟡 MOCKED | Awaiting API key + catalog |
| ONDC / Zepto | 🟡 MOCKED | Smart router simulated |
| Amazon Affiliate | 🟡 MOCKED | Provider ready, no live key |
| Flipkart Affiliate | 🟡 MOCKED | Provider ready, no live key |
| Airtime (Recharge) | ✅ LIVE | Mobile recharge via partner API |
| MongoDB | ✅ LIVE | Managed by Emergent in production |

---

## Prioritized Backlog

### P0 — Only Remaining Production Blocker
- [ ] **Razorpay**: Switch test keys → live keys (`rzp_live_*` keys → backend .env). This is the ONLY remaining blocker for real payments.

### P1 — Soon
- [ ] Reloadly INR: contact support to enable product IDs 18678, 18677, 15714
- [ ] Cashfree: await compliance approval + activate live keys
- [ ] Google Play: Complete identity verification + closed test (20 testers × 14 days)
- [ ] Update assetlinks.json with SHA-256 from signed APK
- [ ] Woohoo or Gyftr integration (India-first gift card alternative to Reloadly INR)
- [ ] FCM push campaigns ("Predict live!")
- [ ] Better product images in Shop
- [ ] Fix Xoxoday voucher redeem to use atomic coin deduction (currently non-atomic, low risk since mocked)

### P2 — Future Dev Work
- [ ] Refactor v2_routes.py (large file → smaller domain routers)
- [ ] iOS App (WKWebView wrapper for App Store)
- [ ] Live ONDC/Zepto router (replace mocked providers)
- [ ] Xoxoday integration (API key + catalog needed)
- [ ] Enhance Rummy/Poker/Solitaire with same animation polish as Teen Patti rewrite
- [ ] Add live multiplayer via WebSockets (games currently AI-only)
- [ ] Squad vs Squad Battles
- [ ] UTM tracking for growth/reels
- [ ] Advanced cohort retention analytics
- [ ] Background job queue (Celery/RQ) for async voucher fulfillment

---

## Security Audit Results

### Fixed ✅
- `/api/admin/analytics` — Now requires admin auth (was public)
- `/api/admin/beta-metrics` — Now requires admin auth (was public)
- `/api/admin/brand-roas` — Now requires admin auth (was public)
- `POST /api/products` — Now requires admin role (was any authenticated user)
- `POST /api/coins/checkin` — Atomic check-in (was race-condition exploitable)
- `POST /api/redemptions` — Atomic stock+coin deduction (was two-step vulnerable)
- Rate limiter — In-memory fallback when Redis unavailable (was pass-through)
- DB indexes — 10 critical indexes added for performance at scale
- FIREBASE_APP_ID — Now set in frontend .env ✅
- FIREBASE_VAPID_KEY — Now set in frontend .env ✅

### Known Remaining (P1)
- ⚠️ `POST /api/v2/vouchers/redeem` — Non-atomic coin deduction (low risk: Xoxoday MOCKED)
- ⚠️ Router settle per-user rate limit only works with Redis (no in-memory fallback)

---

## Test Credentials
- **Admin**: admin@free11.com / Admin@123
- **Test User**: test_redesign_ui26@free11test.com / Test@1234

---

## CHANGELOG

### Feb 2026 — Firebase Config Complete + Production Hardening
- `REACT_APP_FIREBASE_APP_ID` set: `1:725923627857:web:8f5781a890c37c24679d01`
- `REACT_APP_FIREBASE_VAPID_KEY` set: `BEiusm7D-lciKuezp9PVjtryA8OXGXMiiSsFniUziBSER8Gw65d-XahBRYEuUvEwequaf6slwyKkU8qtuFjNBS`
- Firebase authorized domains confirmed: free11.com, www.free11.com, all preview URLs ✅
- Resend DNS confirmed verified ✅
- Production confirmed live on Emergent at **free11.com** ✅
- MongoDB confirmed managed by Emergent (no external Atlas needed) ✅
- Atlas cluster created (free11-prod, ap-south-1) — available as backup/migration option

### Feb 2026 — Dynamic Home Page + Real Card Games
- **Dynamic Dashboard**: `isImportantMatch()` detects IPL/ICC/T20 WC/ODI WC/Test/India matches
  - IF important live match: QuickPredict first + LiveScorecard (Cricbuzz-style) right below (45s KPI protected)
  - ELSE: "Play & Earn Now" CardGamesCarousel as first element (Teen Patti, Rummy, Poker, Solitaire)
  - LiveScorecard (`components/LiveScorecard.js`): batsmen, bowlers, CRR/RRR, ball-by-ball ticker, EntitySport data
- **Teen Patti Real Rules Rewrite** (`TeenPattiGame.js`):
  - Boot amount selection (10/20/50 coins)
  - Blind/Seen mode with proper chaal multipliers (blind=×1, seen=×2)
  - Sideshow (compare hands with AI, accept/reject logic)
  - Pack, Show (force reveal), Showdown
  - AI personalities: conservative vs aggressive
  - Framer Motion pot burst + confetti on win
  - +40 coin API reward via `/v2/earn/teen-patti-win`
- Rummy/Poker/Solitaire untouched (already had real rules)
- OnboardingChecklist + FirstPredictionBanner updated to mention card games

### Feb 2026 — PWA & Biometric Nudge Fix
- Restored `PWAInstallButton` FAB in `App.js` (shows after full bottom sheet dismissed once)
- Added `PWANudge` card in Dashboard (always visible for non-installed users)
- Added `BiometricNudge` card in Dashboard (for users who haven't set up biometrics)
- Fixed Login.js race condition: biometric modal now appears correctly after email/password login
- Biometric setup now works directly from Dashboard (no re-login required)

### March 2026 — Notification Engine
- `send_activation_trigger_campaign`: targets users 20-28h after registration with 0 predictions
- `send_streak_reminder_campaign` enhanced: 3+ day streak, 20h inactivity, fires 20:00 + 22:00 IST
- In-app notification center (`NotificationPanel.js`), bell icon in Navbar with unread badge
- Admin test trigger: `POST /api/v2/notifications/trigger-test`

### March 2026 — Analytics 360° Dashboard
- `GET /api/admin/analytics-360`: queries 10+ MongoDB collections, real user filter, 6-stage funnel
- `GET /api/admin/analytics-360/export/csv`: streaming authenticated CSV export
- `src/pages/AdminAnalytics.js` at `/admin/analytics`: 5 tabs, Recharts, AgGridReact, sortable tables
- `trackFirstPredictionTime()` fires after first prediction → feeds analytics dashboard

### March 2026 — UI/UX Redesign (45-Second First-Prediction Journey)
- QuickPredict inline component is FIRST element above the fold for new users
- OnboardingChecklist + FirstPredictionBanner with Framer Motion animations
- 5-tab bottom navigation restored: Home | Predict | Games | Rewards | Profile
- Session tracking: all events include session_id + platform (UA)

### March 2026 — Phase 1-6 Platform Upgrade
- Security: X-Request-ID tracing, global error handlers
- Performance: paginated products + transactions, Redis cache
- Refactoring: v2_routes.py → 5 domain-specific route files
- Testing: 48-test suite at `/app/backend/tests/test_platform_v2.py`
- Activation: FirstPredictionBanner + OnboardingChecklist components
- Production: startup env validation, fail-fast on missing config

### Feb–March 2026 — PWA Polish + Auth + Play Store
- Android TWA build errors resolved; signed AAB generated
- Firebase Phone Auth added
- FCM fix: send_all → send_each
- ScrollToTop component, PWA Install button in Profile
- All fake stats removed, Play Store listing updated

### Dec 2025 — i18n + SEO
- Complete translations for all 8 Indian languages
- Comprehensive SEO: FAQ Schema, sitemap.xml, blog articles

### Phase 1–8 (Foundation)
- Full auth (OTP, WebAuthn, JWT), cricket data, prediction engine, fantasy builder
- Contest system, coin economy, shop + redemptions
- Leaderboards, duels, social feed, admin panel, PWA, referrals, clans
- Card Games: Rummy, Teen Patti, Poker, Solitaire
- Quest Engine, Smart Router, Sponsored Pools
- AdMob, Resend, Firebase FCM, Razorpay (test), Wallet
- Wishlist Tracker, Streak multiplier, Crowd Meter, AI Puzzle, Weekly Report
- Legal pages: Terms, Privacy, Disclaimer, Responsible Play, Refund Policy
