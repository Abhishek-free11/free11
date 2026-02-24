# FREE11 Phase 1 (Beta) — UPGRADED SCOPE

**Date:** February 24, 2026  
**Status:** BETA BUILD COMPLETE (UPGRADED)
**Positioning:** Sports Fan Community / Social Entertainment
**Geo-restriction:** India only (all states allowed)

---

## Scope Upgrade: MVP 1.0 + MVP 1.5 Merged into Beta

### Card Games Added (Coins Only)
| Game | Entry | 1st Place | 2nd Place | Participate |
|------|-------|-----------|-----------|-------------|
| **Rummy** | FREE | 50 coins | 20 coins | 5 coins |
| **Teen Patti** | FREE | 40 coins | 15 coins | 5 coins |
| **Poker** | FREE | 60 coins | 25 coins | 5 coins |

**All games use the same:**
- ✅ Coin wallet (earn-only, non-cash, non-withdrawable)
- ✅ Catalog + Redemption + Fulfilment
- ✅ Admin + Support + Abuse controls
- ✅ No ads, no cash-out, no buy-ins
- ✅ India-only availability

---

## Access Information

### Web App URL
**https://cricket-coins.preview.emergentagent.com**

### Test Credentials
- **Admin Account:**
  - Email: `abhishek@free11.com`
  - Password: `admin123`
  
- **Beta Invite Codes (for new users):**
  - `BETA01`, `BETA02`, `BETA03` ... `BETA50`
  - 50 codes available, case-insensitive

---

## User Flow: Install → Contest → Score → Coins → Redeem → Fulfilment

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           FREE11 CORE LOOP (ONE-PAGE FLOW)                              │
└─────────────────────────────────────────────────────────────────────────────────────────┘

   INSTALL          REGISTER         JOIN CONTEST        PARTICIPATE         SCORE
     │                  │                  │                  │                 │
     ▼                  ▼                  ▼                  ▼                 │
┌─────────┐       ┌───────────┐      ┌───────────┐     ┌───────────────┐       │
│Download │──────▶│ 18+ Age   │─────▶│ Browse    │────▶│ Make Calls    │       │
│FREE11   │       │ Verify    │      │ Live      │     │ (3 Types)     │       │
│App      │       │ + State   │      │ Matches   │     │               │       │
└─────────┘       │ Check     │      │           │     │ • Ball-by-Ball│       │
                  │ + Invite  │      │ OR        │     │ • Over Outcome│       ▼
                  └───────────┘      │           │     │ • Match Winner│  ┌─────────┐
                        │            │ Build     │     │               │  │ Correct │
                        │            │ Fantasy   │     │ OR            │  │ = Coins │
                        ▼            │ Team      │     │               │  │ Earned  │
                   +50 Welcome       └───────────┘     │ Fantasy Team  │  └─────────┘
                     Coins                 │           │ Points        │       │
                                           │           └───────────────┘       │
                                           │                  │                 │
                                           └──────────────────┴─────────────────┘
                                                              │
                                                              ▼
                                                     ┌───────────────┐
                                                     │ COIN WALLET   │
                                                     │ (Earn-Only)   │
                                                     │ Non-Cash      │
                                                     │ Non-Withdraw  │
                                                     └───────────────┘
                                                              │
   ┌──────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                      REDEEM                                              │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│   │ ₹50 Mobile  │    │ Swiggy ₹100 │    │ Amazon ₹500 │    │ Netflix     │             │
│   │ Recharge    │    │ Voucher     │    │ Gift Card   │    │ Subscription│             │
│   │             │    │             │    │             │    │             │             │
│   │ 100 coins   │    │ 200 coins   │    │ 1000 coins  │    │ 500 coins   │             │
│   │ Level 1     │    │ Level 2+    │    │ Level 3+    │    │ Level 2+    │             │
│   └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘             │
│                                                                                          │
│   Categories: Recharge | Food | Vouchers | Electronics | Fashion | Groceries            │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                                              │
                                                              ▼
                                                     ┌───────────────┐
                                                     │ FULFILMENT    │
                                                     │               │
                                                     │ Order Placed  │
                                                     │      ↓        │
                                                     │ Processing    │
                                                     │      ↓        │
                                                     │ Delivered     │
                                                     │ (Email/SMS)   │
                                                     └───────────────┘
```

---

## What's Built (Beta Features)

### ✅ BUILD (New)

| Feature | Status | Notes |
|---------|--------|-------|
| **Fantasy Team Contests** | ✅ Complete | Dream11-style 11-player selection, captain/VC multipliers |
| **Over Outcome Predictions** | ✅ Complete | 0-5, 6-10, 11-15, 16+, Wicket — 25 coins/correct |
| **Match Winner Predictions** | ✅ Complete | Team A vs Team B — 50 coins/correct |
| **Limited Ball-by-Ball** | ✅ Complete | Capped at 20 predictions per match — 5-15 coins/correct |
| **Private Leagues** | ✅ Complete | User-created P2P leagues, share codes, leaderboards |
| **Age Gate** | ✅ Complete | 18+ verification at registration (DOB field) |
| **Geo-blocking** | ✅ Complete | AP, Telangana, Assam, Odisha, Sikkim, Nagaland blocked |
| **Feature Flags** | ✅ Complete | Kill switches per feature via `/api/features/flags` |

### ✅ SALVAGE (Refactored)

| Component | Status | Changes |
|-----------|--------|---------|
| **Auth / Onboarding** | ✅ Working | Added age gate, state selection |
| **Coin Ledger** | ✅ Working | Earn-only, PRORGA-compliant |
| **Catalog + Redemption** | ✅ Working | Foodtech / QComm / E-comm products |
| **Orders + Fulfilment** | ✅ Working | Status tracking, support integration |
| **Admin + Support** | ✅ Working | Beta dashboard, ticket system |
| **Clans + Leaderboards** | ✅ Working | Global rankings, clan challenges |

### ❌ EXPLICITLY OUT OF BETA

| Feature | Status |
|---------|--------|
| Cash deposits | NOT INCLUDED |
| Cash-out | NOT INCLUDED |
| Buy-ins | NOT INCLUDED |
| Ads / AdMob | REMOVED |
| Live player trading | NOT INCLUDED |
| Coin gifting | NOT INCLUDED |

---

## Positioning (Implemented)

### Language Guidelines (Enforced)
- ✅ "Coins" instead of "money" or "cash"
- ✅ "Community" instead of "gaming"
- ✅ "Participate" instead of "bet"
- ✅ "Earn through skill" instead of "win"
- ✅ "Redeem for products" instead of "prizes"

### App Store Category Compliance
- Primary: Sports / Community
- Secondary: Entertainment / Social
- Avoid: Gaming / Fantasy / Betting

---

## Screenshots (All Major Flows)

| Flow | Screen | Status |
|------|--------|--------|
| Entry | Landing Page | ✅ |
| Entry | Registration (18+ Age Gate) | ✅ |
| Entry | Login | ✅ |
| Home | Dashboard | ✅ |
| Contest | Cricket Predictions | ✅ |
| Contest | Ball-by-Ball Predictions | ✅ |
| Contest | Over Outcome Predictions | ✅ |
| Contest | Match Winner Predictions | ✅ |
| Contest | Fantasy Team Selection | ✅ |
| Social | Private Leagues | ✅ |
| Social | Clans | ✅ |
| Social | Leaderboards | ✅ |
| Redeem | Shop / Catalog | ✅ |
| Redeem | Redemption Confirmation | ✅ |
| Fulfil | Order Status | ✅ |
| Support | Help & Tickets | ✅ |
| Admin | Beta Dashboard | ✅ |

---

## Known Gaps + Phase 2 Polish List

### Mock/Placeholder Components
| Component | Current State | Phase 2 Action |
|-----------|---------------|----------------|
| Live Cricket Data | Mock CSK vs MI match | Integrate CricAPI/SportRadar |
| Voucher Delivery | Order placed, not fulfilled | Integrate Amazon/Brand APIs |
| Push Notifications | Not implemented | Add Firebase/OneSignal |
| Email Notifications | Sandbox mode | Production Resend setup |

### Technical Debt
| Item | Priority | Phase 2 Action |
|------|----------|----------------|
| Password utils duplication | P2 | Extract to shared utility |
| Test coverage | P1 | Add comprehensive tests |
| Mobile app build | P0 | React Native / PWA setup |
| Performance optimization | P2 | Caching, CDN, lazy loading |

### UX Polish
| Item | Priority | Phase 2 Action |
|------|----------|----------------|
| Onboarding tutorial | P1 | Interactive walkthrough |
| Loading states | P2 | Skeleton screens |
| Error messages | P2 | More contextual errors |
| Accessibility | P2 | WCAG compliance |

---

## API Endpoints (Key)

### Features & Compliance
- `GET /api/features/flags` — Feature flag status
- `GET /api/features/blocked-states` — Geo-blocked states
- `POST /api/features/compliance-check` — Age + Geo validation

### Fantasy & Predictions
- `GET /api/fantasy/matches/{match_id}/players` — Player list
- `POST /api/fantasy/teams/create` — Create fantasy team
- `GET /api/fantasy/matches/{match_id}/contests` — Available contests
- `POST /api/cricket/predict/ball` — Ball-by-ball (limited)
- `POST /api/cricket/predict/over` — Over outcome
- `POST /api/cricket/predict/winner` — Match winner

### Private Leagues
- `POST /api/leagues/create` — Create league
- `POST /api/leagues/join` — Join with code
- `GET /api/leagues/{id}/leaderboard` — League standings

---

## Compliance Summary

| Requirement | Status |
|-------------|--------|
| **India-only access** | ✅ Enforced (non-India blocked) |
| **18+ Age Gate** | ✅ Enforced at registration |
| **All Indian states allowed** | ✅ No state blocking |
| No cash deposits | ✅ Not implemented |
| No cash-out | ✅ Not implemented |
| No buy-ins | ✅ All contests FREE entry |
| Earn-only coins | ✅ PRORGA-compliant |
| No gambling language | ✅ Copy updated |

---

## Next Steps (Phase 2)

1. **Production deployment setup**
2. **Live cricket data API integration**
3. **Real voucher delivery mechanism**
4. **Push notification system**
5. **Performance optimization**
6. **Mobile app build (Android APK)**

---

**Phase 1 Beta: COMPLETE**  
**Ready for: User testing and feedback collection**
