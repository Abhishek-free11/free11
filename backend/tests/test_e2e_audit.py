"""
FREE11 — FULL SYSTEM E2E TEST SUITE
Comprehensive breakage audit across all modules.
"""
import asyncio
import httpx
import json
import time
import uuid
import sys
from datetime import datetime

API = "http://localhost:8001/api"
RESULTS = {"pass": 0, "fail": 0, "tests": []}

def record(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    RESULTS["pass" if passed else "fail"] += 1
    RESULTS["tests"].append({"name": name, "status": status, "detail": detail})
    print(f"  [{status}] {name}" + (f" — {detail}" if detail and not passed else ""))


async def run_all():
    async with httpx.AsyncClient(timeout=15, base_url=API) as c:
        print("\n" + "="*60)
        print("PHASE 1: CORE AUTH & USER FLOW")
        print("="*60)

        # 1.1 Health check
        r = await c.get("/health")
        record("Health check returns 200", r.status_code == 200)
        if r.status_code == 200:
            d = r.json()
            record("Health: Redis connected", d.get("redis") == True, str(d))
            record("Health: Production env", d.get("env") == "production", d.get("env"))

        # 1.2 Registration (fresh user)
        test_email = f"audit_{uuid.uuid4().hex[:8]}@test.com"
        r = await c.post("/auth/register", json={
            "email": test_email, "name": "Audit User", "password": "AuditPass@1",
            "date_of_birth": "2000-01-01", "invite_code": "ADMIN-MASTER"
        })
        record("Fresh user registration", r.status_code == 200, r.text[:100] if r.status_code != 200 else "")
        if r.status_code == 200:
            d = r.json()
            test_token = d.get("access_token", "")
            test_user_id = d.get("user", {}).get("id", "")
            record("Registration returns token", bool(test_token))
            record("Registration returns user ID", bool(test_user_id))
            record("Welcome bonus in response", d.get("user", {}).get("coins_balance", 0) >= 50,
                   f"coins={d.get('user',{}).get('coins_balance')}")
        else:
            test_token = ""
            test_user_id = ""

        # 1.3 Login
        r = await c.post("/auth/login", json={"email": "admin@free11.com", "password": "Admin@123"})
        record("Admin login succeeds", r.status_code == 200)
        admin_token = r.json().get("access_token", "") if r.status_code == 200 else ""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        test_headers = {"Authorization": f"Bearer {test_token}"}

        # 1.4 Login returns no password hashes
        if r.status_code == 200:
            user_data = r.json().get("user", {})
            record("No password_hash in response", "password_hash" not in user_data)
            record("No hashed_password in response", "hashed_password" not in user_data)

        # 1.5 Auth/me
        r = await c.get("/auth/me", headers=admin_headers)
        record("Auth/me returns user", r.status_code == 200 and "email" in r.json())

        # 1.6 Device fingerprint recorded
        from pymongo import MongoClient
        mc = MongoClient("mongodb://localhost:27017")
        db = mc["free11_db"]
        login_event = db.login_events.find_one({"user_id": r.json().get("id", "")}, sort=[("timestamp", -1)])
        record("Device fingerprint recorded on login", login_event is not None and "device_hash" in (login_event or {}))

        # 1.7 Invalid login
        r = await c.post("/auth/login", json={"email": "admin@free11.com", "password": "wrong"})
        record("Wrong password returns 401", r.status_code == 401)

        # 1.8 Banned user test
        if test_user_id:
            db.users.update_one({"id": test_user_id}, {"$set": {"banned": True, "ban_reason": "audit test"}})
            r = await c.post("/auth/login", json={"email": test_email, "password": "AuditPass@1"})
            record("Banned user gets 403", r.status_code == 403, f"got {r.status_code}")
            db.users.update_one({"id": test_user_id}, {"$unset": {"banned": 1, "ban_reason": 1}})

        print("\n" + "="*60)
        print("PHASE 2: ENTITYSPORT & MATCH ENGINE")
        print("="*60)

        # 2.1 Match listing
        r = await c.get("/v2/es/matches?status=1&per_page=5")
        record("Upcoming matches returns 200", r.status_code == 200)
        matches = r.json() if r.status_code == 200 else []
        record("Upcoming matches returns array", isinstance(matches, list))
        if matches:
            record("Match has required fields", all(k in matches[0] for k in ["match_id","team1","team2","status"]))

        # 2.2 Caching verification
        t1 = time.time()
        await c.get("/v2/es/matches?status=1&per_page=5")
        first = time.time() - t1
        t2 = time.time()
        await c.get("/v2/es/matches?status=1&per_page=5")
        second = time.time() - t2
        record("Cache reduces latency (2nd call faster)", second < first, f"first={first:.3f}s, second={second:.3f}s")

        # 2.3 Completed matches
        r = await c.get("/v2/es/matches?status=2&per_page=5")
        record("Completed matches returns 200", r.status_code == 200)

        # 2.4 Match info (use a known completed match)
        completed = r.json() if r.status_code == 200 else []
        if completed:
            mid = completed[0].get("match_id", "")
            r = await c.get(f"/v2/es/match/{mid}/info")
            record("Match info returns data", r.status_code == 200)
            r = await c.get(f"/v2/es/match/{mid}/scorecard")
            record("Match scorecard returns data", r.status_code == 200)

        print("\n" + "="*60)
        print("PHASE 3: WALLET & ECONOMY")
        print("="*60)

        # 3.1 Coins balance
        r = await c.get("/coins/balance", headers=test_headers)
        record("Coins balance endpoint", r.status_code == 200)

        # 3.2 Ledger balance
        r = await c.get("/v2/ledger/balance", headers=test_headers)
        record("Ledger V2 balance", r.status_code == 200)

        # 3.3 FREE Bucks balance
        r = await c.get("/v2/freebucks/balance", headers=test_headers)
        record("FREE Bucks balance", r.status_code == 200)
        fb_balance = r.json().get("balance", 0) if r.status_code == 200 else -1
        record("FREE Bucks starts at 0", fb_balance == 0)

        # 3.4 FREE Bucks packages
        r = await c.get("/v2/freebucks/packages")
        record("FREE Bucks packages returns 3", r.status_code == 200 and len(r.json()) == 3)

        # 3.5 Coins transactions
        r = await c.get("/coins/transactions", headers=test_headers)
        record("Coin transactions endpoint", r.status_code == 200)

        # 3.6 Daily check-in
        r = await c.post("/coins/checkin", headers=test_headers)
        record("Daily check-in works", r.status_code == 200, r.text[:100] if r.status_code != 200 else "")

        print("\n" + "="*60)
        print("PHASE 4: FEATURE GATING")
        print("="*60)

        # 4.1 List gated features
        r = await c.get("/v2/features/gated")
        record("Gated features list returns 3", r.status_code == 200 and len(r.json()) == 3)

        # 4.2 Check access (should be denied - no FREE Bucks)
        r = await c.get("/v2/features/check/ad_free_join", headers=test_headers)
        record("Feature check: denied when no bucks", r.status_code == 200 and r.json().get("allowed") == False)

        # 4.3 Use feature (should fail)
        r = await c.post("/v2/features/use", json={"feature": "ad_free_join"}, headers=test_headers)
        record("Feature use: fails without bucks", r.status_code == 402)

        print("\n" + "="*60)
        print("PHASE 5: CONTEST & PREDICTION ENGINE")
        print("="*60)

        # 5.1 Create contest
        r = await c.post("/v2/contests/create", json={
            "match_id": "audit_test", "name": "Audit Contest", "contest_type": "mega",
            "entry_fee": 0, "max_entries": 100, "prize_pool": 500
        }, headers=admin_headers)
        record("Contest creation", r.status_code == 200)
        contest_id = r.json().get("id", "") if r.status_code == 200 else ""

        # 5.2 Join contest
        if contest_id:
            r = await c.post("/v2/contests/join", json={"contest_id": contest_id}, headers=test_headers)
            record("Contest join", r.status_code == 200, r.text[:100] if r.status_code != 200 else "")

            # 5.3 Duplicate join should fail
            r = await c.post("/v2/contests/join", json={"contest_id": contest_id}, headers=test_headers)
            record("Duplicate contest join blocked", r.status_code != 200, f"status={r.status_code}")

        # 5.4 Prediction types
        r = await c.get("/v2/predictions/types")
        record("Prediction types returns data", r.status_code == 200 and len(r.json()) > 0)

        # 5.5 My contests
        r = await c.get("/v2/contests/user/my", headers=test_headers)
        record("My contests returns list", r.status_code == 200)

        print("\n" + "="*60)
        print("PHASE 6: CARDS & POWER-UPS")
        print("="*60)

        r = await c.get("/v2/cards/types")
        record("Card types returns data", r.status_code == 200 and len(r.json()) > 0)

        r = await c.get("/v2/cards/inventory", headers=test_headers)
        record("Card inventory returns list", r.status_code == 200)

        print("\n" + "="*60)
        print("PHASE 7: NOTIFICATIONS")
        print("="*60)

        r = await c.get("/v2/notifications", headers=test_headers)
        record("Notifications endpoint", r.status_code == 200)
        if r.status_code == 200:
            d = r.json()
            record("Notifications has unread_count", "unread_count" in d)
            record("Notifications has array", isinstance(d.get("notifications"), list))

        print("\n" + "="*60)
        print("PHASE 8: REFERRAL SYSTEM")
        print("="*60)

        r = await c.get("/v2/referral/code", headers=test_headers)
        record("Referral code generation", r.status_code == 200 and "code" in r.json())

        r = await c.get("/v2/referral/stats", headers=test_headers)
        record("Referral stats", r.status_code == 200)

        print("\n" + "="*60)
        print("PHASE 9: SECURITY — AUTH BYPASS TESTS")
        print("="*60)

        # 9.1 No-auth access to protected endpoints
        for ep in ["/v2/ledger/balance", "/v2/freebucks/balance", "/v2/cards/inventory",
                    "/v2/notifications", "/auth/me", "/v2/contests/user/my"]:
            r = await c.get(ep)
            record(f"No-auth blocked: {ep}", r.status_code in (401, 403, 422), f"got {r.status_code}")

        # 9.2 Admin endpoint without admin role
        r = await c.get("/admin/v2/fraud/flagged", headers=test_headers)
        record("Non-admin blocked from fraud panel", r.status_code == 403, f"got {r.status_code}")

        r = await c.post("/admin/v2/wallet/adjust", json={"user_id": "x", "amount": 999, "reason": "hack"},
                         headers=test_headers)
        record("Non-admin blocked from wallet adjust", r.status_code == 403, f"got {r.status_code}")

        # 9.3 Fake token
        fake_headers = {"Authorization": "Bearer fake.token.here"}
        r = await c.get("/auth/me", headers=fake_headers)
        record("Fake token rejected", r.status_code == 401, f"got {r.status_code}")

        print("\n" + "="*60)
        print("PHASE 10: RATE LIMITING")
        print("="*60)

        # 10.1 Auth rate limit (5/min)
        statuses = []
        for i in range(8):
            r = await c.post("/auth/login", json={"email": "admin@free11.com", "password": "Admin@123"})
            statuses.append(r.status_code)
        blocked = [s for s in statuses if s == 429]
        record("Auth rate limit triggers 429", len(blocked) > 0, f"statuses={statuses}")

        print("\n" + "="*60)
        print("PHASE 11: PAYMENT INTEGRATION")
        print("="*60)

        # 11.1 Payment packages
        r = await c.get("/payments/packages")
        record("Payment packages returns data", r.status_code == 200)

        # 11.2 Payment checkout (test mode)
        r = await c.post("/payments/checkout", json={
            "package_id": "starter", "origin_url": "https://play-store-launch-4.preview.emergentagent.com"
        }, headers=admin_headers)
        record("Stripe checkout creates session", r.status_code == 200 and "url" in r.json(),
               r.text[:150] if r.status_code != 200 else "")

        # 11.3 Invalid package
        r = await c.post("/payments/checkout", json={
            "package_id": "invalid_pkg", "origin_url": "http://localhost"
        }, headers=admin_headers)
        record("Invalid package rejected", r.status_code == 400)

        # 11.4 Payment without auth
        r = await c.post("/payments/checkout", json={"package_id": "starter", "origin_url": "http://localhost"})
        record("Payment without auth rejected", r.status_code == 401)

        print("\n" + "="*60)
        print("PHASE 12: ADMIN PANEL")
        print("="*60)

        r = await c.get("/admin/v2/feature-flags", headers=admin_headers)
        record("Admin: feature flags", r.status_code == 200)

        r = await c.get("/admin/v2/action-log?limit=5", headers=admin_headers)
        record("Admin: action log", r.status_code == 200)

        r = await c.get("/admin/v2/fraud/flagged", headers=admin_headers)
        record("Admin: fraud flagged users", r.status_code == 200)

        r = await c.get("/v2/analytics/dashboard", headers=admin_headers)
        record("Admin: analytics dashboard", r.status_code == 200)
        if r.status_code == 200:
            d = r.json()
            record("Analytics has total_users", "total_users" in d)
            record("Analytics has DAU", "dau" in d)

        r = await c.get("/v2/cache/stats", headers=admin_headers)
        record("Admin: cache stats", r.status_code == 200)

        print("\n" + "="*60)
        print("PHASE 13: CHAOS — GRACEFUL FAILURE TESTS")
        print("="*60)

        # 13.1 Invalid match ID
        r = await c.get("/v2/es/match/99999999/info")
        record("Invalid match ID handled gracefully", r.status_code in (404, 200))

        # 13.2 Invalid contest ID
        r = await c.get("/v2/contests/nonexistent-id")
        record("Invalid contest ID handled", r.status_code in (404, 200))

        # 13.3 Empty predictions
        r = await c.get("/v2/predictions/my", headers=test_headers)
        record("Empty predictions returns list", r.status_code == 200)

        print("\n" + "="*60)
        print("PHASE 14: DATA INTEGRITY")
        print("="*60)

        # 14.1 Check for negative balances
        neg_coins = db.users.count_documents({"coins_balance": {"$lt": 0}})
        record("No negative coin balances", neg_coins == 0, f"found {neg_coins}")

        # 14.2 Check for orphaned transactions
        user_ids = set(u["id"] for u in db.users.find({}, {"id": 1, "_id": 0}))
        orphan_txns = db.ledger.count_documents({"user_id": {"$nin": list(user_ids)}})
        record("No orphaned ledger entries", orphan_txns == 0, f"found {orphan_txns}")

        # 14.3 Check user count consistency
        total_users = db.users.count_documents({})
        record("Users collection has data", total_users > 0, f"count={total_users}")

        # 14.4 No duplicate emails
        pipeline = [{"$group": {"_id": "$email", "count": {"$sum": 1}}}, {"$match": {"count": {"$gt": 1}}}]
        dupes = list(db.users.aggregate(pipeline))
        record("No duplicate email addresses", len(dupes) == 0, f"dupes={dupes}")

        # Cleanup test user
        if test_user_id:
            db.users.delete_one({"id": test_user_id})

        mc.close()

    # ─── FINAL REPORT ───
    print("\n" + "="*60)
    print("FINAL AUDIT REPORT")
    print("="*60)
    total = RESULTS["pass"] + RESULTS["fail"]
    print(f"Total tests: {total}")
    print(f"PASSED: {RESULTS['pass']}")
    print(f"FAILED: {RESULTS['fail']}")
    print(f"Pass rate: {round(RESULTS['pass']/total*100, 1)}%")

    if RESULTS["fail"] > 0:
        print("\n--- FAILURES ---")
        for t in RESULTS["tests"]:
            if t["status"] == "FAIL":
                print(f"  FAIL: {t['name']} — {t['detail']}")

    # Save report
    with open("/app/test_reports/e2e_audit.json", "w") as f:
        json.dump(RESULTS, f, indent=2)
    print(f"\nReport saved: /app/test_reports/e2e_audit.json")


if __name__ == "__main__":
    asyncio.run(run_all())
