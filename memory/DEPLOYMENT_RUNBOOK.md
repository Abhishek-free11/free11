# FREE11 Production Deployment Runbook
**Version**: 1.0 – T20 Season 2026 RC Release Candidate  
**Date**: March 2026  
**Environment**: Production (free11.com)  
**Assumptions**: PRD finalized; all mocks (ONDC, Xoxoday) in place; live integrations post-RC.

---

## 1. Pre-Deployment Checklist
- [ ] Confirm Resend domain verification complete at https://resend.com/domains (for live email OTP; fallback inline code already implemented).
- [ ] Verify .env secrets: EntitySport key, Gemini/Emergent LLM, Razorpay test keys (to be swapped), Firebase service account, AdMob keys, FCM server key, Mongo Atlas URI (authSource=admin fixed).
- [ ] Run final E2E tests (92%+ coverage): Landing load, SEO schemas, Blog keywords, Google login, Prediction flow, Quest completion + coin animation, Redemption success + ShareCard, Admin forecast + breakage KPI.
- [ ] Smoke test locally/staging: PWA install prompt, Framer Motion animations, SkillDisclaimerModal on 6 surfaces, expiry countdown in Wallet.
- [ ] Backup current production DB (if any) + Redis cache.
- [ ] Confirm domain DNS: free11.com points to hosting (Vercel/Netlify for frontend; Render/Fly.io/Railway for backend).

---

## 2. Deployment Steps

### Backend (FastAPI)
1. Pull latest main branch.
2. Build Docker image (if containerized) or direct deploy.
3. Deploy to production host:
   - Update env vars: switch `RAZORPAY_MODE=live` (after key swap below).
   - Restart services: `uvicorn server:app --host 0.0.0.0 --port $PORT`
4. Run APScheduler seeding if needed (sponsored pools, SKUs).

### Frontend (React PWA/TWA)
1. `yarn build`
2. Deploy static build to Vercel / Netlify / CDN.
3. Verify `index.html` meta/OG tags are intact (SEO, JSON-LD, font preloads).
4. For Android TWA: rebuild with latest SHA-256 fingerprint.

### Key Config Swaps

#### Razorpay (Test → Live)
- Replace `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` in `.env` with live keys.
- Redeploy backend.
- Test a minimal FREE Bucks purchase (₹1 or lowest denomination) end-to-end.

#### assetlinks.json (Android TWA Verified Links)
```bash
keytool -list -v -keystore your_keystore.jks -alias your_alias
```
- Copy the `SHA-256` fingerprint.
- Update `frontend/public/.well-known/assetlinks.json`:
```json
[{
  "relation": ["delegate_permission/common.handle_all_urls"],
  "target": {
    "namespace": "android_app",
    "package_name": "com.free11.app",
    "sha256_cert_fingerprints": ["YOUR_SHA256_HERE"]
  }
}]
```
- Redeploy frontend.

#### Firebase FCM
- Confirm `firebase@12.10.0` in `package.json` (already done).
- Run push campaign dry-run: `POST /api/v2/push/campaign` with `dry_run: true`.
- Confirm FCM delivery via Firebase Console → Cloud Messaging.

#### Resend DNS Verification
- Go to https://resend.com/domains
- Add the provided TXT/MX/DKIM records to your DNS (Cloudflare / GoDaddy / Route 53).
- Verification typically takes 5–30 minutes.
- Once verified, OTPs will deliver via email (inline fallback code still available as backup).

---

## 3. Post-Deployment Smoke Tests
- [ ] Access https://free11.com — verify PWA install banner, hero carousel, tagline "Play Cricket. Earn Essentials."
- [ ] Register via OTP (email delivery) + Google OAuth login.
- [ ] Make a prediction → earn coins → confirm expiry countdown visible in Wallet.
- [ ] Complete quest → confirm SkillBadge + ShareCard appear.
- [ ] Redeem a small SKU → confirm QR voucher + "Powered by Zepto/ONDC" branding + ShareCard.
- [ ] Trigger SkillDisclaimerModal on all 6 surfaces: Shop, Sponsored Pools, Quest modal, Predict, LiveMatch, Landing footer.
- [ ] Admin login (admin@free11.com) → verify KPIs (breakage ratio, ARR forecast chart).
- [ ] Monitor Sentry dashboard for new errors.
- [ ] Check Redis cache hit rate for Router and Crowd Meter endpoints.

---

## 4. Rollback Plan
1. Revert to previous git tag/branch via Emergent "Rollback" or CI/CD.
2. Restore MongoDB backup (`mongorestore`).
3. Revert `.env` to test keys.
4. Redeploy previous Docker image / static build.

---

## 5. Post-Launch Monitoring (First 7 Days)

| Metric | Tool | Target |
|--------|------|--------|
| Error rate | Sentry | < 0.5% |
| API latency (p95) | Sentry / logs | < 800ms |
| DAU / Retention | Mixpanel / GA4 | 30%+ D7 |
| Redemption rate | AdminV2 KPIs | > 5% of coin earners |
| Breakage ratio | AdminV2 KPIs | > 10% |
| OTP delivery rate | Resend dashboard | > 95% |
| FCM delivery | Firebase Console | > 90% |

**Actions:**
- Day 1: Run FCM push campaign — "Predict live match!" dry-run → real send.
- Day 3: Check Resend bounce/complaint rates; suppress problematic domains.
- Day 7: Review breakage KPI and ARR forecast in AdminV2; adjust coin expiry nudge copy if <10% breakage.

---

## 6. Go-Live Communication

- **Internal:** Slack / team announce once smoke tests pass.
- **Soft launch:** No public announcement until live integrations tested (Xoxoday, ONDC real API).
- **Hard launch:** Full T20 Season 2026 marketing push (YouTube Shorts, Telegram, WhatsApp loops) once Xoxoday redemption and ONDC router are live.
- **Legal watch:** Monitor Supreme Court updates on Online Gaming Act, 2025; update `SkillDisclaimerModal` text if new rules notified.

---

## 7. Post-RC Live Integration Queue (P1)

| Integration | Action Required | Owner |
|-------------|----------------|-------|
| Xoxoday | Share API key + catalog CSV | Abhishek |
| ONDC Router | Replace mock in `router_service.py` with real BAP endpoint | Dev |
| Resend DNS | Add TXT/DKIM records to DNS provider | Abhishek |
| Razorpay Live | Swap keys in `.env` + test ₹1 purchase | Abhishek |
| Play Store TWA | Sign APK, generate SHA-256, submit to Play Console | Dev |
| Professional translations | Share translated strings for 8 locales | Abhishek |

---

**Owner**: Abhishek (Mumbai)  
**Runbook version**: 1.0  
**Last updated**: March 9, 2026  
**Next review**: After Xoxoday + ONDC live integration (estimated April 2026)
