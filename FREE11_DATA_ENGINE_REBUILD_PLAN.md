# FREE11 DATA ENGINE REBUILD - IMPLEMENTATION PLAN

## Executive Summary

Complete rebuild of the live cricket data layer to achieve production-grade integrity.

---

## TIMELINE (Estimated)

| Phase | Task | Duration |
|-------|------|----------|
| **1** | Disable Random Simulation | ✅ DONE |
| **2** | EntitySport Integration Setup | 2-3 hours |
| **3** | Ball-by-Ball Data Pipeline | 3-4 hours |
| **4** | Prediction Lock System | 2-3 hours |
| **5** | WebSocket Implementation | 3-4 hours |
| **6** | Cache TTL Optimization | 1 hour |
| **7** | Playing XI Logic | 1-2 hours |
| **8** | Testing & Validation | 2-3 hours |

**Total Estimated Time: 14-20 hours**

---

## DATA MODEL CHANGES

### New Collections/Tables

```python
# 1. Ball Events (Real-time BBB data)
ball_events = {
    "match_id": str,
    "innings_number": int,
    "over_number": int,
    "delivery_number": int,
    "event_id": str,  # EntitySport unique ID
    "ball_timestamp": int,  # Unix timestamp from API
    "api_received_at": datetime,  # When we got the data
    "batting_team_id": str,
    "bowler_id": str,
    "bowler_name": str,
    "striker_id": str,
    "striker_name": str,
    "runs_off_bat": int,
    "extras": int,
    "total_runs": int,
    "is_wicket": bool,
    "wicket_type": str,
    "commentary": str
}

# 2. Confirmed Playing XI
playing_xi = {
    "match_id": str,
    "team_id": str,
    "team_name": str,
    "players": [
        {"player_id": str, "name": str, "role": str}
    ],
    "captain_id": str,
    "keeper_id": str,
    "confirmed": bool,
    "confirmed_at": datetime,
    "source": str  # "toss", "api", "manual"
}

# 3. Prediction Lock Events
prediction_locks = {
    "match_id": str,
    "innings_number": int,
    "over_number": int,
    "delivery_number": int,
    "lock_timestamp": int,  # When prediction window closed
    "ball_timestamp": int,  # Actual ball delivery time
    "status": str  # "open", "locked", "resolved"
}

# 4. Ball Predictions (Updated schema)
ball_predictions = {
    "id": str,
    "user_id": str,
    "match_id": str,
    "innings_number": int,
    "over_number": int,
    "delivery_number": int,
    "prediction": str,
    "predicted_at": int,  # Unix timestamp
    "ball_event_timestamp": int,  # Actual ball timestamp
    "is_valid": bool,  # predicted_at < ball_event_timestamp
    "actual_result": str,
    "is_correct": bool,
    "coins_earned": int,
    "validated_at": datetime
}
```

---

## INFRASTRUCTURE IMPACT

### API Changes
- **New Provider**: EntitySport REST API + WebSocket
- **Endpoints Added**:
  - `GET /api/cricket/bbb/{match_id}` - Ball-by-ball feed
  - `GET /api/cricket/playing-xi/{match_id}` - Confirmed XI
  - `WS /ws/match/{match_id}` - Real-time WebSocket
  - `POST /api/predict/ball` - Updated with timestamp validation

### Cache Layer
- **OLD**: 5-minute file cache
- **NEW**: 2-3 second Redis cache for live data

### Polling → WebSocket
- **OLD**: 30-60 second HTTP polling
- **NEW**: WebSocket push updates (<1 sec latency)

---

## COST ESTIMATE

### EntitySport API
| Plan | Price | Features |
|------|-------|----------|
| **Free** | $0 | 100 req/day, no BBB |
| **Basic** | ~$99/mo | 10K req/day, limited BBB |
| **Pro** | ~$299/mo | Unlimited req, full BBB, WebSocket |
| **Enterprise** | Custom | Dedicated, lowest latency |

**Recommendation**: Start with **Pro** ($299/mo) for full BBB + WebSocket

### Infrastructure
- Redis (for caching): $0 (use existing or local)
- No additional servers needed

---

## REQUIRED CREDENTIALS

To proceed with EntitySport integration, I need:

1. **EntitySport Account**
   - Sign up at: https://www.entitysport.com/cricket-api/
   - Get `access_key` and `secret_key`

2. **API Plan**
   - Must support ball-by-ball endpoint
   - Must support WebSocket (preferred)

---

## IMPLEMENTATION STEPS

### Step 1: Disable Random Simulation ✅ DONE
- Ball prediction endpoint now returns 503
- No simulated outcomes

### Step 2: EntitySport Integration
```python
# Environment variables needed
ENTITYSPORT_ACCESS_KEY=your_access_key
ENTITYSPORT_SECRET_KEY=your_secret_key
ENTITYSPORT_API_BASE=https://rest.entitysport.com/v2
```

### Step 3: Ball-by-Ball Pipeline
- Fetch real BBB data from EntitySport
- Store with event IDs and timestamps
- Validate sequence integrity

### Step 4: Prediction Lock System
```python
# Validation logic
def is_prediction_valid(prediction_timestamp, ball_event_timestamp):
    return prediction_timestamp < ball_event_timestamp
```

### Step 5: WebSocket Implementation
- Server-side: FastAPI WebSocket endpoint
- Client-side: Socket connection for live updates
- Auto-close prediction window on ball event

### Step 6: Cache Optimization
- Live data: 2-3 second TTL
- Ball events: No cache (real-time)
- Remove 1-hour fallback

### Step 7: Playing XI Logic
- Fetch from EntitySport squad endpoint post-toss
- Lock fantasy until XI confirmed
- Show "Lineup TBA" before toss

---

## RISK MITIGATION

| Risk | Mitigation |
|------|------------|
| EntitySport downtime | Failover to cached data (short TTL) |
| WebSocket disconnection | Auto-reconnect with exponential backoff |
| Timestamp sync issues | Server-side NTP sync, validate monotonic ordering |
| Cost overrun | Set request limits, monitor usage |

---

## SUCCESS CRITERIA

Before declaring stable:
- [ ] Ball-by-ball data from EntitySport working
- [ ] Event timestamps accurate (<1s drift)
- [ ] Prediction lock validates against ball timestamp
- [ ] Playing XI shows only confirmed 11 post-toss
- [ ] WebSocket updates in <3 seconds
- [ ] No random simulation anywhere
- [ ] 99.9% uptime during test period

---

## NEXT STEP

**I need EntitySport API credentials to proceed.**

Options:
1. Sign up at https://www.entitysport.com/cricket-api/
2. Get Pro plan ($299/mo) for full BBB + WebSocket
3. Share `access_key` and `secret_key`

Or confirm if you want me to:
- Use a different provider (Roanuz, SportMonks Premium)
- Implement a mock BBB service for testing first

---

*Document created: February 27, 2026*
