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

## Next: Phase 4 - Closed Beta + Hardening

Now that Phase 3 exit criteria are met:
1. Enable production email (`RESEND_API_KEY`)
2. Configure monitoring alerts
3. Set `FREE11_ENV=production`
4. Onboard beta users
5. Monitor and fix issues

---

*Last updated: Feb 23, 2026*
*Phase 3 Exit: APPROVED*
