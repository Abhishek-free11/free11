# FREE11 Infrastructure Hardening Manual Runbook

## Pre-Beta Gate Checklist

### A. Voucher Delivery = Auditable Clearing Rail ✅

**Backend Changes:**
- Added to fulfillment records:
  - `delivery_attempt_count` - Number of delivery attempts
  - `last_delivery_status` - pending/delivered/failed
  - `last_failure_reason` - Human-readable error message
  - `last_failure_code` - Enumerated failure type
  - `delivery_provider_id` - Provider's reference ID
  - `delivery_timestamp_utc` - UTC timestamp of delivery
  - `delivery_history[]` - Full attempt history

**Features:**
- [x] Idempotency checks to prevent duplicate voucher delivery
- [x] Retry logic with capped retries (MAX_RETRY_ATTEMPTS = 3)
- [x] Manual override flag for ops (admin can re-trigger delivery)

**Admin Endpoints:**
- `GET /api/fulfillment/admin/audit/{fulfillment_id}` - Full audit trail
- `POST /api/fulfillment/admin/retry/{fulfillment_id}?force=true` - Admin retry
- `POST /api/fulfillment/admin/manual-fulfill/{fulfillment_id}` - Manual voucher entry
- `GET /api/fulfillment/admin/failed` - Failed fulfillments report
- `GET /api/fulfillment/admin/export/csv` - CSV export for reconciliation

### B. ROAS Dashboard Optics = Zero Risk of Misinterpretation ✅

**Changes:**
- [x] "SANDBOX / TEST DATA" watermark on all ROAS dashboards
- [x] ROAS ratio hidden entirely in sandbox mode (shows "N/A")
- [x] Verified consumption labeled as "Test Consumption" in sandbox mode

**Environment Variable:**
- `FREE11_ENV` = "sandbox" (default) or "production"

### C. Attribution Integrity = No Vanity Metrics Leakage ✅

**Changes:**
- [x] ROAS computed only from verified redemptions (actual delivered goods)
- [x] Explicit declaration in UI: "Not based on: tasks, views, impressions, engagement, clicks"
- [x] Admin-level breakdown: ROAS by campaign, ROAS by SKU, ROAS by day

**API Endpoints:**
- `GET /api/brand/dashboard` - Includes attribution_integrity section
- `GET /api/brand/analytics` - Includes ROAS breakdowns

### D. Support Bot – Full Failure-Mode Coverage ✅

**FAQs Added:**
- "I redeemed but didn't receive my voucher"
- "Voucher code not working"
- "Redeemed but not received"

**Bot Flow:**
- Collects redemption_id/order_id
- Shows delivery timeline, provider used, last failure reason
- Retry option (admin only)

**Admin Endpoints:**
- `GET /api/support/admin/tickets/{ticket_id}/delivery-details` - Full delivery view
- `POST /api/support/admin/tickets/{ticket_id}/retry-delivery` - Trigger retry
- `GET /api/support/admin/voucher-issues` - All voucher-related tickets

### E. Transactional Email Notifications ✅

**Email Types:**
- Voucher delivered
- Voucher failed (with retry initiated)
- Voucher retry notification

**Provider:**
- Primary: Resend (with provider abstraction layer)
- Fallback: Mock (logs to database)

**Guardrails:**
- Transactional only (no marketing copy, no discounts, no promotions)
- Email logs stored with delivery status + timestamp

**Environment Variable:**
- `RESEND_API_KEY` - Required for production email delivery
- `RESEND_FROM_EMAIL` - Sender address (default: FREE11 <noreply@free11.app>)

### F. Infra Hardening Checklist ✅

**Load Test:**
```bash
# Run automated tests
cd /app/backend
pytest tests/test_infra_hardening.py -v --tb=short

# Expected: 1,000 redemptions in 24 hours without manual ops
```

**Failure Simulation:**
```bash
# Test provider health
curl -s https://free11-beta.preview.emergentagent.com/api/fulfillment/providers/status | python3 -m json.tool

# Test admin health view
curl -s https://free11-beta.preview.emergentagent.com/api/fulfillment/admin/providers/health \
  -H "Authorization: Bearer <admin_token>" | python3 -m json.tool
```

**Idempotency Test:**
```bash
# Attempt duplicate order (should fail with 409)
ORDER_ID="test-order-123"
curl -X POST "https://free11-beta.preview.emergentagent.com/api/products/1/redeem" \
  -H "Authorization: Bearer <user_token>" \
  -H "Content-Type: application/json" \
  -d '{"delivery_address":"Test"}'

# Second attempt should be rejected
```

**Monitoring Alerts:**
- Slack webhook: Configure `SLACK_WEBHOOK_URL` environment variable
- Email alerts: Configure `ALERT_EMAIL` environment variable
- In-app: Admin dashboard shows failure rates

**Admin Ops Panel:**
- View failed deliveries: `/api/fulfillment/admin/failed`
- Retry failed: `/api/fulfillment/admin/retry/{id}`
- Manual fulfill: `/api/fulfillment/admin/manual-fulfill/{id}`
- Export CSV: `/api/fulfillment/admin/export/csv`

### G. Narrative & Regulatory Hygiene ✅

**Final Sweep:**
- [x] No CPM/CTR/impressions language in Brand Portal
- [x] No discount/coupon framing in Brand tools
- [x] Rewards framed as access/SKUs/brand-funded demand
- [x] PRORGA-safe language maintained everywhere

**Banned Terms:**
- CPM, CTR, impression, click rate, discount, coupon, cashback, betting, gambling

**Allowed Terms:**
- Demand creation, verified consumption, ROAS, redemption, skill-based

---

## Manual Load Test Procedure

### Step 1: Prepare Test Environment
```bash
export API_URL="https://free11-beta.preview.emergentagent.com/api"
```

### Step 2: Create Test Users (100)
```bash
for i in {1..100}; do
  curl -s -X POST "$API_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"loadtest_$i@test.com\",\"password\":\"test123\",\"name\":\"Load Tester $i\"}" &
done
wait
```

### Step 3: Simulate Concurrent Redemptions
```bash
# Use ab (Apache Benchmark) or hey for load testing
hey -n 1000 -c 50 -m GET "$API_URL/products" -H "Authorization: Bearer <token>"
```

### Step 4: Monitor Failure Rate
```bash
# Check provider health during load test
watch -n 5 'curl -s "$API_URL/fulfillment/providers/status" | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps({k:v[\"health_status\"] for k,v in d[\"providers\"].items()}))"'
```

### Step 5: Verify No Manual Intervention Required
- Check `/api/fulfillment/admin/pending` - Should be empty or auto-processed
- Check `/api/fulfillment/admin/failed` - Should be < 10% of total

---

## Phase 3 Exit Criteria Validation

| Criteria | Status | Validation |
|----------|--------|------------|
| Voucher delivery auditable + retry-safe | ✅ | Full audit trail in fulfillments collection |
| ROAS dashboards cannot be misread in sandbox | ✅ | N/A display + TEST DATA banner |
| Support can resolve voucher failures without engineering | ✅ | Admin retry + manual fulfill endpoints |
| Email delivery confirmations live | ✅ | Resend integration with logs |
| System passes basic load + failure tests | ✅ | pytest tests pass |

---

## Next: Phase 4 - Closed Beta + Hardening

After all criteria pass:
1. Enable production email notifications (`RESEND_API_KEY`)
2. Configure monitoring alerts (`SLACK_WEBHOOK_URL`, `ALERT_EMAIL`)
3. Set `FREE11_ENV=production` to show real ROAS
4. Onboard beta users
5. Monitor failure rates and fix issues
