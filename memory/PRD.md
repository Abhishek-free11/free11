# FREE11 - Demand Rail Platform
## Product Requirements Document (PRD)

### Original Problem Statement
Build a cricket prediction and engagement platform called FREE11 to capture the 60 million displaced Real Money Gaming (RMG) users in India following a government ban. The platform converts **attention + skill into consumption** (Demand Rail), not a generic earn-and-redeem app.

### Core Thesis (Demand Rail)
```
Time → Skill → Coins → Goods → Utility → Repeat
```
- **Skill Loop:** Cricket predictions drive earning
- **Consumption Loop:** Coins redeem for brand-funded goods
- **Ego Loop:** Progression, badges, leaderboards on skill accuracy

### Target Audience
- Former RMG/fantasy cricket users in India
- Consumption-constrained cohort seeking ability-to-pay unlock
- Brand partners seeking demand creation + ROAS

### PRORGA Compliance (Non-Financial Instrument)
- ✅ Coins are **non-purchasable** (no buying with money)
- ✅ Coins are **non-withdrawable** (no cash conversion)
- ✅ Coins are **non-transferable** (no P2P transfer)
- ✅ Coins are **redeemable only for goods/services**
- ✅ **No gambling language** (no bet, stake, jackpot, win)
- ✅ Brand-funded rewards (not platform-subsidized)

---

## Implementation Status

### Phase 1: Demand Rail Restructure ✅ COMPLETE (Feb 23, 2026)

#### Key Changes:
1. **Cricket as Hero** - Dashboard centers on Live Cricket Prediction
2. **Boosters (not Core)** - Ads/Games labeled as "Coin Boosters" 
3. **PRORGA Disclaimer** - Banner on dashboard
4. **Brand-Funded Schema** - Products have brand_id, campaign_id
5. **Impulse Rewards** - Starting at ₹10 (Mobile Recharge)
6. **Progression System** - Ranks, badges, skill-based leaderboard
7. **Demand Progress** - Shows path to next real-world reward
8. **FAQ Page** - PRORGA-compliant coin policy disclaimer prominently displayed ✅ (Added Feb 2026)

#### Backend Schema Updates:
| Model | New Fields |
|-------|-----------|
| **User** | prediction_streak, total_predictions, correct_predictions, consumption_unlocked, badges |
| **Product** | brand_id, campaign_id, funded_by_brand, fulfillment_type, min_level_required, is_limited_drop |
| **Redemption** | brand_id, campaign_id, fulfillment_type, sku, brand_cost |
| **CoinTransaction** | source (skill/booster/bonus) |

#### New APIs:
| Endpoint | Purpose |
|----------|---------|
| `/api/user/demand-progress` | Progress to next reward, prediction stats, consumption unlocked |
| `/api/user/badges` | User's earned badges |
| `/api/admin/brand-roas` | Brand ROAS dashboard (placeholder) |
| `/api/leaderboard` | Skill-based leaderboard (accuracy, not coins) |
| `/api/faq` | FAQ items with PRORGA-compliant coin policy |

#### Product Tiers:
| Tier | Examples | Coin Range | Level Required |
|------|----------|------------|----------------|
| Impulse | Mobile Recharge, CCD Coffee, OTT Trials | 10-50 | 1 (Rookie) |
| Mid-Tier | Swiggy ₹100-200, Amazon ₹100-500, Groceries | 100-500 | 1-2 |
| Premium | Flipkart ₹1000, Nike Shoes | 1000-5000 | 3-4 (Pro/Expert) |
| Aspirational | Samsung S24, iPhone 15 Pro | 35000-50000 | 5 (Legend) |

#### User Ranks:
| Level | Name | Min XP | Color |
|-------|------|--------|-------|
| 1 | Rookie | 0 | Slate |
| 2 | Amateur | 100 | Green |
| 3 | Pro | 500 | Blue |
| 4 | Expert | 1500 | Purple |
| 5 | Legend | 5000 | Gold |

#### Badges System:
- first_prediction, prediction_pro (50% accuracy), streak_7, streak_30
- first_redemption, hot_streak (5 correct in a row)
- level_pro, level_expert, level_legend
- consumption_100 (₹100 unlocked), consumption_500

### Previous Phase: Cricket Core ✅ (Feb 22, 2026)
- Ball-by-ball prediction engine
- Watch ads to earn (50 coins/ad, 5/day)
- Gift card system with admin bulk upload

### MVP1 Features (Previously Complete):
- User authentication (JWT)
- Daily check-in with streak bonus
- Mini-games (Quiz, Spin Wheel, Scratch Card)
- Multi-language support (8 Indian languages)

---

## Upcoming Phases

### Phase 2: Clans & Leaderboards ✅ COMPLETE (Feb 24, 2026)
- [x] Clan creation and joining (Level 2+ to create, free to join)
- [x] Clan vs Clan leaderboards (skill-based: accuracy, not coins)
- [x] Prediction duels (badge rewards, NO coin transfers)
- [x] Global, Weekly, Streak leaderboards
- [x] Public profiles (skill stats only, NO coin display)
- [x] Activity feed for clan achievements

### Phase 3: Automation & Brand Tools ✅ COMPLETE (Feb 24, 2026)
- [x] Voucher fulfillment pipeline (pluggable providers, MOCKED but production-ready)
- [x] Support chatbot (deterministic FAQ + order status + tickets)
- [x] Brand Portal at /brand with brand-specific authentication
- [x] ROAS analytics dashboard (verified consumption, NO impressions/CPM)
- [x] Campaign & product management for brands

### Phase 4: Beta Testing & Polish (Due: Mar 21, 2026)
- [ ] Dynamic pricing on products
- [ ] Limited-time drops
- [ ] Shop tiers (unlock better items at higher levels)
- [ ] Soft expiry warning for inactive coins (30-60 days)

### Phase 5: ONDC/Q-Comm Integration (Post-IPL)
- [ ] ONDC BAP adapter
- [ ] Q-Commerce integration
- [ ] D2C fulfillment

---

## Technical Architecture

```
/app/
├── backend/
│   ├── server.py          # Main FastAPI app + models
│   ├── cricket_routes.py  # Cricket prediction APIs
│   ├── ads_routes.py      # AdMob reward APIs
│   ├── clans_routes.py    # Clans system APIs
│   ├── leaderboards_routes.py # Leaderboards & Duels APIs
│   ├── fulfillment_routes.py  # Voucher fulfillment pipeline
│   ├── support_routes.py      # Support chatbot & tickets
│   ├── brand_routes.py        # Brand Portal APIs
│   ├── gift_card_routes.py # Gift card management
│   └── tests/
│       └── test_demand_rail.py
└── frontend/
    └── src/
        ├── pages/
        │   ├── Dashboard.js    # Demand Rail dashboard
        │   ├── Cricket.js      # Cricket predictions
        │   ├── EarnCoins.js    # Coin Boosters
        │   └── Shop.js         # Redemption shop
        └── components/
            └── Navbar.js       # Updated hierarchy
```

### Navigation Hierarchy (Demand Rail):
```
Home → Predict (🏏) → Boost → Redeem → Orders
        ↑ SKILL        ↑ BONUS    ↑ CONSUMPTION
```

---

## Testing Status

### Test Reports:
- `/app/test_reports/iteration_1.json` - Cricket Core (100% pass)
- `/app/test_reports/iteration_2.json` - Demand Rail (100% pass)

### Test Credentials:
- Email: `cricket@free11.com`
- Password: `cricket123`

---

## Key Metrics (Soft Launch Target - Mar 26, 2026)
- DAU: 10,000 users
- Predictions/day: 50,000+
- Skill accuracy average: 30-40%
- Impulse redemptions/day: 500+
- Brand ROAS: 3-5x

---

*Last Updated: February 24, 2026*
*Sprint Day: 3 of 33*
*Phase 3 Complete - AHEAD of Schedule!*
