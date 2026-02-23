# FREE11 - Cricket Prediction Platform
## Product Requirements Document (PRD)

### Original Problem Statement
Build a cricket prediction and engagement platform called FREE11 to capture the 60 million displaced Real Money Gaming (RMG) users in India following a government ban. The platform enables users to predict ball-by-ball outcomes during live IPL matches, earn coins, and redeem them for gift cards.

### Target Audience
- Former RMG/fantasy cricket users in India
- Cricket enthusiasts who enjoy prediction-based engagement
- Users seeking skill-based earning opportunities (PRORGA compliant)

### Core Requirements
1. **Cricket Prediction Engine** - Ball-by-ball and match outcome predictions
2. **Coin Reward System** - Earn coins for correct predictions
3. **Watch Ads to Earn** - AdMob integration for additional earning
4. **Gift Card Redemption** - Convert coins to Amazon gift cards
5. **Social Features** - Clans and leaderboards (Phase 2)

---

## Implementation Status

### Phase 1: Cricket Core ✅ COMPLETE (Feb 23, 2026)

#### Backend APIs Implemented:
| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| `/api/cricket/matches` | GET | ✅ | List all matches |
| `/api/cricket/matches/live` | GET | ✅ | Get live matches |
| `/api/cricket/matches/{id}` | GET | ✅ | Get match details |
| `/api/cricket/predict/ball` | POST | ✅ | Ball-by-ball prediction |
| `/api/cricket/predict/match` | POST | ✅ | Match outcome prediction |
| `/api/cricket/predictions/my` | GET | ✅ | User's predictions |
| `/api/cricket/leaderboard` | GET | ✅ | Prediction leaderboard |
| `/api/ads/config` | GET | ✅ | Ad configuration |
| `/api/ads/status` | GET | ✅ | User's ad watch status |
| `/api/ads/reward` | POST | ✅ | Claim ad reward |
| `/api/gift-cards/available` | GET | ✅ | Available gift cards |
| `/api/gift-cards/redeem` | POST | ✅ | Redeem gift card |
| `/api/gift-cards/admin/upload-single` | POST | ✅ | Upload single card |
| `/api/gift-cards/admin/upload-bulk` | POST | ✅ | Bulk CSV upload |

#### Frontend Pages:
- ✅ Cricket.js - Live match display, ball prediction UI, leaderboard
- ✅ EarnCoins.js - Updated with "Watch Ads" tab (+50 coins/ad, 5/day limit)
- ✅ Navbar.js - Added Cricket navigation link

#### Key Features:
- **Ball Prediction Rewards:** 5 coins (dot/1/2/3), 10 coins (4), 15 coins (6/wicket)
- **Ad Rewards:** 50 coins per ad, max 5 ads/day (250 potential coins)
- **Gift Card System:** Admin bulk upload, auto-distribution on redemption

### MVP1 Features (Previously Complete):
- ✅ User authentication (JWT)
- ✅ Daily check-in with streak bonus
- ✅ Mini-games (Quiz, Spin Wheel, Scratch Card)
- ✅ Task completion system
- ✅ Product shop with redemption
- ✅ User profile and leaderboard
- ✅ Admin dashboard
- ✅ Multi-language support (8 Indian languages)

---

## Upcoming Phases

### Phase 2: Clans & Leaderboards (Due: Mar 7, 2026)
- [ ] Clan creation and joining
- [ ] Clan leaderboards
- [ ] Friend system
- [ ] Clan-based challenges

### Phase 3: Automation & Brand Tools (Due: Mar 14, 2026)
- [ ] Automated voucher delivery notifications
- [ ] Customer support chatbot
- [ ] Brand partner self-service dashboard
- [ ] Analytics dashboard

### Phase 4: Beta Testing & Polish (Due: Mar 21, 2026)
- [ ] Beta user onboarding
- [ ] Bug fixes and stability
- [ ] Performance optimization
- [ ] UI/UX refinements

### Phase 5: Launch Prep (Due: Mar 26, 2026)
- [ ] Server scaling
- [ ] Monitoring setup
- [ ] IPL 2026 soft launch

---

## Technical Architecture

```
/app/
├── backend/
│   ├── server.py          # Main FastAPI app
│   ├── cricket_routes.py  # Cricket prediction APIs
│   ├── ads_routes.py      # AdMob reward APIs
│   ├── gift_card_routes.py # Gift card management
│   └── cricket_service.py  # Cricket data service
└── frontend/
    └── src/
        ├── pages/
        │   ├── Cricket.js      # Cricket predictions UI
        │   ├── EarnCoins.js    # Earn page with Watch Ads
        │   └── [other pages]
        └── utils/
            └── api.js          # API client
```

### Database Collections:
- `users` - User accounts
- `cricket_matches` - IPL match data
- `ball_predictions` - Ball-by-ball predictions
- `match_predictions` - Match outcome predictions
- `ad_watches` - Ad viewing records
- `gift_cards` - Gift card inventory
- `gift_card_redemptions` - Redemption records

---

## Testing Status

### Test Report: iteration_1.json
- **Backend:** 22/22 tests passed (100%)
- **Frontend:** All features working (100%)
- **Test User:** cricket@free11.com / cricket123

### Known Limitations (Demo Mode):
- Cricket match data uses mock IPL 2026 fixtures
- Ball prediction outcomes are randomly simulated
- AdMob uses test ad unit IDs (3-second simulation)

---

## Key Metrics (Target for Soft Launch)
- DAU: 10,000 users
- Predictions/day: 50,000+
- Ad impressions/day: 25,000+
- Gift cards redeemed/week: 500+

---

*Last Updated: February 23, 2026*
*Sprint Day: 2 of 33*
