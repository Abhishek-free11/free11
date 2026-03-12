"""
FCM Campaign Scheduler for FREE11
===================================
Auto-triggered push notification campaigns:
 1. Match starting in 30 mins → predict now
 2. Coin expiry warning → 7 days before expiry
 3. Streak at-risk → user hasn't logged in for 23+ hours (daily at 8 PM IST)
 4. Quest available → daily at 9 AM IST (users who haven't claimed today)

Called from APScheduler jobs registered in server.py
"""
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

IST_OFFSET = timedelta(hours=5, minutes=30)


async def send_match_starting_campaign(db, fcm_service):
    """Push to all users who have predictions in matches starting in 30-60 mins."""
    try:
        now = datetime.now(timezone.utc)
        window_start = now + timedelta(minutes=25)
        window_end   = now + timedelta(minutes=65)

        # Find matches starting in the window
        matches = await db.matches.find({
            "start_time": {"$gte": window_start.isoformat(), "$lte": window_end.isoformat()},
            "status": {"$in": ["upcoming", "scheduled"]},
        }, {"_id": 0, "id": 1, "team1": 1, "team2": 1}).to_list(10)

        if not matches:
            return

        # Collect all users who have FCM tokens
        tokens = await db.fcm_tokens.find({}, {"_id": 0, "token": 1, "user_id": 1}).to_list(10000)
        if not tokens:
            return

        for match in matches:
            t1 = match.get("team1", "Team A")
            t2 = match.get("team2", "Team B")
            title = f"Match Starting Soon! 🏏"
            body  = f"{t1} vs {t2} — Make your prediction now and earn coins!"

            all_tokens = [t["token"] for t in tokens if t.get("token")]
            if all_tokens:
                await fcm_service.send_bulk(
                    tokens=all_tokens[:500],
                    title=title,
                    body=body,
                    data={"type": "match_starting", "match_id": match.get("id", "")},
                )
                logger.info("Match-starting campaign sent: %s tokens for match %s", len(all_tokens[:500]), match.get("id"))
    except Exception as e:
        logger.error("match_starting campaign error: %s", e)


async def send_coin_expiry_campaign(db, fcm_service):
    """Push to users whose coins expire in exactly 7 days."""
    try:
        now        = datetime.now(timezone.utc)
        target_day = (now + timedelta(days=7)).date().isoformat()

        users = await db.users.find(
            {"coin_expiry_date": {"$regex": f"^{target_day}"}},
            {"_id": 0, "id": 1, "coins_balance": 1},
        ).to_list(5000)

        if not users:
            return

        user_ids = [u["id"] for u in users]
        tokens   = await db.fcm_tokens.find(
            {"user_id": {"$in": user_ids}},
            {"_id": 0, "token": 1},
        ).to_list(5000)

        all_tokens = [t["token"] for t in tokens if t.get("token")]
        if not all_tokens:
            return

        await fcm_service.send_bulk(
            tokens=all_tokens[:500],
            title="Your coins expire in 7 days! ⏰",
            body="Redeem your FREE Coins for Flipkart vouchers, Uber credits, and more before they expire.",
            data={"type": "coin_expiry", "days_left": "7"},
        )
        logger.info("Coin-expiry campaign sent: %s users", len(all_tokens))
    except Exception as e:
        logger.error("coin_expiry campaign error: %s", e)


async def send_streak_reminder_campaign(db, fcm_service):
    """Push to users who haven't logged in for 23+ hours (streak at risk)."""
    try:
        now      = datetime.now(timezone.utc)
        cutoff   = now - timedelta(hours=23)

        users = await db.users.find(
            {
                "last_login": {"$lt": cutoff.isoformat(), "$gt": (now - timedelta(days=2)).isoformat()},
                "streak_days": {"$gte": 2},
            },
            {"_id": 0, "id": 1, "streak_days": 1},
        ).to_list(5000)

        if not users:
            return

        user_ids = [u["id"] for u in users]
        tokens   = await db.fcm_tokens.find(
            {"user_id": {"$in": user_ids}},
            {"_id": 0, "token": 1, "user_id": 1},
        ).to_list(5000)

        # Personalise per user using their streak
        streak_map = {u["id"]: u["streak_days"] for u in users}
        for t in tokens[:500]:
            uid   = t.get("user_id", "")
            days  = streak_map.get(uid, 2)
            await fcm_service.send_single(
                token=t["token"],
                title=f"🔥 {days}-day streak at risk!",
                body="Log in now to keep your prediction streak alive and earn bonus coins.",
                data={"type": "streak_reminder", "streak_days": str(days)},
            )

        logger.info("Streak-reminder campaign sent: %s users", len(tokens[:500]))
    except Exception as e:
        logger.error("streak_reminder campaign error: %s", e)


async def send_quest_available_campaign(db, fcm_service):
    """Push to users who haven't claimed today's quest yet."""
    try:
        today = datetime.now(timezone.utc).date().isoformat()

        # Users who claimed yesterday but not today (active users worth nudging)
        claimed_today_ids = set(
            r["user_id"] for r in
            await db.quest_sessions.find(
                {"date": today, "status": "completed"},
                {"_id": 0, "user_id": 1},
            ).to_list(50000)
        )

        tokens = await db.fcm_tokens.find(
            {"user_id": {"$nin": list(claimed_today_ids)}},
            {"_id": 0, "token": 1},
        ).to_list(5000)

        all_tokens = [t["token"] for t in tokens if t.get("token")]
        if not all_tokens:
            return

        await fcm_service.send_bulk(
            tokens=all_tokens[:500],
            title="Daily Quest available! ⚡",
            body="Watch a quick ad or grab today's grocery deal — earn up to 20 bonus coins.",
            data={"type": "quest_available"},
        )
        logger.info("Quest-available campaign sent: %s tokens", len(all_tokens[:500]))
    except Exception as e:
        logger.error("quest_available campaign error: %s", e)
