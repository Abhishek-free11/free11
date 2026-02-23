# FREE11 - Cricket Prediction & Demand Rail Platform

## Original Problem Statement
Build a cricket prediction and engagement platform for capturing 60 million displaced RMG users in India. Designed as a "Demand Rail Engine" where users convert skill (cricket predictions) into coins, redeemable for brand-funded real goods.

## Core Product Thesis
- **Demand Rail Engine**: Not a generic rewards app - cricket prediction is the PRIMARY feature
- **Brand-Funded Model**: All rewards are brand-sponsored with tracked ROAS
- **PRORGA-Safe**: Coins are non-financial (non-purchasable, non-withdrawable, non-transferable)
- **Skill-First**: Rankings, leaderboards, and progression based on prediction ACCURACY, not coin balance

## What's Been Implemented

### Phase 1: Core Foundation (COMPLETE)
- [x] User authentication (JWT-based)
- [x] User progression system (levels, XP, streaks, badges)
- [x] Cricket prediction interface (ball-by-ball, mocked data)
- [x] Shop with brand-funded products
- [x] Basic redemption flow
- [x] FAQ page explaining coin policy

### Phase 2: Social & Competition (COMPLETE)
- [x] Clans system (create, join, browse)
- [x] Clan leaderboard
- [x] Global skill-based leaderboard
- [x] Streaks leaderboard
- [x] Prediction duels

### Phase 3: Automation & Brand Tools (COMPLETE - VERIFIED Feb 23, 2026)
- [x] Voucher fulfillment pipeline (pluggable providers)
- [x] Support chatbot (deterministic, FAQ-driven)
- [x] Support tickets system
- [x] My Vouchers tracking (pending → delivered status)
- [x] Brand Portal (separate authentication)
  - [x] Campaign creation
  - [x] Product management (SKU upload)
  - [x] ROAS Dashboard
  - [x] Analytics with time filters

## Verification Artifacts Captured (Feb 23, 2026)

### Screenshots Delivered:
1. **User Dashboard** - Shows profile, coins (500), level, progression
2. **Shop Page** - Brand-funded products with "Redeem Now" buttons
3. **Redemption Dialog** - Balance breakdown, delivery address input
4. **My Vouchers** - Shows pending/delivered status with voucher codes
5. **Support Chat** - Bot interaction with order status lookup
6. **My Tickets** - Existing ticket with order ID reference
7. **Create Ticket Dialog** - Subject, category, description fields
8. **Clans Page** - Browse, create, join clans
9. **Leaderboards** - Skill-based with accuracy metrics (NOT coins)
10. **Predict Page** - Ball-by-ball prediction interface
11. **Brand Portal Login** - Partner dashboard entry
12. **Brand Dashboard** - ROAS metrics (₹5,250 consumption, 30 redemptions)
13. **Brand Campaigns** - IPL 2026 Campaign (₹6,000 delivered, 25 consumers)
14. **Brand Products** - SKUs with redeemed counts
15. **Brand Analytics** - Top performing products, consumer segments

### ROAS Payload Sample Provided:
```json
{
  "brand_id": "BRAND_90FD92XX",
  "campaign_id": "CAMP_96A1D9CA",
  "roas_metrics": {
    "verified_consumption_inr": 5250,
    "total_redemptions": 30,
    "roas_ratio": 0.1
  },
  "attribution_correctness": {
    "roas_computation_basis": "actual_consumption",
    "not_based_on": ["tasks", "views", "impressions"]
  }
}
```

## Technical Architecture

```
/app/
├── backend/
│   ├── server.py           # Main FastAPI application
│   ├── models.py           # Pydantic/MongoDB models
│   ├── fulfillment_routes.py
│   ├── support_routes.py
│   ├── brand_routes.py
│   ├── clans_routes.py
│   └── leaderboards_routes.py
└── frontend/
    └── src/
        ├── pages/
        │   ├── Dashboard.js
        │   ├── Shop.js
        │   ├── Support.js
        │   ├── Clans.js
        │   ├── Leaderboards.js
        │   └── brand/BrandPortal.js
        └── context/AuthContext.js
```

## Key API Endpoints
- `/api/auth/*` - User authentication
- `/api/products` - Shop products
- `/api/redemptions` - Order/redemption management
- `/api/fulfillments/*` - Voucher fulfillment pipeline
- `/api/support/*` - Chat bot and tickets
- `/api/clans/*` - Clan management
- `/api/leaderboards/*` - Skill-based rankings
- `/api/brand/*` - Brand portal (separate auth)

## Database Collections
- `users` - User accounts with coins, level, XP
- `products` - Brand-funded SKUs
- `redemptions` - User orders
- `fulfillments` - Voucher delivery records
- `support_tickets` - User support requests
- `clans` - User groups
- `brand_accounts` - Brand partner accounts
- `brand_campaigns` - Campaign management
- `brand_products` - Brand-specific SKUs

## What's MOCKED
- Cricket match data (live scores, ball-by-ball)
- Voucher fulfillment providers (Amazon, Swiggy APIs)
- Brand campaign budget deduction

## Upcoming Tasks

### Phase 4: Beta Testing & Polish (Target: Mar 21, 2026)
- [ ] Onboard beta users
- [ ] Bug fixes from user feedback
- [ ] Performance optimization
- [ ] Mobile responsiveness audit

### Phase 5: Launch Prep (Target: Mar 26, 2026)
- [ ] Server scaling
- [ ] Monitoring setup
- [ ] Soft launch for IPL 2026

## Future/Backlog
- [ ] Live cricket data API integration
- [ ] Real voucher provider integrations
- [ ] AdMob monetization
- [ ] Premium subscriptions
- [ ] ONDC/Q-Comm fulfillment
- [ ] Push notifications

## Test Credentials
- **User**: Register new account or use existing test users
- **Brand**: Register via `/api/brand/auth/register`

## Known Technical Notes
- Screenshot tool loses auth on hard navigation (use client-side nav buttons)
- Auth state managed via React context + localStorage token
- Brand Portal has separate JWT authentication system
