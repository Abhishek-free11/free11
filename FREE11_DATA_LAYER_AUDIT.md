# FREE11 LIVE CRICKET DATA INTEGRATION AUDIT
## FULL DATA LAYER VERIFICATION

Generated: February 27, 2026

---

## 1) RAW API RESPONSES

### 1A. Live Match Endpoint Response (Truncated for display)
```json
{
  "source": "cricketdata_api",
  "count": 25,
  "matches": [
    {
      "id": "7b52fba2-74fa-4d62-bc62-06c475d04540",
      "name": "India vs Zimbabwe, 48th Match, Super 8 Group 1, ICC Men's T20 World Cup 2026",
      "series": "ICC Men's T20 World Cup 2026",
      "team1": "India",
      "team1_short": "IND",
      "team2": "Zimbabwe",
      "team2_short": "ZIM",
      "status": "completed",
      "status_text": "India won by 72 runs",
      "venue": "MA Chidambaram Stadium, Chennai",
      "match_type": "t20",
      "start_time": "2026-02-26T13:30:00",
      "team1_score": "256/4 (20)",
      "team2_score": "184/6 (20)",
      "source": "cricketdata_api",
      "is_mock": false,
      "is_icc_worldcup": true,
      "is_ipl": false,
      "priority": 3,
      "failover_source": "primary"
    },
    {
      "id": "c3a6a2f0-6c2d-495e-b46c-707022052a2f",
      "name": "Australia Women vs India Women, 2nd ODI",
      "status": "live",
      "status_text": "Innings Break",
      "team1_score": null,
      "team2_score": "251/9 (50)",
      "failover_source": "primary"
    }
  ]
}
```

### 1B. Players/Squad Endpoint Response
```json
{
  "match_id": "c3a6a2f0-6c2d-495e-b46c-707022052a2f",
  "match_name": "Australia Women vs India Women, 2nd ODI, India Women tour of Australia, 2026",
  "team1": "Australia Women",
  "team2": "India Women",
  "players": [
    {"name": "Sophie Molineux", "team": "Australia Women", "team_short": "AUS", "role": "BAT", "credits": 8.0, "is_real": true},
    {"name": "Ellyse Perry", "team": "Australia Women", "team_short": "AUS", "role": "BAT", "credits": 8.0, "is_real": true},
    {"name": "Alyssa Healy", "team": "Australia Women", "team_short": "AUS", "role": "BAT", "credits": 8.0, "is_real": true},
    {"name": "Smriti Mandhana", "team": "India Women", "team_short": "IND", "role": "BAT", "credits": 8.0, "is_real": true},
    {"name": "Harmanpreet Kaur", "team": "India Women", "team_short": "IND", "role": "BAT", "credits": 8.0, "is_real": true},
    {"name": "Richa Ghosh", "team": "India Women", "team_short": "IND", "role": "BAT", "credits": 8.0, "is_real": true}
  ],
  "is_real_squad": true
}
```

### 1C. Confirmed Playing XI Endpoint
**CRITICAL GAP IDENTIFIED:**
- NO SEPARATE PLAYING XI ENDPOINT EXISTS
- Currently using SQUAD data (15-17 players per team) NOT confirmed 11
- CricketData.org API does not provide a dedicated "confirmed playing XI" endpoint
- The scorecard endpoint shows batsmen who actually played but only AFTER match starts

### 1D. Ball-by-Ball Delivery Objects
**CRITICAL GAP IDENTIFIED:**
```json
{
  "apikey": "ee437183-3bb8-4a1b-a031-6150617c2df3",
  "status": "failure",
  "reason": "ERR: Not able to get BBB for match c3a6a2f0-6c2d-495e-b46c-707022052a2f"
}
```
- Ball-by-ball endpoint (`/match_bbb`) returns FAILURE for most matches
- This is a CricketData.org API limitation on the free/basic tier
- NO REAL-TIME BALL-BY-BALL DATA AVAILABLE

---

## 2) MATCH STATE LOGIC

### Which endpoint determines match_status?
```python
# File: /app/backend/cricket_data_service.py, Lines 380-389
match_started = match.get("matchStarted", False)
match_ended = match.get("matchEnded", False)

if match_ended:
    status = "completed"
elif match_started:
    status = "live"
else:
    status = "upcoming"
```

### Which field determines toss completion?
```python
# From CricketData API raw response:
"tossWinner": "india women"
"tossChoice": "bat"
```
- Available in `/match_info` endpoint
- NOT currently used in FREE11 - we don't fetch toss data

### Which field determines confirmed lineup?
**GAP: NO CONFIRMED LINEUP FIELD**
- We use `/series/{id}/squads` endpoint which returns FULL SQUAD (15-17 players)
- NOT the confirmed playing XI (11 players)
- API does not differentiate between squad and playing XI

### Are we using squad or confirmed XI for fantasy?
**USING SQUAD** - Not confirmed XI
```python
# File: /app/backend/cricket_data_service.py
# get_match_players() fetches squad, not playing XI
response = await client.get(
    f"{CRICKET_API_BASE}/match_squad",
    params={"apikey": api_key, "id": match_id}
)
```

### When does system refresh lineup post-toss?
**NO AUTOMATIC REFRESH** - This is not implemented
- System caches squad data for 5 minutes
- No webhook/trigger for toss completion
- No logic to re-fetch lineup after toss

---

## 3) TIMESTAMP NORMALIZATION

### Are API timestamps in UTC?
**YES** - API returns `dateTimeGMT` field
```json
"dateTimeGMT": "2026-02-27T03:30:00"
```

### Where are timestamps converted to IST?
**FRONTEND ONLY** - No server-side conversion
```javascript
// File: /app/frontend/src/pages/Contests.js
// Uses browser's local timezone automatically via Date object
const startTime = new Date(match.start_time);
```

### Exact code for time conversion:
```javascript
// File: /app/frontend/src/components/MatchCard.js
// NO EXPLICIT IST CONVERSION - relies on browser locale
const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit'
  });
};
```

**GAP:** No explicit UTC→IST conversion on server or client

---

## 4) CACHING CONFIGURATION

### Cache TTL Values:
```python
# File: /app/backend/cricket_data_service.py, Lines 37-43

# Live match data
CACHE_FILE = "/tmp/cricket_api_cache.json"
CACHE_DURATION = 300  # 5 MINUTES

# Fallback cache (stale data)
FALLBACK_CACHE_FILE = "/tmp/cricket_fallback_cache.json"
FALLBACK_CACHE_DURATION = 3600  # 1 HOUR
```

### Ball-by-ball feed:
**NOT CACHED** - Ball-by-ball API is not functional

### Squad data:
**SAME 5-MINUTE CACHE** as match data

### What triggers cache invalidation?
```python
# File: /app/backend/cricket_data_service.py
def _get_cached_data(self) -> Optional[Dict]:
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                cached = json.load(f)
            cache_time = datetime.fromisoformat(cached.get('timestamp', ''))
            age = (datetime.now(timezone.utc) - cache_time).total_seconds()
            if age < CACHE_DURATION:  # 300 seconds = 5 min
                return cached
    except:
        pass
    return None  # Cache expired or invalid - triggers fresh fetch
```

**ONLY TIME-BASED EXPIRY** - No event-based invalidation

---

## 5) POLLING / REAL-TIME MECHANISM

### Polling intervals:
```javascript
// File: /app/frontend/src/pages/Contests.js, Line 326
const interval = setInterval(fetchLiveMatches, 60000);  // 60 SECONDS

// File: /app/frontend/src/pages/Cricket.js, Line 129
const interval = setInterval(fetchData, 30000);  // 30 SECONDS
```

### WebSockets or HTTP Polling?
**HTTP POLLING ONLY** - No WebSocket implementation
- Contests page: 60-second polling
- Cricket/Predict page: 30-second polling

### Is prediction lock tied to:
**(A) Frontend countdown timer** ❌ NOT IMPLEMENTED
**(B) Official ball event timestamp from API** ❌ NOT AVAILABLE

**CRITICAL GAP:** No prediction lock mechanism exists
- Ball-by-ball API doesn't work
- No countdown timer implemented
- Predictions are NOT locked before ball is bowled

---

## 6) PREDICTION LOCK INTEGRITY

### Current validation logic:
```python
# File: /app/backend/cricket_routes.py, Lines 552-556
match = await db.cricket_matches.find_one({"match_id": prediction_data.match_id})
if not match:
    raise HTTPException(status_code=404, detail="Match not found")
if match.get("status") != "live":
    raise HTTPException(status_code=400, detail="Can only predict on live matches")
```

### What determines if prediction is "late"?
**NOTHING** - No late prediction check exists

### Are we comparing prediction timestamp with API ball timestamp?
**NO** - No comparison exists

### Current prediction flow:
```python
# File: /app/backend/cricket_routes.py, Lines 579-591
prediction = BallPrediction(
    user_id=current_user.id,
    match_id=prediction_data.match_id,
    ball_number=prediction_data.ball_number,
    prediction=prediction_data.prediction
)
await db.ball_predictions.insert_one(prediction.model_dump())

# SIMULATED RESULT - NOT REAL
actual_outcomes = ['0', '1', '1', '2', '4', '6', '0', '1', 'wicket', '1', '2', '4']
actual_result = random.choice(actual_outcomes)  # RANDOM!
is_correct = prediction_data.prediction == actual_result
```

**CRITICAL:** Ball prediction results are RANDOMLY SIMULATED, not from API

---

## 7) FAILOVER LOGIC

### Current failover chain:
```python
# File: /app/backend/cricket_data_service.py

# Source 1: Primary API (CricketData.org - subscribed)
if self.primary_api_key and self._is_api_available('primary'):
    matches = await self._fetch_from_cricketdata(self.primary_api_key)

# Source 2: Sportmonks FREE tier (instant failover)
if not matches and self.sportmonks_token and self._is_api_available('sportmonks'):
    matches = await self._fetch_from_sportmonks()

# Source 3: Stale cache fallback (data < 1 hour old)
fallback = self._get_fallback_cache()
if fallback and fallback.get('matches'):
    matches = fallback['matches']

# Source 4: NO MOCK DATA - Returns empty list
return []
```

### Is licensed API failover implemented?
**YES** - Sportmonks configured as secondary
```
Primary: CricketData.org (ee437183-3bb8-4a1b-a031-6150617c2df3) ✓
Secondary: Sportmonks (18a1b8ef-5269-46b3-886c-0537a540061a) ✓
```

---

## CRITICAL GAPS IDENTIFIED

| Issue | Severity | Impact |
|-------|----------|--------|
| No Playing XI endpoint | HIGH | Fantasy shows 15+ players, not confirmed 11 |
| Ball-by-ball API broken | CRITICAL | No real-time ball data for predictions |
| Predictions use RANDOM results | CRITICAL | Not connected to actual match events |
| No prediction lock mechanism | CRITICAL | Users can predict AFTER ball is bowled |
| No toss-triggered lineup refresh | MEDIUM | Stale squad data possible |
| No UTC→IST explicit conversion | LOW | Could cause timezone bugs |
| No WebSocket implementation | MEDIUM | 30-60s delay on live updates |

---

## VERDICT

**THE MVP DATA LAYER IS NOT STABLE FOR PRODUCTION**

### Lineup-accurate: ❌ NO
- Using squad (15+ players) not confirmed XI (11 players)

### Timestamp-accurate: ⚠️ PARTIAL
- API timestamps are UTC
- No explicit IST conversion

### Over-accurate: ❌ NO
- No real ball-by-ball data
- Over/ball state is HARDCODED in frontend

### Prediction-safe: ❌ NO
- Results are RANDOMLY SIMULATED
- No prediction locking mechanism
- Users can cheat by predicting after seeing result

---

## IMMEDIATE ACTIONS REQUIRED

1. **Ball-by-Ball Data**: Either upgrade API subscription or integrate a real-time data provider that supports BBB
2. **Prediction Lock**: Implement countdown timer + backend timestamp validation
3. **Playing XI**: Fetch from scorecard endpoint once match starts (shows actual batsmen)
4. **WebSocket**: Replace polling with WebSocket for real-time updates
5. **Result Verification**: Connect prediction results to actual API ball outcomes

---

*Audit completed: February 27, 2026*
