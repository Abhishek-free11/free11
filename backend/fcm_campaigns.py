"""
FCM Campaign Scheduler for FREE11
===================================
Auto-triggered push notification campaigns:
 1. Match starting in 30 mins → predict now
 2. Coin expiry warning → 7 days before expiry
 3. Streak at-risk → 3+ day streak, 20h inactivity (fires 20:00 + 22:00 IST)
 4. Quest available → daily at 9 AM IST
 5. [NEW] Activation trigger → registered 20-28h ago, 0 predictions

Called from APScheduler jobs registered in server.py / scheduler_service.py
"""
import logging
import uuid
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

IST_OFFSET = timedelta(hours=5, minutes=30)


async def _store_in_app(db, user_id: str, notif_type: str, title: str, body: str, deep_link: str = "/"):
    """Persist notification to db.notifications so in-app bell shows it too."""
    try:
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": notif_type,
            "title": title,
            "body": body,
            "deep_link": deep_link,
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        logger.warning("in-app store failed for %s: %s", user_id, e)


async def send_match_starting_campaign(db, fcm_service):
    """Push to all users who have predictions in matches starting in 30-60 mins."""
    try:
        now = datetime.now(timezone.utc)
        window_start = now + timedelta(minutes=25)
        window_end   = now + timedelta(minutes=65)

        matches = await db.matches.find({
            "start_time": {"$gte": window_start.isoformat(), "$lte": window_end.isoformat()},
            "status": {"$in": ["upcoming", "scheduled"]},
        }, {"_id": 0, "id": 1, "team1": 1, "team2": 1}).to_list(10)

        if not matches:
            return

        tokens = await db.fcm_tokens.find({}, {"_id": 0, "token": 1, "user_id": 1}).to_list(10000)
        if not tokens:
            return

        for match in matches:
            t1 = match.get("team1", "Team A")
            t2 = match.get("team2", "Team B")
            title = "Match Starting Soon! 🏏"
            body  = f"{t1} vs {t2} — Make your prediction now and earn coins!"
            all_tokens = [t["token"] for t in tokens if t.get("token")]
            if all_tokens:
                await fcm_service.send_bulk(
                    tokens=all_tokens[:500],
                    title=title, body=body,
                    data={"type": "match_starting", "match_id": match.get("id", ""), "deep_link": "/match-centre"},
                )
                logger.info("Match-starting campaign sent: %s tokens", len(all_tokens[:500]))
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
            {"user_id": {"$in": user_ids}}, {"_id": 0, "token": 1, "user_id": 1},
        ).to_list(5000)

        all_tokens = [t["token"] for t in tokens if t.get("token")]
        if all_tokens:
            await fcm_service.send_bulk(
                tokens=all_tokens[:500],
                title="Your coins expire in 7 days! ⏰",
                body="Redeem your FREE Coins for Flipkart vouchers, Uber credits, and more before they expire.",
                data={"type": "coin_expiry", "days_left": "7", "deep_link": "/shop"},
            )

        # Also store in-app for each user
        for uid in user_ids[:200]:
            await _store_in_app(db, uid, "coin_expiry",
                "Your coins expire in 7 days! ⏰",
                "Redeem for vouchers and groceries before they expire.",
                "/shop")

        logger.info("Coin-expiry campaign sent: %s users", len(user_ids))
    except Exception as e:
        logger.error("coin_expiry campaign error: %s", e)


async def send_streak_reminder_campaign(db, fcm_service):
    """
    Push to users whose streak is at risk.
    Upgraded: requires 3+ day streak and 20h inactivity window for high urgency.
    Personalises copy with exact hours remaining before streak resets.
    """
    try:
        now    = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=20)   # Inactive for 20+ hours
        # Streak resets at midnight UTC — calculate hours until reset
        midnight_utc = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        hours_left   = int((midnight_utc - now).total_seconds() / 3600)

        users = await db.users.find(
            {
                "last_login":   {"$lt": cutoff.isoformat(), "$gt": (now - timedelta(days=2)).isoformat()},
                "streak_days":  {"$gte": 3},   # Only meaningful streaks (3+)
            },
            {"_id": 0, "id": 1, "streak_days": 1, "name": 1},
        ).to_list(5000)

        if not users:
            logger.info("Streak-reminder: no at-risk users found")
            return

        user_ids  = [u["id"] for u in users]
        streak_map = {u["id"]: (u.get("streak_days", 3), u.get("name", "")) for u in users}

        tokens = await db.fcm_tokens.find(
            {"user_id": {"$in": user_ids}}, {"_id": 0, "token": 1, "user_id": 1},
        ).to_list(5000)

        for t in tokens[:500]:
            uid   = t.get("user_id", "")
            days, name = streak_map.get(uid, (3, ""))
            first = name.split()[0] if name else ""
            title = f"🔥 {days}-day streak breaks in {hours_left}h!"
            body  = (
                f"{'Hey ' + first + ', your' if first else 'Your'} {days}-day prediction streak "
                f"expires in {hours_left} hours. Log in and keep it alive!"
            )
            await fcm_service.send_single(
                token=t["token"], title=title, body=body,
                data={"type": "streak_reminder", "streak_days": str(days),
                      "hours_left": str(hours_left), "deep_link": "/dashboard"},
            )
            await _store_in_app(db, uid, "streak_reminder", title, body, "/dashboard")

        logger.info("Streak-reminder campaign sent: %s users (%sh left)", len(tokens[:500]), hours_left)
    except Exception as e:
        logger.error("streak_reminder campaign error: %s", e)


async def send_quest_available_campaign(db, fcm_service):
    """Push to users who haven't claimed today's quest yet."""
    try:
        today = datetime.now(timezone.utc).date().isoformat()

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
            data={"type": "quest_available", "deep_link": "/earn"},
        )
        logger.info("Quest-available campaign sent: %s tokens", len(all_tokens[:500]))
    except Exception as e:
        logger.error("quest_available campaign error: %s", e)


async def send_activation_trigger_campaign(db, fcm_service):
    """
    [NEW] Activation trigger: fire when a user registered 20-28h ago but has
    made zero predictions. The goal is to convert them before Day-2 churn.

    Fires: every hour (scheduler checks), so users hit exactly once in their 20-28h window.
    """
    try:
        now         = datetime.now(timezone.utc)
        window_end  = now - timedelta(hours=20)   # Registered at least 20h ago
        window_start = now - timedelta(hours=28)  # But no more than 28h ago (avoid repeat)

        # Find users who registered in the window, haven't predicted, and haven't been sent this push
        # Use a "activation_push_sent" flag to avoid repeat fires
        at_risk_users = await db.users.find(
            {
                "created_at":             {"$gte": window_start.isoformat(), "$lte": window_end.isoformat()},
                "total_predictions":      {"$in": [0, None]},
                "activation_push_sent":   {"$ne": True},
                "is_admin":               {"$ne": True},
                "is_seed":                {"$ne": True},
            },
            {"_id": 0, "id": 1, "name": 1, "coins_balance": 1},
        ).to_list(1000)

        if not at_risk_users:
            return

        user_ids = [u["id"] for u in at_risk_users]
        name_map = {u["id"]: u.get("name", "") for u in at_risk_users}

        # Mark as sent immediately to prevent double-fire
        await db.users.update_many(
            {"id": {"$in": user_ids}},
            {"$set": {"activation_push_sent": True, "activation_push_sent_at": now.isoformat()}}
        )

        tokens = await db.fcm_tokens.find(
            {"user_id": {"$in": user_ids}}, {"_id": 0, "token": 1, "user_id": 1},
        ).to_list(1000)

        for t in tokens[:500]:
            uid  = t.get("user_id", "")
            name = name_map.get(uid, "")
            first = name.split()[0] if name else ""
            title = f"{'Hey ' + first + '!' if first else '🎯 Almost there!'} Make your first prediction"
            body  = "You're 1 tap away from winning 50 FREE coins. Pick a match, predict the outcome — it's FREE!"
            await fcm_service.send_single(
                token=t["token"], title=title, body=body,
                data={"type": "activation_trigger", "deep_link": "/match-centre"},
            )
            await _store_in_app(db, uid, "activation_trigger", title, body, "/match-centre")

        # Also store in-app for users without FCM tokens
        notif_user_ids_with_token = {t.get("user_id") for t in tokens}
        for uid in user_ids:
            if uid not in notif_user_ids_with_token:
                name = name_map.get(uid, "")
                first = name.split()[0] if name else ""
                title = f"{'Hey ' + first + '!' if first else '🎯 Almost there!'} Make your first prediction"
                body  = "You're 1 tap away from winning 50 FREE coins. Pick a match — it's FREE!"
                await _store_in_app(db, uid, "activation_trigger", title, body, "/match-centre")

        logger.info("Activation-trigger campaign: sent to %s users (%s with FCM tokens)", len(user_ids), len(tokens))
    except Exception as e:
        logger.error("activation_trigger campaign error: %s", e)

