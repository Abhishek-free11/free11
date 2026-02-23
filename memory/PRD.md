# FREE11 - Cricket Prediction & Demand Rail Platform

## Original Problem Statement
Build a cricket prediction and engagement platform for capturing 60 million displaced RMG users in India. Designed as a "Demand Rail Engine" where users convert skill (cricket predictions) into coins, redeemable for brand-funded real goods.

## Core Product Thesis
- **Demand Rail Engine**: Cricket prediction is PRIMARY, ads/mini-games are secondary boosters
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

*Last updated: Feb 23, 2026*
*Phase 3 Exit: APPROVED*
*Phase 4: IN PROGRESS*
