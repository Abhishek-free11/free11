# FREE11 - Sports Fan Community Platform

## Positioning (Non-Negotiable)
**FREE11 is a sports fan community / social entertainment product, NOT a gaming app.**
- App store category: Community + Participation + Consumption
- Language: Avoid win / bet / odds / prize money
- UX: Dream11-familiar for reduced learning curve

## Original Problem Statement
Build a cricket prediction and engagement platform for capturing 60 million displaced RMG users in India. Designed as a "Demand Rail Engine" where users convert skill (cricket predictions) into coins, redeemable for brand-funded real goods.

## Delivery Model (LOCKED)
- **Phase 1 = Beta** — ONE consolidated drop (COMPLETE)
- **Phase 2 = Final MVP** — ONE consolidated drop (polish + stability)
- **MVP 1.5** — Rummy / Poker / Teen Patti (coins only) — May 1, 2026
- No piecemeal releases. No weekly drops.

---

## Phase 1 (Beta) — COMPLETE ✅

### BUILD (New) — All Complete
| Feature | Status |
|---------|--------|
| Fantasy Team Contests (Dream11-style) | ✅ |
| Over Outcome Predictions (0-5, 6-10, 11-15, 16+, Wicket) | ✅ |
| Match Winner Predictions (Team A / Team B) | ✅ |
| Limited Ball-by-Ball (20 per match cap) | ✅ |
| Private Leagues (user-created P2P, no money) | ✅ |
| Age Gate (18+ at registration) | ✅ |
| **Country Restriction (India only)** | ✅ |
| Feature Flags (kill switches) | ✅ |

### Geo-Restrictions
- **Country:** India only (non-India access blocked)
- **States:** All Indian states allowed (no state-level blocking)

### SALVAGE (Refactored) — All Complete
| Component | Status |
|-----------|--------|
| Auth / Onboarding | ✅ |
| Coin Ledger (earn-only) | ✅ |
| Catalog + Redemption | ✅ |
| Orders + Fulfilment | ✅ |
| Admin + Support | ✅ |
| Clans + Leaderboards | ✅ |

### EXPLICITLY OUT OF BETA
- ❌ Cash deposits
- ❌ Cash-out
- ❌ Buy-ins
- ❌ Ads / AdMob (REMOVED)
- ❌ Live player trading
- ❌ Coin gifting

---

## Core Product Thesis
- **Demand Rail Engine**: Cricket prediction is PRIMARY, mini-games are secondary boosters
- **Brand-Funded Model**: All rewards are brand-sponsored with tracked ROAS
- **PRORGA-Safe**: Coins are non-financial (non-purchasable, non-withdrawable, non-transferable)
- **Skill-First**: Rankings based on prediction ACCURACY, not coin balance

---

## Phase 3 Exit Criteria - ALL MET ✅

### A. Voucher Delivery = Auditable Clearing Rail ✅
**Audit Trail Fields:**
- `delivery_attempt_count` - Number of attempts
- `last_delivery_status` - pending/delivered/failed
- `last_failure_reason` - Human-readable error
- `last_failure_code` - Enumerated failure type (PROVIDER_ERROR, TIMEOUT, etc.)
- `delivery_provider_id` - Provider's reference ID
- `delivery_timestamp_utc` - Delivery timestamp
- `delivery_history[]` - Full attempt history

**Features:**
- Idempotency checks prevent duplicate vouchers
- Retry logic with MAX_RETRY_ATTEMPTS = 3
- Manual override flag for admin
- Admin endpoints: `/admin/audit/`, `/admin/retry/`, `/admin/manual-fulfill/`

### B. ROAS Dashboard Optics ✅
- "SANDBOX / TEST DATA" watermark on all dashboards
- ROAS hidden in sandbox mode (shows "N/A")
- "Test Consumption" label instead of "Verified Consumption"
- Environment indicator in all API responses

### C. Attribution Integrity ✅
- ROAS computed only from verified redemptions
- Explicit "Not based on: tasks, views, impressions, engagement, clicks"
- Admin breakdown: ROAS by campaign, ROAS by SKU, ROAS by day

### D. Support Bot – Full Failure-Mode Coverage ✅
- FAQ: "I redeemed but didn't receive my voucher"
- Bot collects redemption_id/order_id
- Admin view: delivery timeline, provider, failure reason, retry option

### E. Transactional Email Notifications ✅
- Email service with Resend provider abstraction
- Voucher delivered/failed/retry notifications
- Email logs stored with status + timestamp
- Transactional only (no marketing)

### F. Infra Hardening ✅
- Load test: 100+ concurrent requests pass
- Failure simulation: Provider health checks
- Idempotency: Double-click prevention
- Admin ops: View + retry failed deliveries

### G. Regulatory Hygiene ✅
- No CPM/CTR/impressions language (except "not based on" context)
- No discount/coupon framing
- PRORGA-safe language maintained

---

## Test Results (Feb 23, 2026)

```
9 passed in 8.42s
✅ TestLoadRedemptions::test_bulk_redemptions
✅ TestLoadRedemptions::test_redemption_rate_limit
✅ TestIdempotency::test_double_click_prevention
✅ TestFailureSimulation::test_provider_health_check
✅ TestFailureSimulation::test_failure_rate_below_threshold
✅ TestAuditTrail::test_audit_endpoint_structure
✅ TestMonitoring::test_system_responds_under_stress
✅ TestSandboxMode::test_sandbox_indicators
✅ TestRegulatoryHygiene::test_no_banned_terms_in_api
```

---

## Architecture

```
/app/
├── backend/
│   ├── server.py                    # Main FastAPI app
│   ├── email_service.py             # NEW: Email notifications
│   ├── fulfillment_routes.py        # UPDATED: Audit trail, idempotency, retry
│   ├── brand_routes.py              # UPDATED: Sandbox mode, ROAS breakdowns
│   ├── support_routes.py            # UPDATED: Voucher FAQ, admin retry
│   ├── clans_routes.py
│   ├── leaderboards_routes.py
│   └── tests/
│       └── test_infra_hardening.py  # NEW: Load + hardening tests
├── frontend/
│   └── src/pages/
│       └── BrandPortal.js           # UPDATED: Sandbox banner, attribution UI
└── docs/
    └── INFRA_HARDENING_RUNBOOK.md   # NEW: Manual runbook
```

---

## Key API Endpoints (NEW/UPDATED)

### Fulfillment Admin
- `GET /api/fulfillment/admin/audit/{id}` - Full audit trail
- `POST /api/fulfillment/admin/retry/{id}?force=true` - Admin retry
- `POST /api/fulfillment/admin/manual-fulfill/{id}` - Manual entry
- `GET /api/fulfillment/admin/failed` - Failed report
- `GET /api/fulfillment/admin/export/csv` - Reconciliation export
- `GET /api/fulfillment/admin/providers/health` - Provider health

### Support Admin
- `GET /api/support/admin/tickets/{id}/delivery-details` - Delivery timeline
- `POST /api/support/admin/tickets/{id}/retry-delivery` - Retry from ticket
- `GET /api/support/admin/voucher-issues` - All voucher tickets

### Brand Dashboard
- `GET /api/brand/dashboard` - Includes sandbox mode, attribution integrity
- `GET /api/brand/analytics` - ROAS by campaign/SKU/day

---

## Environment Variables

### Required for Production
- `FREE11_ENV=production` - Enables ROAS display
- `RESEND_API_KEY` - Email delivery
- `RESEND_FROM_EMAIL` - Sender address

### Optional Monitoring
- `SLACK_WEBHOOK_URL` - Failure alerts
- `ALERT_EMAIL` - Admin notifications

---

## What's MOCKED (Intentional)
- Cricket match data (live scores)
- Voucher provider APIs (Amazon, Swiggy)
- Brand budget deduction

---

## Phase 3 Verification - COMPLETE (Feb 23, 2026)

All verification artifacts generated and documented in `/app/memory/phase3_verification_report.md`:

1. ✅ Load test proof - 9 automated tests passed
2. ✅ Audit trail payload - Full delivery history with failure codes
3. ✅ Failed deliveries admin endpoint - Working with retry button
4. ✅ Provider health status - 24h performance metrics
5. ✅ ROAS dashboard (Sandbox) - Watermark + hidden ROAS + attribution integrity
6. ✅ Support bot flow - "Voucher not received" FAQ + enriched tickets
7. ✅ Email notifications - Resend integration (mock for sandbox)
8. ✅ Regulatory hygiene - No CPM/CTR language verified

**UI Screenshots captured:**
- Brand Portal with SANDBOX banner
- ROAS "N/A - Hidden in sandbox"
- Attribution integrity notes

---

## Pre-Beta UX Polish - COMPLETE (Feb 23, 2026)

### 1. First-Time Tutorial (60 seconds, 4 screens)
**Component:** `/app/frontend/src/components/FirstTimeTutorial.js`
- Screen 1: "Predict cricket. That's how you earn coins."
- Screen 2: "Coins unlock real products. No cash. No betting."
- Screen 3: "Redeem vouchers instantly for real products."
- Screen 4: "Skill drives rewards. Boosters just help you earn faster."
- **Server-side persistence** (not localStorage) via `/api/user/tutorial-status`
- **Replay option** in Profile → Help

### 2. Empty States
**Component:** `/app/frontend/src/components/EmptyState.js`
- Dashboard: "Make your first prediction to start unlocking real products."
- My Vouchers: "Redeemed vouchers will appear here once you unlock your first reward."
- Transactions: "Your coin history will show up once you start earning."
- Predictions: "No predictions yet. Start predicting to build your streak!"

### 3. Microcopy Polish (5 key spots)
- Dashboard CTA: "Start Predicting" (was "Predict Now")
- Predict helper: "Earn 5-15 coins per correct prediction" (green text)
- Boosters: "Boosters help you earn faster. Skill drives your rewards."
- Wallet disclaimer: Warm, human tone in Profile section
- Registration: Clear invite code validation with visual feedback

### 4. Progress to Next Reward - Enhanced
- Larger progress bar (h-4 instead of h-2)
- Milestone markers at 25%, 50%, 75%
- "Ready!" badge when progress >= 100%
- Prominent coins balance display
- Green border highlight on card

### 5. Beta Registration with Invite Code
- Invite code field with real-time validation
- Green checkmark for valid codes
- "(Required for beta)" label
- Button disabled until valid invite provided

---

## Phase 4: Closed Beta + Hardening (IN PROGRESS)

### Phase 4 Implemented Features (Feb 23, 2026)

#### P0 Features (Complete)

**1. Go Live Script (`/app/scripts/go_live.py`)**
- `--dry-run` mode to preview changes
- `--confirm-production` flag required for go-live
- `--rollback` to revert to sandbox
- `--status` to check current state
- Secondary confirmation for live vouchers and email
- Full logging to `/app/logs/go_live.log`
- Backup/restore of .env file

**2. Beta Invite System (`/api/beta/*`)**
- Invite code generation: `FREE11-XXXXXXXX` format
- Default cap: 200 invites
- Invite source tracking
- Revoke/pause functionality
- Expiration support
- Single-use and multi-use codes
- Registration now requires valid invite code

**3. Weekly Beta Report (`/api/admin/reports/beta-report`)**
- DAU/WAU tracking
- Total redemptions + period redemptions
- Voucher failure rate
- Avg delivery time (minutes)
- Top support issues
- Brand-funded redemptions
- Invite usage stats
- Funnel metrics: Predict → Earn → Redeem → Receive

#### P1 Features (Planned)
- Slack alerts (webhook configurable via `SLACK_WEBHOOK_URL` env var)
- Email fallback for critical alerts
- UX funnel event tracking

### New API Endpoints

```
# Beta Invite System
POST /api/beta/admin/invites/generate
GET  /api/beta/admin/invites
POST /api/beta/admin/invites/{code}/revoke
POST /api/beta/admin/invites/pause
POST /api/beta/admin/invites/resume
GET  /api/beta/admin/settings
PUT  /api/beta/admin/settings
POST /api/beta/validate-invite
GET  /api/beta/status

# Reports
GET  /api/admin/reports/beta-report
GET  /api/admin/reports/beta-summary
GET  /api/admin/reports/funnel-metrics
```

### New Files

```
/app/scripts/go_live.py          # Production deployment script
/app/backend/beta_routes.py      # Beta invite system
/app/backend/reports_routes.py   # Weekly reporting
/app/backend/alerting_service.py # Slack + email alerts
/app/logs/go_live.log           # Deployment logs
```

### Environment Variables

```
# Production controls (in .env)
FREE11_ENV=sandbox              # sandbox | production
ENABLE_LIVE_VOUCHERS=false      # Enable real voucher providers
ENABLE_LIVE_EMAIL=false         # Enable Resend API

# Optional (for production)
SLACK_WEBHOOK_URL=              # Slack alerts
ALERT_EMAIL=                    # Email fallback
RESEND_API_KEY=                 # Email provider
```

---

## Phase 4 Guardrails (Non-Negotiable)

DO NOT introduce:
- Coin cash-out
- P2P transfers
- Pooling
- Discount/coupon framing
- CPM/CTR language

DO NOT:
- Optimize for growth hacks
- Add new features outside beta hardening
- Change core loops (Skill → Demand → Clearing → Attribution)

---

## Light Emotional Design / Delight Touches - COMPLETE (Feb 23, 2026)

### 1. Correct Prediction Celebration (Cricket.js)
**Location:** `/app/frontend/src/pages/Cricket.js` (lines 100-145)

**Implementation:**
- ✅ Confetti burst (80 particles, team colors: green/yellow/blue)
- ✅ Celebration sound via `playCorrectPredictionSound()` (respects user preference)
- ✅ First correct prediction: "Nice call! 🎯" + "Nice start. +X coins!"
- ✅ Subsequent predictions: Random celebration messages from pool:
  - "Nice call! 🎯" / "Your prediction was spot on!"
  - "Well played! 🏏" / "You read that one perfectly!"
  - "Sharp eye! 👁️" / "Great prediction!"
  - "Nailed it! ✨" / "Your cricket instincts are on point!"

### 2. Voucher Delivery Delight Moment (Shop.js)
**Location:** `/app/frontend/src/pages/Shop.js` (lines 77-120, 359-415)

**Implementation:**
- ✅ Success dialog with headline: **"Unlocked! Your reward is ready 🎉"**
- ✅ Skill acknowledgment: **"You earned this through skill. Enjoy!"** (green text)
- ✅ Confetti burst (100 particles, celebratory colors)
- ✅ `playCelebrationSound()` (respects user preference)
- ✅ Animated Gift icon with bounce animation
- ✅ Sparkles icon with pulse animation
- ✅ Product info card with redeemed product image/name/brand
- ✅ "Delivery in progress" badge
- ✅ "Continue Shopping" CTA button
- ✅ Gradient background with green accent
- ✅ All elements have proper `data-testid` attributes for testing

**Test Report:** `/app/test_reports/iteration_6.json`
- 100% frontend success rate
- All delight elements verified working

---

## Ready for Closed Beta Sign-off

**Pre-Beta Checklist:**
- [x] Tutorial system working (server-side persistence)
- [x] Empty states with friendly copy
- [x] Progress visualization enhanced
- [x] Invite code registration flow
- [x] Prediction celebration (confetti + sound + toast)
- [x] Voucher delivery delight (success dialog + animations)

**Next Steps:**
1. User sign-off on delight screenshots
2. Open Closed Beta (50-200 users)
3. Phase 4 monitoring & hardening
4. Onboard pilot brand campaign

---

## CLOSED BETA LAUNCHED - Feb 23, 2026

### Beta Launch Status
- **Status:** OPEN
- **Invite Cap:** 200 users
- **Invites Generated:** 58 (50 for wave 1)
- **Invites Used:** 3
- **Beta Users Onboarded:** 0 (awaiting distribution)

### Initial Invite Codes (Wave 1 - 10 samples)
```
FREE11-Z2QL1GSR
FREE11-T294PKU7
FREE11-ODTMFJWI
FREE11-XCLUXQL4
FREE11-XYWMDFMW
FREE11-3ASRK8OY
FREE11-B2QAM9WP
FREE11-6CLYSTE6
FREE11-SBS6D8MS
FREE11-1JXY32U6
```
*Source: beta_launch_wave1 | Expires: 30 days*

### Pilot Brand Onboarded
- **Brand:** Swiggy
- **Email:** pilot@swiggy.in / pilot123
- **Campaign:** IPL 2026 Beta Trial
- **Budget:** ₹25,000 allocated
- **Product:** Swiggy ₹100 Voucher (200 coins)
- **Status:** Active, Verified

### Guardrails Implemented
1. ✅ Confetti/sound trigger only once per redemption (inside API success handler)
2. ✅ Celebration sound default OFF (opt-in via Profile → Settings)
3. ✅ First-correct-prediction tracked via user.correct_predictions (persisted)

### Monitoring Checklist (48-72 hours)
- [x] Track user registrations via invite codes
- [ ] Monitor redemption flow completion
- [ ] Identify support ticket patterns
- [ ] Capture first beta report
- [ ] Document top 3 friction points

---

## Admin Beta Dashboard - FIXED (Feb 24, 2026)

### Issue Fixed
The Admin Beta Dashboard (`/admin`) was displaying all metrics as zero despite having real user data.

**Root Cause:** The frontend `api.js` utility was missing a generic `get()` method. The `Admin.js` component was calling `api.get('/admin/beta-metrics')` but this method didn't exist.

**Fix Applied:** Added generic `get()` and `post()` methods to `/app/frontend/src/utils/api.js`:
```javascript
get: (endpoint) => axios.get(`${API}${endpoint}`, { headers: getAuthHeader() }),
post: (endpoint, data) => axios.post(`${API}${endpoint}`, data, { headers: getAuthHeader() }),
```

### Current Beta Metrics (as of Feb 24, 2026)
- **Beta Users:** 5
- **Invites Used:** 4
- **Predictions:** 0
- **Redemptions:** 4 (40% adoption)
- **Coins in Circulation:** 15,400
- **Loop Completion:** 0% (no users completed Predict → Redeem)
- **Beta Health Status:** "Needs Work"

### Invite Codes Status
- **Generated:** 50 (Wave 1 - simple format: BETA01-BETA50)
- **Used:** 4
- **Available:** 46

---

*Last updated: Feb 24, 2026*
*Phase 3 Exit: APPROVED*
*Phase 4: IN PROGRESS*
*Pre-Beta UX: COMPLETE*
*CLOSED BETA: LAUNCHED*
*Admin Dashboard: WORKING*
*Card Games: IMPLEMENTED*

---

## MVP 1.5: Card Games - IMPLEMENTED (Feb 24, 2026)

### Scope
Card Games (Rummy, Teen Patti, Poker) added to Phase 1 Beta with the FREE11 coin model:
- **Multiplayer room-based play** (real-time with other users)
- **Simplified/casual rule-sets** for beta
- **WebSocket-based real-time communication**
- **Same coin wallet, catalog, redemption, fulfilment**

### Game Types & Rewards
| Game | Win | 2nd | Participate | Min Players | Max Players |
|------|-----|-----|-------------|-------------|-------------|
| Rummy | 50 coins | 20 coins | 5 coins | 2 | 6 |
| Teen Patti | 40 coins | 15 coins | 5 coins | 3 | 6 |
| Poker | 60 coins | 25 coins | 5 coins | 2 | 9 |

### Architecture
```
/app/backend/
├── card_game_logic.py     # Card game state machines (Rummy, Teen Patti, Poker)
├── websocket_manager.py   # WebSocket session management
└── games_routes.py        # REST + WebSocket endpoints
```

### Key Features
1. **Room Management**: Create public/private rooms, join by code, quick play
2. **Real-time Communication**: WebSocket at `/api/games/ws/{room_id}`
3. **Game State**: Full game logic for each card game type
4. **Rewards**: Automatic coin distribution on game completion
5. **Stats Tracking**: Games played, won, win rate, total coins earned
6. **Leaderboards**: Per-game type leaderboards by win rate
7. **Invite Friends**: Share button with native share API + clipboard fallback, direct join via `?join=CODE` URL parameter

### API Endpoints
- `GET /api/games/config` - Game configuration and rewards
- `GET /api/games/{type}/info` - Detailed game info with hand rankings
- `POST /api/games/{type}/rooms/create` - Create public/private room
- `POST /api/games/{type}/quick-play` - Auto-join or create room
- `GET /api/games/{type}/rooms` - Available public rooms
- `POST /api/games/rooms/join-by-code` - Join private room
- `GET /api/games/my-rooms` - User's active rooms
- `GET /api/games/{type}/stats/my` - User's game stats
- `GET /api/games/{type}/leaderboard` - Game leaderboard
- `WS /api/games/ws/{room_id}` - WebSocket for real-time gameplay

### Frontend Pages
- `/games` - Card Games Hub (CardGames.js)
- `/games/{type}/room/{roomId}` - Game Room (GameRoom.js)

### Test Results
```
Backend: 24/24 tests PASSED (100%)
Frontend: All UI features working
WebSocket: Connection established successfully
```

### Explicitly NOT Included
- ❌ AI/single-player mode
- ❌ Cash buy-ins
- ❌ Real-money wagering
- ❌ Coin transfers between players

