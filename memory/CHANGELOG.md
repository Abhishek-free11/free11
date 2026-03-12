# FREE11 — Changelog

All notable changes to FREE11, in reverse-chronological order.

---

## [RC 1.6] – March 10, 2026 — Smart Commerce Router v2

### Added
- **Smart Commerce Router** — Unified redemption layer aggregating 4 providers:
  - **ONDC** (groceries/rations, ~45 min metro delivery): atta, rice, oil, daal, biscuits, etc.
  - **Xoxoday Plum** (instant digital vouchers): Amazon/Flipkart/Swiggy/Zomato/Myntra gift cards, mobile recharge
  - **Amazon Affiliate** (electronics/lifestyle): earbuds, cables, water bottles, yoga mats, jerseys
  - **Flipkart Affiliate** (fashion/electronics): T-shirts, jeans, shoes, smartwatch, headphones
- **Provider scoring formula** (Redis-cached 600s):
  `score = 0.50×delivery_speed + 0.25×value_score + 0.15×margin_score + 0.10×geo_match`
  - `atta_5kg + MH → ONDC wins (score 0.9048, ~45 min)`
  - `amazon_gc_100 → Xoxoday wins (score 0.89, instant)`
- **`backend/providers/` directory** with `base_provider.py` + 4 provider implementations
- **`router_service.py` rewrite** — provider registry, scoring, `get_best_provider()`, `get_aggregated_skus()`
- **API endpoints** (`/api/v2/router/`):
  - `GET /skus` — 33 aggregated SKUs from all providers with dynamic demand pricing
  - `GET /tease?sku=&geo_state=` — scored options, best provider, ETA, value note
  - `POST /settle` — auto-select best, atomic coin deduction, provider redeem, log to `router_orders`
- **Rate limiting** on settle: 5 req/user/min (Redis; graceful fallback when Redis unavailable)
- **`router_orders` MongoDB collection** with schema: `{id, user_id, sku, provider, coins_used, order_status, result_data, created_at, score_used, eta_used, value_score_used, geo_state}`
- **Shop.js Smart Deals section** — horizontal scrollable carousel above existing product catalogue:
  - Category pills (Groceries, Vouchers, Food, Electronics, Fashion, Lifestyle, Recharge)
  - Provider badges (ONDC/INSTANT/AMAZON/FLIPKART) + ETA badge + value % indicator
  - Click → Router Tease Modal: best provider preview with coins/₹value/ETA before confirming
  - Settle → 3 response handlers: voucher_code (QR dialog), redirect_url (window.open), order_id (toast)
- **AdminV2 "Router" tab** — KPI dashboard: total orders, provider distribution (pie chart), avg coin price, avg value score, conversion rate, top SKUs
- **`GET /api/v2/kpis/router`** — admin-only router analytics endpoint
- **Tease view tracking** — Redis counter with MongoDB fallback for conversion rate KPI
- **`ROUTER_MODE=mock`** feature flag in `.env` — swap to `live` when real API keys added, zero code changes

### Architecture
```
backend/providers/
  ├── __init__.py
  ├── base_provider.py       (ABC with get_skus, supports_sku, get_price, get_real_price, get_eta, get_margin, redeem)
  ├── ondc_provider.py       (10 grocery SKUs, metro 45-min ETA)
  ├── xoxoday_provider.py    (11 digital vouchers, instant)
  ├── amazon_provider.py     (6 electronics/lifestyle, affiliate redirect)
  └── flipkart_provider.py   (6 fashion/electronics, affiliate redirect)
```

### Tested
- 12/12 E2E scenarios PASS + 29/29 pytest backend tests PASS — iteration_43.json
- Scoring verified: atta_5kg→ONDC, amazon_gc_100→Xoxoday, earbuds_basic→Amazon
- Settlement: ONDC→order_id, Xoxoday→voucher_code+QR, Amazon/Flipkart→redirect_url

### Mocked (swap to live without code changes)
- All 4 providers return mock data. Set `ROUTER_MODE=live` and add provider API keys to `.env`

---

## [RC 1.5] – March 10, 2026 — Email OTP Login Tab

### Added
- **Magic-link Login on Login page**: New "EMAIL OTP" tab alongside the existing "PASSWORD" tab. Users who registered without a password (OTP-only magic-link) can now sign back in using email + OTP. Flow: enter email → Send OTP → 6-box code input → Verify & Sign In → /match-centre. Uses the same `/api/auth/verify-otp-register` endpoint (logs in existing users OR creates new account).

### Fixed
- **`verifyOtp` error handling**: Reordered `res.ok` check before `res.json()` to prevent Sentry's replayIntegration consuming 4xx response bodies, which previously showed "Network error" instead of "Incorrect code".
- **`sendOtp` rate-limit handling**: Now shows "Too many requests" toast on HTTP 429 instead of silently succeeding.

### Tested
- 100% backend (14/14) + 92% frontend on first run → both bugs fixed → ready — iteration_41.json

---

## [RC 1.4] – March 10, 2026 — Master Audit + Balance Fix

### Audited
- **Master E2E Audit (iteration_40.json)**: 56/56 backend + 97% frontend across 30 complete user journeys — Registration, Login, Dashboard, Daily Check-in, Predict, Watch & Earn, Shop, Leaderboard (all 3 tabs), Referrals, Profile, Wallet, Match Centre, Admin Panel, Blog, FAQ, Landing, Sponsored Pools, Quest, Earn, IPL Countdown, PWA manifest, robots.txt/sitemap, error handling.

### Fixed
- **Coin balance discrepancy on Ledger page**: `Ledger.js` was showing `LedgerEngine.get_balance()` (stale, ledger-entry-computed = 50) instead of `user.coins_balance` (authoritative = 215). Fixed to always display `user.coins_balance` as the true balance, with ledger-computed as fallback.

---

## [RC 1.3] – March 10, 2026 — Critical Signin Bug Fix

### Fixed
- **Missing `/api/auth/verify-otp-register` endpoint** (404): Created new magic-link endpoint that verifies OTP, then either logs in an existing user OR auto-creates a new account — returns JWT in both cases. This was the root cause of the blank white screen on sign-in.
- **Register.js calling `login()` with wrong signature**: `login(access_token, user)` was calling AuthContext's `login(email, password)` method (which calls /api/auth/login). Fixed by using `loginWithToken(token)` instead.
- **Google login button in Register.js pointing to wrong URL**: Was hitting `${BACKEND_URL}/api/auth/google` (404). Fixed to redirect to `https://auth.emergentagent.com/?redirect=...` (same as Login.js).
- **AuthContext `loginWithToken` race condition**: Missing `setLoading(true)` caused PrivateRoute to see `user=null, loading=false` and immediately redirect to `/login` before `fetchUser` could complete. Fixed by calling `setLoading(true)` before `setToken`.
- **App.js `AuthCallback` (Google OAuth) not updating context**: Was only setting `localStorage.setItem(token)` without calling `setToken`. After Google OAuth, navigating to `/dashboard` bounced to `/login`. Fixed by calling `loginWithToken(data.token)`.

### Tested
- 100% backend (17/17), 95% frontend — all signin/register flows verified — iteration_39.json

---

## [RC 1.2] – March 9, 2026 — Refer a Friend Feature

### Added
- **Referrals page** (`/referrals`): Full redesign with gold/dark branding — unique referral code display, one-tap Copy Link (copies full deep URL), Share Invite (Web Share API), Show/Hide QR code toggle (qrcode.react), stats row (Friends Joined, Coins Earned, Per Referral), apply-a-friend's-code input, and 3-step How It Works section.
- **Deep link referral URL**: Shares `{origin}/register?ref=CODE` — keeps friends inside the FREE11 ecosystem. QR code encodes this same URL.
- **Register.js auto-apply**: Reads `?ref=CODE` from URL on the registration page; after successful join, silently calls `v2BindReferral` and shows a toast nudging the user to complete 3 predictions to unlock the reward.
- **Dashboard nudge card**: New "Invite Friends, Earn Together" card (with `data-testid="referral-nudge"`) links to `/referrals`.
- **Rewards**: Referrer gets +50 coins, referee gets +25 coins, unlocked after referee completes 3 predictions.

### Tested
- 100% backend (14/14) + 100% frontend (16/16 scenarios) — iteration_37.json

---

## [RC 1.1] – March 9, 2026 — E2E Regression Fixes

### Fixed
- **Dashboard rank fallback**: UserHeader now derives rank from `user.level` directly (Rookie/Amateur/Pro/Expert/Legend), eliminating the brief 'Rookie' flash before `demandProgress` loads.
- **Leaderboard accessibility**: Tab labels (Global/Weekly/Streak) now always visible on all screen sizes (removed `hidden sm:inline` restriction).

### Tested
- Full E2E regression: 100% backend (32/32), 97% frontend — all new features (tutorial, OTP flow, PWA banner, IPL countdown) verified working.

---

## [RC 1.0] – March 9, 2026 — IPL 2026 Launch Candidate ✅

### Added
- **Legal compliance**: `SkillDisclaimerModal` + `SkillBadge` integrated on 6 surfaces (Shop, SponsoredPools, QuestModal, Predict, LiveMatch, Landing footer). Disclaimer text aligned with Promotion and Regulation of Online Gaming Act, 2025.
- **Distribution Engine**: `ShareCard` component with native share + copy — triggers on redemption success, quest completion, leaderboard top-3.
- **Blog**: `/blog` and `/blog/ipl-guide` with SEO-optimised content, FAQs, structured data (JSON-LD FAQPage).
- **Google OAuth2**: Social login button on Login page (Emergent-managed).
- **Framer Motion**: UI animations — coin glow, quest slide-up, redemption burst, page entrance stagger.
- **PWA**: Enhanced `manifest.json` (standalone display, all icon sizes 72–512px) + `PWAInstallBanner` in App.js.
- **Performance**: React.lazy + Suspense for 30+ heavy pages; critical font preloads in `index.html`.
- **SEO**: Full meta/OG/Twitter tags, JSON-LD `MobileApplication` + `FAQPage`, `robots.txt`, `sitemap.xml`.
- **Admin Analytics**: ARR forecast chart + breakage ratio KPI card in AdminV2 (Recharts).
- **Push Campaigns**: `push_routes.py` — `POST /api/v2/push/campaign` (FCM dry-run + real send).
- **Quest Engine**: Rebound quest modal — opt-in after prediction loss (streak < 3), ad +20 coins OR grocery tease. SkillBadge + ShareCard on completion.
- **Smart Router**: `/api/v2/router/tease` — mock ONDC/Zepto/BigBasket/Flipkart scoring (0.7×eta + 0.2×margin + 0.1×geo), Redis cached.
- **Sponsored Pools**: Brand-funded prize pools (Pepsi/Parle-G/Fortune seeded), admin finalize, 20% platform cut. SkillBadge + SkillDisclaimerModal on page.
- **50 SKUs seeded**: 30 grocery items (atta, Pepsi, oil ₹20–500) + 20 lifestyle rewards.
- **IPL Carousel**: 4-slide hero on Dashboard (IPL 2026 / Mega Contest / Sponsored / Free Rewards).
- **KPIs API**: `/api/v2/kpis` — opt-in%, repeats%, pool_lift, revenue estimates; `/cohort-csv` export.

### Fixed
- **OTP "Failed to send" bug**: `otp_engine.py` now always returns `sent: true` if OTP stored in DB. Inline `dev_otp` shown clearly in UI when Resend domain unverified. Rate-limit (429) still enforced separately.
- **Duplicate HTML title tags** in `index.html` — single canonical `<title>` tag.
- **Landing.js section ordering** — hero → how it works → KPIs → SEO content → CTA → footer.
- **Seeded product images** — Tata Salt, Parle-G, Uttam Sugar updated to relevant food images.

### Changed
- **Positioning**: "Consumption Operating System" → "Sports entertainment platform where users earn real grocery rewards." Tagline: "Play Cricket. Earn Essentials."
- **Legal language**: All "PRORGA" references → "Promotion and Regulation of Online Gaming Act, 2025" (short form: "Online Gaming Act, 2025").
- **App.js**: All 30+ page imports converted to `React.lazy` with `Suspense` fallback spinner.
- **Footer disclaimer**: Static text → interactive button that opens `SkillDisclaimerModal`.

### Infrastructure
- `firebase@12.10.0` added to `package.json` (deployment blocker resolved).
- MongoDB Atlas `authSource=admin` connection string fix.

---

## [0.9.0] – February 2026 — Phase 8: Integrations

### Added
- AdMob rewarded ads (`POST /api/v2/ads/reward`, +20 coins, 5/day cap, Android TWA `RewardedAdActivity`)
- Resend email OTP with HTML template
- Firebase FCM push notifications (service account + FCM delivery)
- Razorpay test payments — FREE Bucks purchase flow, Wallet history page

---

## [0.8.0] – January 2026 — Phase 7: UX & Engagement

### Added
- Wishlist Tracker, Streak "Hot Hand" multiplier
- Live Crowd Meter (Redis-backed, real-time)
- AI Daily Puzzle (Gemini Flash via Emergent LLM key)
- Weekly Report Card (user performance digest)
- Full UI/UX redesign: gold/charcoal design system, Bebas Neue headings, bottom navigation

### Fixed
- Referral double-payout bug
- "TBA vs TBA" match display bug

---

## [0.1.0 – 0.7.0] – 2025 — Phases 1–6: Foundation

### Added
- Full authentication: OTP, WebAuthn, JWT
- Cricket data pipeline via EntitySport
- Prediction engine + result settlement
- Fantasy team builder
- Contest system: Mega / Standard / Practice / H2H / Private rooms
- Coin economy + ledger
- Shop + redemptions
- Leaderboards, duels, social feed
- Admin panel
- Progressive Web App (service worker, manifest)
- Internationalization: 8 languages (English, Hindi, Bengali, Tamil, Telugu, Kannada, Malayalam, Marathi)
- KYC, referrals, clans
