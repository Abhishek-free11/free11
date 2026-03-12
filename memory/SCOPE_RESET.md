# FREE11 - Scope Reset & Salvage Plan
**Date:** February 24, 2026  
**Status:** SCOPE RESET

---

## Delivery Model (LOCKED)

| Phase | Description | Delivery |
|-------|-------------|----------|
| **Phase 1 (Beta)** | Real Product Beta | ONE consolidated drop |
| **Phase 2 (MVP)** | Polish + Stability | ONE consolidated drop |
| **MVP 1.5** | Rummy/Poker/Teen Patti | May 1, 2026 |

**No piecemeal releases. No weekly drops.**

---

## Final Product Model

### Core Features (Beta Must Reflect)
| Feature | Status | Notes |
|---------|--------|-------|
| Fantasy Team Contests | 🔴 BUILD | Dream11-style UX |
| Over Outcome | 🔴 BUILD | New prediction type |
| Match Winner | 🔴 BUILD | New prediction type |
| Ball-by-Ball (limited) | ✅ EXISTS | Keep but secondary |
| Leaderboards | ✅ EXISTS | Enhance |
| Private Leagues (P2P) | 🔴 BUILD | No money |
| Clans | ✅ EXISTS | Working |
| Coins (earn-only) | ✅ EXISTS | PRORGA-compliant |
| Catalog Redemption | ✅ EXISTS | Foodtech/QComm/ECom |
| Age Gate | 🔴 BUILD | Required |
| Geo-blocking | 🔴 BUILD | Required |
| Admin Dashboard | ✅ EXISTS | Enhance |
| Support System | ✅ EXISTS | Working |
| Feature Flags | 🟡 PARTIAL | Need enhancement |
| Abuse Controls | 🟡 PARTIAL | Need enhancement |

### Must NOT Be in Beta
| Feature | Status | Action |
|---------|--------|--------|
| Cash deposits/cash-out/buy-ins | ✅ NOT PRESENT | None |
| Ads / AdMob | ⚠️ PRESENT | **REMOVE** |
| Live player trading | ✅ NOT PRESENT | None |
| Coin gifting | ✅ NOT PRESENT | None |

---

## Salvage Assessment

### ✅ REUSE (No Changes)
| Component | Location | Status |
|-----------|----------|--------|
| Auth / Onboarding | `server.py`, `Login.js`, `Register.js` | Working |
| Coin Ledger | `server.py` (add_coins, spend_coins) | Working |
| Catalog Wiring | `Shop.js`, products routes | Working |
| Orders + Fulfillment | `fulfillment_routes.py`, `MyOrders.js` | Working |
| Admin Dashboard | `Admin.js`, admin routes | Working |
| Support System | `support_routes.py`, `Support.js` | Working |
| Telemetry | `reports_routes.py` | Working |

### 🔧 REFACTOR
| Component | Current | Target |
|-----------|---------|--------|
| Scoring Pipeline | Ball-by-ball only | Multi-format (Fantasy, Over, Match) |
| Contest Engine | Basic predictions | Full contest system |
| Leaderboards | Global only | + Private Leagues |
| Clans | Basic | + Challenges |

### 🔴 BUILD NEW
| Component | Description |
|-----------|-------------|
| Fantasy Team System | Dream11-style player selection |
| Contest Types | Over Outcome, Match Winner |
| Private Leagues | User-created P2P leagues |
| Age Gate | 18+ verification |
| Geo-blocking | State-based restrictions |
| Feature Flags | Kill switches per feature |

### ❌ REMOVE
| Component | Location |
|-----------|----------|
| Ads/AdMob | `ads_routes.py`, `EarnCoins.js` (Watch Ads section) |

---

## Phase 1 (Beta) Deliverables

### 1. Working Beta Build
- [ ] Fantasy Team contests (Dream11-style)
- [ ] Over Outcome predictions
- [ ] Match Winner predictions
- [ ] Ball-by-Ball (limited/secondary)
- [ ] Leaderboards (Global + Weekly + Private)
- [ ] Private Leagues
- [ ] Clans (existing)
- [ ] Coins (earn-only)
- [ ] Catalog redemption
- [ ] Age gate
- [ ] Geo-blocking
- [ ] Admin + Support
- [ ] Feature flags

### 2. Screenshots (All Major Flows)
- [ ] Landing / Entry
- [ ] Registration (with age gate)
- [ ] Contest Discovery
- [ ] Fantasy Team Selection
- [ ] Over/Match Predictions
- [ ] Live Match View
- [ ] Leaderboards
- [ ] Private League Creation
- [ ] Coin Wallet
- [ ] Shop / Catalog
- [ ] Redemption Flow
- [ ] Order Status
- [ ] Support

### 3. User Flow (1-pager)
```
Install → Register (18+) → Join Contest → Build Team/Predict → Score → Earn Coins → Redeem → Fulfilment
```

### 4. Known Gaps + Phase 2 Polish List
- Live cricket API integration (mock data in Beta)
- Real voucher delivery (mock in Beta)
- Payment gateway for brands
- Push notifications
- Deep linking
- Performance optimization
- Analytics integration

---

## Implementation Order

### Step 1: Remove Ads
- Remove `ads_routes.py` from backend
- Remove "Watch Ads" section from `EarnCoins.js`
- Remove ads API from `api.js`

### Step 2: Add Age Gate + Geo-blocking
- Add age verification to registration
- Add blocked states list
- Add location check

### Step 3: Build Fantasy Team System
- Create Fantasy models
- Build team selection UI
- Implement scoring logic

### Step 4: Add Over Outcome + Match Winner
- Add new prediction types
- Build UI components
- Implement scoring

### Step 5: Build Private Leagues
- Create league models
- Build league UI
- Implement leaderboards

### Step 6: Feature Flags + Abuse Controls
- Add feature flag system
- Add rate limiting
- Add fraud detection

---

## Files to Modify/Create

### Backend
| File | Action |
|------|--------|
| `server.py` | Add age/geo models |
| `cricket_routes.py` | Add Over/Match predictions |
| `fantasy_routes.py` | **NEW** - Fantasy team system |
| `leagues_routes.py` | **NEW** - Private leagues |
| `ads_routes.py` | **DELETE** |
| `feature_flags.py` | **NEW** - Feature flag system |

### Frontend
| File | Action |
|------|--------|
| `Register.js` | Add age gate |
| `Cricket.js` | Refactor for multi-format |
| `Fantasy.js` | **NEW** - Fantasy team UI |
| `Leagues.js` | **NEW** - Private leagues UI |
| `EarnCoins.js` | Remove ads section |
| `api.js` | Update endpoints |

---

## Timeline Estimate

| Task | Effort |
|------|--------|
| Remove Ads | 30 min |
| Age Gate + Geo-blocking | 2 hours |
| Fantasy Team System | 6-8 hours |
| Over/Match Predictions | 2-3 hours |
| Private Leagues | 4-5 hours |
| Feature Flags | 2 hours |
| Screenshots + Documentation | 2 hours |
| Testing | 4 hours |

**Total: ~24-30 hours of development**

---

## Default Decisions Made

1. **Age Gate**: 18+ (standard for fantasy sports in India)
2. **Blocked States**: Andhra Pradesh, Telangana, Assam, Odisha, Sikkim, Nagaland (based on gaming regulations)
3. **Fantasy Points**: Standard Dream11-style (runs, wickets, catches, etc.)
4. **Private League Size**: Max 100 members
5. **Over Outcome Options**: 0-5, 6-10, 11-15, 16+, Wicket Fall
6. **Match Winner**: Team A / Team B / Tie

---

*Ready to proceed with implementation.*
