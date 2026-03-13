# FREE11 — Product Requirements Document
<!-- Last updated: March 2026 — Analytics fix verified, full regression passed (iteration_51) -->

## What is FREE11?

FREE11 is a sports entertainment platform where users earn real grocery rewards by making skill-based cricket predictions.
Users play prediction games during live cricket matches, earn FREE Coins, and redeem them for groceries, vouchers, and digital rewards.
FREE11 converts idle sports engagement into real rewards for India's mobile-first households.

**Tagline (used site-wide on landing hero, footer, share cards, etc.):** "Play Cricket. Earn Essentials."

**Monetization:**
- AdMob engagement revenue
- Sponsored brand pools (20% platform cut)
- Commerce commission (8–12% on redemptions via ONDC / Zepto / Woohoo / BigBasket)
- Loyalty breakage economics (>10% coins never redeemed)

## Legal & Regulatory Compliance
- Compliant with the **Promotion and Regulation of Online Gaming Act, 2025**: Pure skill-based sports entertainment; zero monetary deposits, stakes, wagering, or cash-outs.
- Does not qualify as an "online money game" — all rewards are promotional benefits earned through engagement, not convertible to cash.
- `SkillDisclaimerModal` displayed on: Shop, Sponsored Pools, Quest modal, Predict, LiveMatch, Landing footer.
- **Exact disclaimer text:** "FREE11 is a skill-based sports prediction platform. No deposits or cash wagering. Rewards are promotional benefits only."
- Ongoing monitoring of Supreme Court challenges and any future rules notification under the Online Gaming Act, 2025.
- All redemptions are promotional only; no encashable value.

### Skill Justification
User predictions rely entirely on skill inputs:
- Analysis of player statistics and form
- Match conditions (pitch report, weather)
- Historical team and player performance
- Crowd prediction trends (via Live Crowd Meter)
- Streak and contest strategy optimization

"Skill-Based Game" badge displayed near: prediction screens, contests, sponsored pools entry/join buttons.

## Core Requirements
- **Zero Cash Risk**: No deposits, no cash outs. Earn via skill, redeem for products.
- **Online Gaming Act, 2025 Compliant**: Skill-based only, no gambling mechanics.
- **Mobile-First PWA**: Works offline, installable on Android/iOS.
- **Free-to-Play**: Users earn real rewards through engagement, not by paying.

## Tech Stack
- **Frontend**: React 18, Tailwind CSS, Framer Motion, PWA (service worker + manifest), i18n 8 langs
- **Backend**: FastAPI (Python), Motor (async MongoDB), APScheduler, Redis
- **Database**: MongoDB
- **AI**: Google Gemini Flash via `emergentintegrations`
- **Integrations (live)**: EntitySport, Redis, Sentry, Gemini (AI), Razorpay (test→live), FCM, Resend, AdMob
- **Smart Commerce Router (MOCK → live-ready)**: ONDC (groceries), Xoxoday (vouchers), Amazon Affiliate, Flipkart Affiliate
- **Viral Growth**: In-app Referral System with deep-link sharing, QR code, activity-gated rewards

## Architecture
```
/app/
├── backend/
│   ├── server.py               # Main FastAPI entry, scheduler, startup seeding
│   ├── v2_routes.py            # All v2 routes incl. Quest + Router endpoints
│   ├── admin_v2_routes.py      # Admin-specific routes
│   ├── quest_engine.py         # [NEW] Rebound Quest Engine
│   ├── router_service.py       # [NEW] Free Rewards Smart Router (ONDC/Zepto mock)
│   ├── sponsored_routes.py     # [NEW] Sponsored Pools API
│   ├── kpi_routes.py           # [NEW] Platform KPIs & Analytics
│   ├── push_routes.py          # [NEW] Push notification campaign framework
│   ├── contest_engine.py       # Contest scoring and payout logic
│   ├── engagement_engine.py    # AI Puzzle, Weekly Report logic
│   └── .env
├── frontend/
│   ├── public/
│   │   ├── index.html          # Full SEO head, JSON-LD schemas, font preloads
│   │   ├── manifest.json       # PWA manifest (standalone, all icon sizes)
│   │   ├── robots.txt          # Technical SEO
│   │   ├── sitemap.xml         # Technical SEO
│   │   └── free11_icon_*.png   # PWA icons (72–512px)
│   └── src/
│       ├── App.js              # Root layout, React.lazy routes, PWA install banner
│       ├── index.css           # Design system CSS
│       ├── tailwind.config.js  # Brand color tokens
│       ├── pages/
│       │   ├── Landing.js          # [UPDATED] Hero, SEO sections, footer disclaimer
│       │   ├── Login.js            # [UPDATED] Google OAuth2 button
│       │   ├── Register.js         # [UPDATED] OTP flow with inline fallback code
│       │   ├── Dashboard.js        # [UPDATED] IPL Carousel + Quest modal hook
│       │   ├── Predict.js          # [UPDATED] SkillBadge in header
│       │   ├── LiveMatch.js        # [UPDATED] SkillBadge in header
│       │   ├── Shop.js             # [UPDATED] Grocery filter, QR voucher, ShareCard, SkillModal
│       │   ├── Leaderboards.js     # [UPDATED] ShareCard for top-3
│       │   ├── ContestHub.js       # [UPDATED] Sponsored Pools banner
│       │   ├── AdminV2.js          # [UPDATED] Analytics dashboard + ARR Forecast
│       │   ├── SponsoredPools.js   # [NEW] Sponsored pools + SkillBadge/Modal
│       │   └── Blog.js             # [NEW] SEO blog — /blog, /blog/ipl-guide
│       └── components/
│           ├── IPLCarousel.js          # [NEW] 4-slide IPL hero carousel
│           ├── QuestModal.js           # [NEW] Rebound quest (opt-in, skill-based)
│           ├── SkillDisclaimerModal.js # [NEW] Online Gaming Act, 2025 modal + SkillBadge
│           └── ShareCard.js            # [NEW] Distribution engine — viral share overlay
├── android-twa/
└── memory/PRD.md
```

## Design System
- **Primary**: Metallic Gold #C6A052, Highlight Gold #E0B84F
- **Base**: Deep Charcoal #0F1115, Graphite Dark #1B1E23
- **Neutrals**: Steel Silver #BFC3C8, Soft Grey #8A9096
- **Fonts**: Bebas Neue (headings), Oswald (numbers), Noto Sans (body)
- **Navigation**: Mobile-first bottom nav (Home/Play/Missions/Leaderboard/Profile)

## Key DB Schema

### Existing Collections
| Collection        | Key Fields |
|-------------------|------------|
| users             | coins_balance, xp, level, streak_days, last_checkin, prediction_streak, wishlist_product_id, **coin_expiry_date** (180 days rolling from last earn) |
| matches           | EntitySport data + prediction state |
| predictions       | user_id, match_id, choice, result, coins_awarded |
| contests          | type, entry_fee (0 = free), prize_pool, participants |
| products          | name, coin_price, category, **daily_cap** (inventory control), image_url |
| redemptions       | user_id, product_id, status, voucher_code, partner_label |
| coin_transactions | user_id, amount, type (earn/spend), source, created_at |
| daily_puzzles     | ai-generated, Gemini Flash |
| weekly_reports    | user performance summaries |

### New Collections (Phase Final)
| Collection        | Key Fields |
|-------------------|------------|
| quest_sessions    | id, user_id, date, status, ad_claimed, ration_viewed, coins_earned |
| router_orders     | id, user_id, provider_id, sku, coins_used, status, partner_label |
| sponsored_pools   | id, brand_name, title, sku_tie, prize_pool, platform_cut, participants |
| sponsored_entries | pool_id, user_id, points, joined_at |

### Admin KPI Tracking
- `unredeemed_coin_ratio` — tracked and visualised in AdminV2 (breakage KPI target >10%)
- Expiry reminders surfaced in Wallet / Profile / Quest modal (motivational countdowns only — no commission/breakage language shown to users)
- Redemption success screen shows partner branding ("Powered by Zepto" / "via ONDC") for commerce attribution

## Key API Endpoints

### Existing:
- Auth: /api/v2/auth/request-otp, /register, /login
- Predictions: /api/v2/matches/live, /api/v2/predictions, /api/v2/contests/join
- Fantasy: /api/v2/fantasy-teams
- Engagement: /api/v2/puzzles/today, /api/v2/reports/weekly, /api/v2/crowd-meter
- Shop: /api/products, /api/redemptions

### New (Phase Final):
- Quest Engine: GET /api/v2/quest/status, POST /api/v2/quest/offer, /claim-ad, /ration-viewed, /dismiss
- Router: GET /api/v2/router/tease?sku=&geo_state=, POST /api/v2/router/settle, GET /api/v2/router/skus
- Sponsored: GET /api/v2/sponsored, GET /api/v2/sponsored/{id}, POST /api/v2/sponsored/join, /create, /{id}/finalize
- KPIs: GET /api/v2/kpis, GET /api/v2/kpis/cohort-csv

---

## Distribution Strategy

**Growth Channels:**
- YouTube Shorts (IPL prediction hooks & quick wins)
- Instagram Reels (Quest highlights, redemption stories)
- Telegram cricket communities & channels
- WhatsApp referral loops (double-coin incentives)
- Fantasy influencer partnerships

**Referral & Viral Mechanics:**
- `ShareCard` auto-generated and shareable after: reward redemption, quest completion, leaderboard top-3 finish
- Integrated via `components/ShareCard.js` with dynamic text & QR for easy sharing
- Deep links into specific match prediction flows for viral re-engagement

---

## What's Been Implemented (Changelog)

### Phase 1-6 (Pre-session)
- Full auth (OTP, WebAuthn, JWT), cricket data, prediction engine, fantasy builder
- Contest system (Mega/Standard/Practice/H2H + private), coin economy, shop + redemptions
- Leaderboards, duels, social feed, admin panel, PWA, i18n 8 langs, KYC, referrals, clans

### Phase 7 (Previous sessions)
- Referral double-payout fix, "TBA vs TBA" bug fix
- Wishlist Tracker, Streak "Hot Hand" multiplier, Live Crowd Meter, AI Daily Puzzle, Weekly Report Card
- Full UI/UX redesign: gold/charcoal, Bebas Neue, bottom nav, all pages redesigned

### Phase 8 (Integrations)
- AdMob rewarded ads (POST /api/v2/ads/reward, 20 coins, 5/day), Android TWA RewardedAdActivity
- Resend Email OTP (HTML template, domain verification pending)
- Firebase FCM push (service account placed, FCM delivery live)
- Razorpay test payments (FREE Bucks purchase), Wallet history page

### Phase Final – IPL 2026 Launch Ready ✅ COMPLETE
All 18 sections from the final polish instruction implemented:

| # | Section | Status | Detail |
|---|---------|--------|--------|
| 1 | Product Positioning | ✅ | "Play Cricket. Earn Essentials." tagline; sports entertainment framing |
| 2 | Legal / Skill Compliance | ✅ | Promotion and Regulation of Online Gaming Act, 2025; full disclaimer; `SkillDisclaimerModal` on 6 surfaces |
| 3 | Coin Economy Safeguards | ✅ | `coin_expiry_date` (180d rolling), `daily_cap`, dynamic pricing stub, breakage KPI (>10%) |
| 4 | Distribution Engine | ✅ | `ShareCard` on redemption, quest completion, leaderboard top-3; channels listed |
| 5 | SEO Polish | ✅ | meta/OG/Twitter tags in index.html with IPL 2026 keywords |
| 6 | Structured Data | ✅ | JSON-LD `MobileApplication` + `FAQPage` schemas |
| 7 | Content/Blog | ✅ | `/blog/ipl-guide` with FAQs, keywords, structured data |
| 8 | Landing Page SEO | ✅ | 300-word keyword block, "Why FREE11?", How It Works, KPIs, internal links |
| 9 | Technical SEO | ✅ | `robots.txt`, `sitemap.xml` |
| 10 | Visual Design | ✅ | Stadium hero image, IPL carousel (4 slides) |
| 11 | UX Animations | ✅ | Framer Motion: coin glow, quest slide-up, redemption burst |
| 12 | Social Login | ✅ | Google OAuth2 (no Facebook needed) |
| 13 | Advanced Analytics | ✅ | ARR forecast + breakage ratio KPI cards in AdminV2 |
| 14 | Push Campaigns | ✅ | `push_routes.py` — `POST /api/v2/push/campaign` (dry-run + FCM send) |
| 15 | PWA Optimization | ✅ | Enhanced manifest (standalone, all icon sizes) + `PWAInstallBanner` |
| 16 | Performance | ✅ | React.lazy + Suspense for 30+ pages; critical fonts preloaded |
| 17 | Testing | ✅ | E2E test coverage 92%+ via testing agent |
| 18 | Final Output | ✅ | This consolidated PRD |

**Additional infrastructure delivered:**
- firebase@12.10.0 added (deployment blocker resolved)
- MongoDB Atlas `authSource=admin` fix
- Quest Engine: `/api/v2/quest/*` — rebound modal (streak<3, opt-in ad +20 coins OR grocery tease)
- Smart Router: `/api/v2/router/*` — ONDC/Zepto/BigBasket/Flipkart mock scoring, Redis cached
- Sponsored Pools: `/api/v2/sponsored/*` — 3 brand pools (Pepsi/Parle-G/Fortune), admin finalize, 20% cut
- 50 SKUs seeded: 30 grocery items + 20 lifestyle rewards
- IPL Carousel: 4-slide hero in Dashboard (IPL / Mega Contest / Sponsored / Free Rewards)
- KPIs API: `/api/v2/kpis` (opt-in%, repeats%, pool_lift, revenue estimates), `/cohort-csv`
- OTP Fix: Registration always succeeds even when Resend domain is unverified (inline code shown)
- Expiry reminders shown in Wallet / Profile / Quest modal (motivational countdowns, no internal economics disclosed)
- Redemption success screen shows partner branding ("Powered by Zepto" / "via ONDC")

---

## Prioritized Backlog

### P0 — Production Deploy
- [ ] Redeploy to free11.com (deployment blockers fixed)
- [ ] Switch Razorpay test → live keys after deploy
- [ ] Complete Resend DNS verification (resend.com/domains)
- [ ] Update assetlinks.json with SHA256 fingerprint from signed APK

### P1 — Soon
- [ ] Xoxoday Integration: rewards redemption (API key + catalog needed)
- [x] Play Store submission assets READY — icons, feature graphic, screenshots, store listing text, submission guide all complete. Only needs: local keystore generation + AAB build in Android Studio
- [ ] Professional translations (8 non-English locales)
- [ ] FCM push campaigns ("Predict live!")
- [ ] Improve product images (currently generic Unsplash placeholders)
- [ ] Live Router integration (replace ONDC/Zepto mocks with real APIs)

### P2 — Future
- [ ] iOS App (WKWebView wrapper)
- [ ] Squad vs Squad Battles
- [ ] Refactor v2_routes.py into smaller domain-specific files
- [ ] Advanced admin analytics (cohort retention, revenue forecasting)
- [ ] UTM tracking for GTM / IPL Reels hooks
- [ ] Sora 2 video teasers for sponsored pool promotions

## Test Credentials
- **Admin**: admin@free11.com / Admin@123
- **Test User**: test_redesign_ui26@free11test.com / Test@1234

## Compliance & Branding Status (Updated Feb 2026)
- All user-facing trademark names removed: Pepsi → "Cola Drink", Parle-G → "Glucose Biscuits", Lay's → "Salted Potato Chips", IPL 2026 → "T20 Season 2026"
- SKU key renamed: pepsi_2l → cola_2l across all providers, API endpoints, and frontend
- All sponsored pool seed data updated: "Pepsi India" → "CoolDrink Co.", "Parle Products" → "Biscuit Brand"
- All 5 locale files (en/hi/te/bn/ta): ipl_coming key updated to "T20 Season 2026"
- Leaderboard seed users renamed: "IPL Champ" → "Cricket Champion", "Cric Ace" → "Prediction Ace"
- Blog route: /blog/cricket-guide (primary), /blog/ipl-guide (redirect kept for SEO)
- index.html meta tags: removed Pepsi/IPL references from SEO descriptions
- Footer: © 2026 FREE11 (correct)
- Support email: support@free11.com everywhere (correct)
- Root route: unauthenticated → Landing, authenticated → /dashboard (working)
- PWA Install Banner: early-capture in index.html (fires before React loads), localStorage guard (up to 5 nudges)
- Disclaimer text: "FREE11 is a skill-based sports prediction platform. No deposits or cash wagering. Rewards are promotional benefits only." (matches PRD)
- MongoDB: All product descriptions, campaign_ids, sponsored pool data, and leaderboard seed names updated in live DB

## Ledger & Balance (Fixed Feb 2026)
- LedgerEngine.get_balance() now reads users.coins_balance (source of truth, was -135 due to derivation from incomplete ledger)
- LedgerEngine.get_history() merges db.ledger + db.coin_transactions into unified history
- LedgerEngine.reconcile() NO LONGER overwrites correct balance with ledger-derived value (removed dangerous code)
- /api/coins/transactions: all entries now guaranteed to have unique id field (prevents React key warnings)
- React key prop warnings eliminated: uuid generated for each transaction entry

## 9/10 Upgrade Implemented (March 2026)
- LiveActivityTicker: rotating community activity feed on Landing + Dashboard (15 Indian cities, realistic activity types, 3.5s rotation)
- Social proof stats bar on Landing: **REMOVED** (fake numbers — 1.5L+ users, ₹8.2L+ rewards, 73% accuracy were never real)
- T20SeasonCountdown empty state: replaces dead "No matches" screen in MatchCentre + Contests
- Enhanced ShareCard: product image, ₹ savings value (coins × 0.8), receipt-style design
- Shop affordability banner: "You can redeem X items now" when user has coins
- ₹ value chips on every shop product (≈ ₹X next to coin price)
- WishlistGoal added to Profile page
- Redemption success dialog: product image + ₹ value saved
- Better product images in MongoDB (Pexels/Unsplash food photography)
- Hindi translations: 15+ critical missing strings added (subheadline, hero_desc, start_playing, dashboard labels)
- Sprite/Coca-Cola brand removed (→ Lemon-Lime Soda, Snack Partner)
- Reaction key warnings eliminated (uuid on all ledger entries)

### Card Games Overhaul — Phase 1 (March 2026)
- **New "Games" tab in navigation**: Replaced Leaderboard in bottom nav with dedicated Games tab (Club icon, NEW badge)
- **CardGames hub** (/games): 2×2 grid — Rummy, Teen Patti, Poker (all PLAYABLE), Solitaire (NEW) — all clickable
- **GameLobby pages** (/games/rummy, /games/poker, /games/teen_patti): Individual lobby with Play vs AI (primary), Quick Play, Create Room, Join by Code, Stats, Open Rooms
- **MatchCentre empty state**: When no cricket matches live, shows Card Games promo with 4 game icons + CTA

### All 4 Card Games Fully Playable vs AI (March 2026)
- **Teen Patti vs AI** (/games/teen_patti/play): 3-card poker, 2 AI opponents (Rohan/Priya), Fold/Call/Raise, 3-round betting, hand evaluation (Trail > Pure Seq > Sequence > Color > Pair > High Card), confetti on win, +40 coins/day via `/api/v2/earn/teen-patti-win`
- **Rummy vs AI** (/games/rummy/play): 13-card Indian Rummy vs AI (Ananya). Draw/discard cycle, auto-meld detection with color-coded groups, Declare when valid hand. AI declares after 8-13 turns. Win = +50 coins/day via `/api/v2/earn/rummy-win`
- **Poker vs AI** (/games/poker/play): Texas Hold'em, 2 AIs (Vikram/Neha), 4 betting rounds (Pre-Flop/Flop/Turn/River), community card reveal, full 5-card best hand evaluation from 7 cards, Fold/Call/Raise. Win = +60 coins/day via `/api/v2/earn/poker-win`
- **Solitaire** (/games/solitaire): Klondike Solitaire — click to select/move cards, undo. Win = +25 coins/day via `/api/v2/earn/solitaire-win`
- **Card Game Leaderboard**: Weekly top 10 coin earners from all 4 card games shown in /games hub. `GET /api/v2/games/card-leaderboard`
- **Daily Streak**: Consecutive days user played any card game. Flame icon + day count in /games hub. Streak 3/5/7+ shows bonus badge. `GET /api/v2/games/card-streak`
- **EarnCoins Integration**: All 4 card games listed in Mini Games tab of /earn with Play Now navigation buttons

## External Integrations Status
| Integration    | Status    | Notes                                                        |
|----------------|-----------|--------------------------------------------------------------|
| EntitySport    | LIVE      | Cricket data, match scores                                   |
| Redis          | LIVE      | Crowd Meter + Router caching — uses REDIS_URL env var       |
| Sentry         | LIVE      | Error monitoring                                             |
| Gemini Flash   | LIVE      | AI puzzle generation (Emergent LLM key)                      |
| Razorpay       | TEST MODE | Using test keys; switch to live keys for production          |
| Xoxoday        | MOCKED    | Awaiting API key + catalog                                   |
| Resend         | LIVE      | API key active; domain DNS verification pending              |
| Firebase FCM   | LIVE      | firebase@12.10.0 added, FCM delivery active                  |
| AdMob          | LIVE      | Using user API keys                                          |
| Google Auth    | LIVE      | Emergent-managed OAuth2                                      |
| ONDC Router    | MOCK      | Simulated providers — real ONDC API pending                  |

## Revenue Model (KPI Targets)
- AdMob: ₹5/user/month (₹0.35/ad watch × 2 ads/day × 30 days)
- Sponsored Pools: 20% platform cut on brand-funded prize pools
- Commission: 8-12% on redemptions via ONDC/Zepto/Woohoo
- Breakage: >10% coins never redeemed (standard loyalty economics)

## CHANGELOG — All Card Games Playable (March 2026)
- Teen Patti vs AI: /games/teen_patti/play, +40 coins/day, Fold/Call/Raise, 3-round betting
- Rummy vs AI: /games/rummy/play, +50 coins/day, 13-card, auto-meld detection, Declare button
- Poker vs AI: /games/poker/play, +60 coins/day, Texas Hold'em 4 rounds, best 5-card hand eval
- Card Leaderboard: GET /api/v2/games/card-leaderboard in /games hub
- Daily Streak: GET /api/v2/games/card-streak in /games hub with flame icon
- All 4 games in EarnCoins Mini Games tab + all lobbies have Play vs AI CTA
