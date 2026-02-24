# FREE11 Beta - UX Audit Pack
**Date:** February 24, 2026  
**Build:** Closed Beta v1.0

---

## 1. User Journey Screenshots

### Entry Points
| Screen | URL | Description |
|--------|-----|-------------|
| Landing | `/` | "Make the right calls. Get real products." - Hero with Join Beta CTA |
| Register | `/register` | Name, Email, Password + **Invite Code (Required)** |
| Login | `/login` | Email + Password with show/hide toggle |

### Core App Screens
| Screen | URL | Description |
|--------|-----|-------------|
| Home/Dashboard | `/dashboard` | User profile, progress bar to next reward, live match card, skill stats, leaderboard preview |
| Predict (Cricket) | `/cricket` | **Ball-by-ball prediction** - CSK vs MI live, 8 outcome options (Dot, 1-4, Six, Wicket, Wide) |
| Shop/Redeem | `/shop` | Product catalog with category filters, level-gated items, coin prices |
| Ranks/Leaderboard | `/leaderboards` | Global rankings by accuracy, Prediction Duels, Activity Feed |
| Clans | `/clans` | Browse/create clans, clan leaderboard, challenges |
| Boosters | `/earn` | Watch Ads (+50 coins), Mini Games, Tasks - marked as "supplementary" |
| Profile | `/profile` | Wallet (balance, earned, unlocked), prediction stats, activity stats |
| Support | `/support` | Chat bot, My Tickets, My Vouchers tabs |
| FAQ | `/faq` | Common questions about coins, redemption, legality |

### Admin (Beta Only)
| Screen | URL | Description |
|--------|-----|-------------|
| Beta Dashboard | `/admin` | Beta health, user metrics, funnel, invite codes, top predictors |

---

## 2. Simple User Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FREE11 CORE LOOP: ENTRY → RECEIVE                     │
└─────────────────────────────────────────────────────────────────────────┘

    ENTRY                CALL                 EARN              REDEEM            RECEIVE
    ─────                ────                 ────              ──────            ───────
      │                    │                   │                  │                  │
      ▼                    ▼                   ▼                  ▼                  ▼
┌──────────┐        ┌──────────────┐    ┌──────────┐      ┌──────────┐      ┌──────────┐
│  Landing │───────▶│   Live Match │───▶│ Prediction│─────▶│   Shop   │─────▶│ Voucher  │
│   Page   │        │  Prediction  │    │  Result   │      │  Browse  │      │ Delivery │
└──────────┘        └──────────────┘    └──────────┘      └──────────┘      └──────────┘
      │                    │                   │                  │                  │
      │                    │                   │                  │                  │
   Sign Up          Select Outcome      Correct = Coins     Select Item       Order Status
   (Invite Code)    (8 options)         5-15 coins/call     (Level Gated)     in Support
      │                    │                   │                  │                  │
      ▼                    ▼                   ▼                  ▼                  ▼
   +50 Welcome      Ball-by-Ball         Accuracy %         Redeem Now         Delivered!
     Coins          Only (Today)         Tracked            (100+ coins)       
```

### Flow Details:

1. **ENTRY** → User lands on homepage → Signs up with invite code → Gets 50 welcome coins
2. **CALL** → User opens Predict tab → Sees live CSK vs MI → Predicts next ball outcome (Dot/1/2/3/4/6/Wicket/Wide)
3. **EARN** → Correct prediction = 5-15 coins → Accuracy % tracked → Appears on leaderboard
4. **REDEEM** → User reaches 100+ coins → Browses Shop → Selects ₹50 Mobile Recharge → Confirms redemption
5. **RECEIVE** → Order placed → Status tracked → Voucher delivered (currently MOCKED)

---

## 3. Prediction Formats

### What's LIVE Today ✅
| Format | Description | Status |
|--------|-------------|--------|
| **Ball-by-Ball** | Predict outcome of each delivery (Dot, 1, 2, 3, 4, 6, Wicket, Wide) | ✅ LIVE |

### What's Coming (Next Beta Patch) 🔜
| Format | Description | Priority | ETA |
|--------|-------------|----------|-----|
| **Over Outcome** | Predict total runs in an over (0-5, 6-10, 11-15, 16+) | P1 | Patch 1.1 |
| **Match Winner** | Pre-match prediction of winning team | P1 | Patch 1.1 |
| **Powerplay Runs** | Predict runs scored in first 6 overs | P2 | Patch 1.2 |

### Planned (Future Phases) 📋
| Format | Description | Notes |
|--------|-------------|-------|
| **Team Formation** | Dream11-style fantasy team selection | Requires player database integration |
| **Scenario-Based** | "Will Dhoni hit a six in last over?" | Requires rich match event data |
| **Top Scorer** | Predict highest scorer of the match | Requires live scorecard API |

---

## 4. Current Limitations (Beta)

### MOCKED Components
- ❌ Live cricket data (using static CSK vs MI mock)
- ❌ Voucher delivery (order placed but not fulfilled)
- ❌ Email notifications (sandbox mode)

### Not Yet Built
- ❌ Multiple prediction formats (only ball-by-ball)
- ❌ Multiple matches (single mock match)
- ❌ Player-level predictions

---

## 5. Gap Analysis vs Dream11

| Feature | Dream11 | FREE11 (Today) | Plan |
|---------|---------|----------------|------|
| Team Formation | ✅ 11-player selection | ❌ | Phase 3 |
| Contest Types | ✅ Multiple formats | ⚠️ Ball-by-ball only | Patch 1.1 |
| Entry Fee | ✅ Cash entry | ❌ Free (by design) | N/A |
| Prize Pool | ✅ Cash prizes | ✅ Brand vouchers | Core thesis |
| Live Score | ✅ Real-time | ⚠️ Mock data | Patch 1.2 |
| Social | ✅ Contests with friends | ⚠️ Clans (basic) | Patch 1.1 |

---

## 6. Recommendations for Next Wave Sign-off

### Must-Have for Wave 2
1. **Add Over Outcome prediction** - Lower friction than ball-by-ball
2. **Add Match Winner prediction** - Simple entry point for new users
3. **Fix live data integration** - At minimum, show real match schedules

### Nice-to-Have
1. Add prediction history page
2. Show "coins you could win" before prediction
3. Add tutorial overlay on first prediction

---

## 7. Empty States Observed
- ✅ Leaderboard: "No predictions yet"
- ✅ Clans: Shows available clans to join
- ✅ Activity Feed: "No recent activity"
- ✅ Support Tickets: "No tickets yet"
- ✅ Prediction History: "No predictions yet"

---

## 8. Error States
- ✅ Invalid invite code message
- ✅ Level requirement for shop items
- ✅ Insufficient coins for redemption
- ⚠️ Network error handling (basic)

---

**Summary:**
Beta is stable with ball-by-ball prediction working end-to-end. Main gaps are:
1. Single prediction format (ball-by-ball only)
2. Mock data instead of live matches
3. No team formation / scenario-based predictions

**ETA for adding 1 non-ball-by-ball format:** Patch 1.1 (Over Outcome + Match Winner)

---
*Generated: Feb 24, 2026*
