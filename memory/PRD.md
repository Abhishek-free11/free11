# FREE11 — Product Requirements Document
<!-- Last updated: Feb 2026 — Full PRD audit & sync with codebase -->

## What is FREE11?

FREE11 is a free skill-based gaming and rewards platform. Users play cricket predictions, card games, daily quests, and puzzles — earn FREE Coins — then redeem them for real groceries, vouchers, and digital rewards.

**Tagline:** "Play Games. Earn Real Rewards." *(formerly "Play Cricket. Earn Essentials." — updated to reflect multi-game nature)*

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
- **Rate limiter**: API rate limiting active.
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
- **Frontend**: React 18, Tailwind CSS, Framer Motion, PWA (service worker + manifest), i18n 8 langs
- **Backend**: FastAPI (Python), Motor (async MongoDB), APScheduler, Redis
- **Database**: MongoDB
- **AI**: Google Gemini Flash via `emergentintegrations` (Emergent LLM Key)
- **Payments**: Razorpay (test→live pending) + Cashfree (pending compliance approval)
- **Notifications**: Firebase FCM (live), Resend email (live, DNS pending)
- **Analytics**: Sentry (live)
- **Ads**: AdMob (live)
- **Auth**: JWT + Google OAuth2 (Emergent-managed) + Firebase Phone Auth
- **Cricket Data**: EntitySport (live)
- **Gift Cards**: Reloadly (USD live, INR blocked), Xoxoday (mocked)
- **Commerce**: ONDC/Zepto/BigBasket/Amazon/Flipkart (all mocked/providers ready)

---

## Complete Architecture

```
/app/
├── android-twa/
│   ├── build.gradle                   # Fixed Kotlin/AGP versions
│   ├── local.properties               # SDK path
│   └── play_store_assets/
│       ├── play_store_listing.txt     # Full store listing (updated Feb 2026)
│       ├── feature_graphic_1024x500.png
│       ├── icon_512x512.png
│       ├── screenshot_01_predict.png
│       └── screenshot_02_shop.png
│
├── backend/
│   ├── server.py                      # Main FastAPI entry, scheduler, startup seeding
│   │
│   ├── ── AUTH & USER ──
│   ├── routes/auth_routes.py          # JWT, OTP, Google OAuth, Phone Auth (Firebase)
│   ├── otp_engine.py                  # OTP generation & verification
│   ├── progression_engine.py          # XP & tier system (Bronze→Silver→Gold→Platinum→Diamond)
│   ├── fraud_engine.py                # Device hash, duplicate detection, ban/flag/unban
│   ├── referral_engine.py             # Referral tracking & coin payouts
│   │
│   ├── ── CRICKET & PREDICTIONS ──
│   ├── cricket_routes.py              # Match data, live scores, prediction endpoints
│   ├── cricket_data_service.py        # Data aggregation layer
│   ├── cricket_service.py             # Business logic
│   ├── entitysport_service.py         # EntitySport API integration (LIVE)
│   ├── predict_engine.py              # Prediction scoring, Hot Hand multiplier
│   ├── matchstate_engine.py           # Live match state management
│   ├── contest_engine.py              # Contest scoring and payout logic
│   ├── fantasy_engine.py              # Fantasy team scoring
│   ├── fantasy_routes.py              # Fantasy team API
│   │
│   ├── ── GAMES ──
│   ├── games_routes.py                # Card game earn endpoints + leaderboard + streak
│   ├── card_game_logic.py             # Teen Patti / Rummy / Poker / Solitaire logic
│   ├── cards_engine.py                # Card deck utilities
│   ├── spin_wheel_engine.py           # Daily Lucky Spin (coin prizes, 1/day)
│   │
│   ├── ── ECONOMY & COINS ──
│   ├── economy_engine.py              # Coin earn/spend rules, daily caps
│   ├── ledger_engine.py               # Transaction ledger (LedgerEngine.get_balance/history)
│   ├── missions_engine.py             # Daily missions (progress tracking, claim rewards)
│   ├── quest_engine.py                # Rebound Quest (streak<3, opt-in ad +20 coins)
│   ├── streak_leaderboard_engine.py   # Streak tracking for leaderboard
│   │
│   ├── ── PAYMENTS ──
│   ├── freebucks_engine.py            # FREE Bucks packages: ₹49/₹149/₹499/₹999
│   ├── razorpay_routes.py             # Razorpay payment (TEST MODE — live keys pending)
│   ├── cashfree_routes.py             # Cashfree payment (pending compliance approval)
│   ├── payment_routes.py              # /api/payments/packages (backward compat)
│   │
│   ├── ── REWARDS & SHOP ──
│   ├── gift_card_routes.py            # Gift card redemption API
│   ├── reloadly_routes.py             # Reloadly gift cards
│   ├── reloadly_provider.py           # Legacy Reloadly provider
│   ├── fulfillment_routes.py          # Voucher fulfillment + order status
│   ├── providers/
│   │   ├── reloadly_provider.py       # Reloadly: USD LIVE (Swype/Razer), INR BLOCKED
│   │   ├── xoxoday_provider.py        # Xoxoday: MOCKED (awaiting API key)
│   │   ├── ondc_provider.py           # ONDC grocery: MOCKED
│   │   ├── amazon_provider.py         # Amazon affiliate: MOCKED
│   │   ├── flipkart_provider.py       # Flipkart affiliate: MOCKED
│   │   ├── airtime_provider.py        # Mobile recharge: LIVE (via partner API)
│   │   └── base_provider.py           # Provider interface
│   ├── services/
│   │   ├── ads_provider.py            # AdMob reward verification
│   │   ├── payment_provider.py        # Payment abstraction
│   │   └── voucher_provider.py        # Voucher dispatch
│   │
│   ├── ── ENGAGEMENT ──
│   ├── engagement_engine.py           # AI Daily Puzzle (Gemini), Weekly Report Card
│   ├── engagement_routes.py           # /api/v2/puzzles, /api/v2/reports
│   ├── airtime_routes.py              # Mobile recharge top-up via coins
│   │
│   ├── ── SOCIAL ──
│   ├── clans_routes.py                # Clan creation, join, leaderboard
│   ├── leagues_routes.py              # Private leagues
│   ├── leaderboards_routes.py         # Leaderboard (admin/seed filtered)
│   ├── sponsored_routes.py            # Sponsored brand pools
│   │
│   ├── ── NOTIFICATIONS & PUSH ──
│   ├── fcm_service.py                 # Firebase FCM (fixed: send_each not send_all)
│   ├── fcm_campaigns.py               # Push campaign management
│   ├── push_routes.py                 # Push notification API
│   ├── notification_engine.py         # In-app notification system
│   ├── email_service.py               # Resend email (live, DNS pending)
│   │
│   ├── ── ADMIN & ANALYTICS ──
│   ├── admin_v2_routes.py             # Admin analytics, ARR forecast, KPIs
│   ├── kpi_routes.py                  # Platform KPIs (/api/v2/kpis)
│   ├── analytics_engine.py            # Internal analytics aggregation
│   ├── reports_routes.py              # Weekly reports
│   ├── brand_routes.py                # Brand portal for advertisers
│   │
│   ├── ── INFRASTRUCTURE ──
│   ├── v2_routes.py                   # All v2 routes (1300+ lines — P2 refactor needed)
│   ├── redis_cache.py                 # Redis caching (Crowd Meter + Router)
│   ├── scheduler_service.py           # APScheduler jobs
│   ├── websocket_manager.py           # WebSocket for live match updates
│   ├── rate_limiter.py                # API rate limiting
│   ├── geo_fence_middleware.py        # India-only geo restriction
│   ├── feature_gate.py                # Feature flags
│   ├── feature_routes.py              # Feature flag API
│   ├── alerting_service.py            # Error alerting
│   ├── beta_routes.py                 # Beta feature routes
│   ├── router_service.py              # Smart commerce router (ONDC/Zepto mock)
│   ├── faq_routes.py                  # FAQ content API
│   ├── support_routes.py              # User support tickets
│   └── .env
│
└── frontend/src/
    ├── App.js                         # Root layout, lazy routes, PWA banner, ScrollToTop
    ├── index.css                      # Design system CSS
    │
    ├── ── PAGES ──
    ├── pages/Landing.js               # Hero, features, SEO, legal footer (no fake stats)
    ├── pages/Login.js                 # Email/OTP + Google OAuth + Firebase Phone Auth
    ├── pages/Register.js              # OTP registration flow
    ├── pages/Dashboard.js             # IPL Carousel + Quest modal hook + LiveActivityTicker
    │
    ├── ── CRICKET ──
    ├── pages/Predict.js               # Match prediction (SkillBadge in header)
    ├── pages/LiveMatch.js             # Live match view (SkillBadge in header)
    ├── pages/MatchCentre.js           # Match listing + Card Games promo empty state
    ├── pages/ContestHub.js            # Contest listing (Sponsored Pools banner)
    ├── pages/TeamBuilder.js           # Fantasy team builder
    ├── pages/Cricket.js               # Redirects to /predict
    │
    ├── ── GAMES ──
    ├── pages/CardGames.js             # Games hub (Rummy/Teen Patti/Poker/Solitaire + leaderboard)
    ├── pages/GameLobby.js             # Per-game lobby (Play vs AI, Quick Play, Create Room)
    ├── pages/RummyGame.js             # 13-card Rummy vs AI (+50 coins/day)
    ├── pages/TeenPattiGame.js         # Teen Patti vs AI (+40 coins/day)
    ├── pages/PokerGame.js             # Texas Hold'em vs AI (+60 coins/day)
    ├── pages/SolitairePage.js         # Klondike Solitaire (+25 coins/day)
    ├── pages/GameRoom.js              # Multiplayer game room
    ├── pages/Cards.js                 # Card utilities page
    │
    ├── ── EARN & ECONOMY ──
    ├── pages/EarnCoins.js             # Earn hub (AdMob, Spin, Scratch, Quiz, Missions, Card Games)
    ├── pages/RewardedAds.js           # Watch & Earn (/watch-earn)
    ├── pages/FreeBucks.js             # FREE Bucks purchase (₹49/₹149/₹499/₹999 via Razorpay)
    ├── pages/Wallet.js                # Coin balance, FREE Bucks balance, transaction history
    ├── pages/Ledger.js                # Full transaction ledger
    ├── pages/WalletExplainer.js       # Coin system explainer
    │
    ├── ── SHOP & REWARDS ──
    ├── pages/Shop.js                  # Grocery filter, QR voucher, ShareCard, SkillModal
    ├── pages/MyOrders.js              # Order history + status
    ├── pages/SponsoredPools.js        # Sponsored brand pools + SkillBadge/Modal
    │
    ├── ── SOCIAL ──
    ├── pages/Leaderboards.js          # Weekly/monthly leaderboards + ShareCard top-3
    ├── pages/Clans.js                 # Clan creation, join, clan leaderboard
    ├── pages/PrivateLeagues.js        # Private prediction leagues
    ├── pages/Referrals.js             # Referral tracking + rewards
    ├── pages/InviteFriends.js         # Invite friends + share deep links
    │
    ├── ── ADMIN ──
    ├── pages/Admin.js                 # Admin panel (v1)
    ├── pages/AdminV2.js               # Admin v2 (Analytics dashboard + ARR Forecast + KPIs)
    ├── pages/BrandPortal.js           # Advertiser/brand portal (/brand)
    │
    ├── ── PROFILE & SETTINGS ──
    ├── pages/Profile.js               # User profile, WishlistGoal, Install App button (PWA)
    │
    ├── ── LEGAL & INFO ──
    ├── pages/AboutUs.js               # About FREE11 (clean, no fake stats)
    ├── pages/FAQ.js                   # FAQ (loads from /api/faq)
    ├── pages/Blog.js                  # SEO blog (/blog/cricket-guide)
    ├── pages/TermsAndConditions.js    # T&Cs
    ├── pages/PrivacyPolicy.js         # Privacy policy
    ├── pages/Disclaimer.js            # Skill-based disclaimer
    ├── pages/ResponsiblePlay.js       # Responsible gaming page
    ├── pages/RefundPolicy.js          # Refund policy
    ├── pages/CommunityGuidelines.js   # Community guidelines
    ├── pages/Support.js               # Support tickets
    │
    └── ── COMPONENTS ──
        ├── components/Navbar.js               # Bottom nav (Home/Play/Games/Earn/Profile)
        ├── components/IPLCarousel.js          # 4-slide hero carousel on Dashboard
        ├── components/QuestModal.js           # Rebound Quest (streak<3, opt-in)
        ├── components/SkillDisclaimerModal.js # PROGA compliance modal + SkillBadge
        ├── components/ShareCard.js            # Viral share overlay
        ├── components/SharePredictionCard.js  # Prediction share card
        ├── components/LiveActivityTicker.js   # Rotating activity feed (Landing+Dashboard)
        ├── components/WeeklyReportCard.js     # Weekly performance summary
        ├── components/WishlistGoal.js         # Wishlist tracker in Profile
        ├── components/DailyPuzzle.js          # AI puzzle component
        ├── components/CrowdMeter.js           # Live crowd prediction meter
        ├── components/HowToPlay.js            # Onboarding tutorial
        ├── components/FirstTimeTutorial.js    # First-time user tutorial
        ├── components/AppSearch.js            # Global search
        ├── components/LanguageSelector.js     # 8-language selector
        ├── components/NotificationSettings.js # FCM notification preferences
        ├── components/EmptyState.js           # Empty state UI component
        ├── components/SiteFooter.js           # Site footer with legal links
        └── App.js ScrollToTop                 # Inline ScrollToTop (fixes page scroll on nav)
```

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

- Payment via **Razorpay** (currently TEST mode — live keys needed for production)
- **Cashfree** as fallback (pending compliance approval from Cashfree team)
- Neither FREE Bucks nor FREE Coins can be withdrawn as cash

---

## Coin Earn Sources (all implemented)

| Source | Coins | Limit |
|---|---|---|
| Correct cricket prediction | 10–30 (×multiplier) | Per prediction |
| Hot Hand streak bonus | Up to 3× multiplier | Active during streak |
| Daily check-in | 10–100 (streak) | 1/day |
| Lucky Spin Wheel | Variable prize | 1/day |
| Scratch Card | Variable prize | 1/day |
| Cricket Quiz | 10 | 1/day |
| AdMob Rewarded Ad | 20 | 5/day |
| Rummy win vs AI | 50 | 1/day |
| Teen Patti win vs AI | 40 | 1/day |
| Poker win vs AI | 60 | 1/day |
| Solitaire win | 25 | 1/day |
| AI Daily Puzzle | Variable | 1/day |
| Daily Missions | Variable | Multiple/day |
| Quest (opt-in ad) | 20 | 1/day |
| Referral | 50 + 50 (referee) | Per referral |

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

---

## Key API Endpoints

### Auth
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/send-otp
- POST /api/auth/verify-otp
- POST /api/auth/google-oauth
- POST /api/auth/phone-verify *(Firebase phone auth — NEW)*
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
- POST /api/coins/checkin
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
- POST /api/redemptions
- GET /api/redemptions

### Quest & Router
- GET /api/v2/quest/status
- POST /api/v2/quest/offer, /claim-ad, /ration-viewed, /dismiss
- GET /api/v2/router/tease, POST /api/v2/router/settle, GET /api/v2/router/skus

### Sponsored Pools
- GET /api/v2/sponsored
- POST /api/v2/sponsored/join, /create, /{id}/finalize

### Engagement
- GET /api/v2/puzzles/today
- GET /api/v2/reports/weekly

### KPIs & Admin
- GET /api/v2/kpis
- GET /api/v2/kpis/cohort-csv
- GET /api/admin/analytics

### Push
- POST /api/v2/push/campaign

---

## External Integrations Status

| Integration | Status | Notes |
|---|---|---|
| EntitySport | LIVE | Cricket data, match scores |
| Redis | LIVE | Crowd Meter + Router caching |
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

## Play Store Submission Assets

Location: `/app/android-twa/play_store_assets/`

| File | Purpose | Status |
|---|---|---|
| play_store_listing.txt | Full store copy (updated Feb 2026, no fake stats) | Ready |
| feature_graphic_1024x500.png | Play Store banner | Ready |
| icon_512x512.png | App icon 512×512 | Ready |
| screenshot_01_predict.png | Phone screenshot 1 | Ready |
| screenshot_02_shop.png | Phone screenshot 2 | Ready |

**Store Listing Summary:**
- App name: FREE11 — Play Games. Earn Real Rewards.
- Short description: Play skill-based games. Earn coins. Redeem for real rewards.
- Category: Sports / Entertainment
- In-app purchases: Yes (FREE Bucks ₹49–₹999)
- Content rating: Everyone 10+ / India: 18+
- Privacy URL: https://free11.com/privacy

---

## Compliance & Branding (Feb 2026)
- All user-facing trademark names removed: Pepsi→"Cola Drink", Parle-G→"Glucose Biscuits", IPL→"T20 Season 2026"
- **Fake stats REMOVED from all pages:** 1.5L+ users, ₹8.2L+ rewards, 73% accuracy, 225M cricket fans, "India's #1", "India's leading", "India's top" — all removed
- Blog: no fabricated claims, no delivery partner guarantees
- "India's #1" → "India's Skill-Based Gaming & Rewards Platform"
- All legal pages live: /terms, /privacy, /disclaimer, /responsible-play, /refund, /guidelines
- Support email: support@free11.com everywhere
- © 2026 FREE11

---

## Prioritized Backlog

### P0 — Production (Do Now)
- [ ] Switch Razorpay test keys → live keys
- [ ] Complete Resend DNS verification (resend.com/domains)
- [ ] Cashfree: await compliance approval + activate live keys
- [ ] Google Play: Complete identity verification + closed test (20 testers × 14 days)
- [ ] Update assetlinks.json with SHA-256 from signed APK

### P1 — Soon
- [ ] Reloadly INR: contact support to enable product IDs 18678, 18677, 15714
- [ ] Woohoo or Gyftr integration (India-first gift card alternative to Reloadly INR)
- [ ] Professional translations (8 non-English locales)
- [ ] FCM push campaigns ("Predict live!")
- [ ] Better product images in Shop

### P2 — Future
- [ ] Refactor v2_routes.py (1300+ lines → smaller domain routers)
- [ ] iOS App (WKWebView wrapper)
- [ ] Live ONDC/Zepto router (replace mocked providers)
- [ ] Xoxoday integration (API key + catalog needed)
- [ ] Squad vs Squad Battles
- [ ] UTM tracking for growth/reels
- [ ] Advanced cohort retention analytics

---

## Test Credentials
- **Admin**: admin@free11.com / Admin@123
- **Test User**: test_redesign_ui26@free11test.com / Test@1234

---

## Revenue Model (KPI Targets)
- AdMob: ~₹5/user/month (₹0.35/ad × 2 ads/day × 30 days)
- Sponsored Pools: 20% platform cut on brand-funded prize pools
- FREE Bucks: ₹49–₹999 packs (Razorpay, test mode)
- Commission: 8–12% on fulfilled redemptions
- Breakage: >10% coins never redeemed (standard loyalty economics)

---

## CHANGELOG

### Phase 1–6 (Pre-session)
- Full auth (OTP, WebAuthn, JWT), cricket data, prediction engine, fantasy builder
- Contest system (Mega/Standard/Practice/H2H + private), coin economy, shop + redemptions
- Leaderboards, duels, social feed, admin panel, PWA, i18n 8 langs, KYC, referrals, clans

### Phase 7
- Referral double-payout fix, "TBA vs TBA" bug fix
- Wishlist Tracker, Streak "Hot Hand" multiplier, Live Crowd Meter, AI Daily Puzzle, Weekly Report Card
- Full UI/UX redesign: gold/charcoal, Bebas Neue, bottom nav

### Phase 8 — Integrations
- AdMob rewarded ads (20 coins, 5/day)
- Resend Email OTP (HTML template)
- Firebase FCM push
- Razorpay test payments (FREE Bucks), Wallet history page

### Phase Final — Multi-game Launch Ready
- Card Games: Rummy, Teen Patti, Poker, Solitaire (all vs AI, all with daily coin rewards)
- Games tab in bottom nav (replaced Leaderboard)
- Card Game Leaderboard + Daily Streak in /games hub
- IPL Carousel (4-slide hero in Dashboard)
- Quest Engine, Smart Router, Sponsored Pools
- SEO: Blog, structured data, robots.txt, sitemap.xml
- Legal pages: Terms, Privacy, Disclaimer, Responsible Play, Refund Policy, Community Guidelines
- ShareCard viral distribution engine
- LiveActivityTicker, WishlistGoal, Redemption success dialog
- MatchCentre empty state → Card Games promo

### Feb 2026 — PWA Polish + Auth + Play Store
- Android TWA build errors resolved; signed AAB generated
- Firebase Phone Auth added (Login.js + /api/auth/phone-verify)
- FCM fix: send_all → send_each (deployment blocker resolved)
- ScrollToTop component (fixes page scroll on navigation)
- PWA Install button added to Profile page
- Leaderboard admin/seed user filtering
- Hardcoded brand names removed from UI
- **All fake stats removed from entire app:** Landing stats bar, Blog, index.html meta tags
- Play Store listing updated: multi-game focus, no fake numbers, correct IAP info
- In-app purchases correctly declared: FREE Bucks ₹49/₹149/₹499/₹999
- PRD fully audited and synced with codebase (Feb 2026)
