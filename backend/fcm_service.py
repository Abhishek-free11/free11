"""
Firebase Cloud Messaging (FCM) Service for FREE11
Manages push notification tokens and sending.
In dev mode (no Firebase keys), notifications are DB-only.
Plug in Firebase when credentials are available.
"""
import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, List
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

FIREBASE_CREDENTIALS_PATH = os.environ.get("FIREBASE_CREDENTIALS_PATH", "")
_FIREBASE_PRIVATE_KEY = os.environ.get("FIREBASE_PRIVATE_KEY", "").replace(r'\n', '\n')
_FIREBASE_CLIENT_EMAIL = os.environ.get("FIREBASE_CLIENT_EMAIL", "")
_FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID", "")
_FIREBASE_PRIVATE_KEY_ID = os.environ.get("FIREBASE_PRIVATE_KEY_ID", "")
_FIREBASE_CLIENT_ID = os.environ.get("FIREBASE_CLIENT_ID", "")

# Enable FCM if env-var credentials are set OR the JSON file exists on disk
FCM_ENABLED = bool(
    (_FIREBASE_PRIVATE_KEY and _FIREBASE_CLIENT_EMAIL and _FIREBASE_PROJECT_ID)
    or (FIREBASE_CREDENTIALS_PATH and os.path.exists(FIREBASE_CREDENTIALS_PATH))
)

_fcm_initialized = False


def _init_firebase():
    global _fcm_initialized
    if _fcm_initialized or not FCM_ENABLED:
        return False
    try:
        import firebase_admin
        from firebase_admin import credentials

        # Priority 1 — environment variables (Kubernetes-safe, no file needed)
        if _FIREBASE_PRIVATE_KEY and _FIREBASE_CLIENT_EMAIL and _FIREBASE_PROJECT_ID:
            cred_dict = {
                "type": "service_account",
                "project_id": _FIREBASE_PROJECT_ID,
                "private_key_id": _FIREBASE_PRIVATE_KEY_ID,
                "private_key": _FIREBASE_PRIVATE_KEY,
                "client_email": _FIREBASE_CLIENT_EMAIL,
                "client_id": _FIREBASE_CLIENT_ID,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": (
                    f"https://www.googleapis.com/robot/v1/metadata/x509/"
                    f"{_FIREBASE_CLIENT_EMAIL.replace('@', '%40')}"
                ),
            }
            cred = credentials.Certificate(cred_dict)
        # Priority 2 — JSON file on disk (local dev / legacy)
        elif FIREBASE_CREDENTIALS_PATH and os.path.exists(FIREBASE_CREDENTIALS_PATH):
            cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        else:
            logger.warning("Firebase: no credentials found (env vars or file)")
            return False

        firebase_admin.initialize_app(cred)
        _fcm_initialized = True
        logger.info("Firebase initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Firebase init failed: {e}")
        return False


class FCMService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        if FCM_ENABLED:
            _init_firebase()

    async def register_token(self, user_id: str, token: str, device_type: str = "web") -> Dict:
        now = datetime.now(timezone.utc).isoformat()
        await self.db.fcm_tokens.update_one(
            {"user_id": user_id, "device_type": device_type},
            {"$set": {"token": token, "updated_at": now, "active": True},
             "$setOnInsert": {"created_at": now}},
            upsert=True,
        )
        return {"registered": True}

    async def unregister_token(self, user_id: str, device_type: str = "web"):
        await self.db.fcm_tokens.update_one(
            {"user_id": user_id, "device_type": device_type},
            {"$set": {"active": False}},
        )

    async def get_user_tokens(self, user_id: str) -> List[str]:
        tokens = await self.db.fcm_tokens.find(
            {"user_id": user_id, "active": True}, {"_id": 0, "token": 1}
        ).to_list(10)
        return [t["token"] for t in tokens]

    async def send_push(self, user_id: str, title: str, body: str, data: Optional[Dict] = None) -> bool:
        tokens = await self.get_user_tokens(user_id)
        if not tokens:
            return False

        if not _fcm_initialized:
            logger.info(f"FCM dev mode: would push to {user_id}: {title}")
            return False

        try:
            from firebase_admin import messaging
            for token in tokens:
                message = messaging.Message(
                    notification=messaging.Notification(title=title, body=body),
                    data={k: str(v) for k, v in (data or {}).items()},
                    token=token,
                )
                try:
                    messaging.send(message)
                except Exception as e:
                    logger.warning(f"FCM send failed for token: {e}")
                    await self.db.fcm_tokens.update_one(
                        {"token": token}, {"$set": {"active": False}}
                    )
            return True
        except Exception as e:
            logger.error(f"FCM send error: {e}")
            return False

    async def send_push_bulk(self, user_ids: List[str], title: str, body: str, data: Optional[Dict] = None):
        for uid in user_ids:
            await self.send_push(uid, title, body, data)

    async def send_bulk(self, tokens: List[str], title: str, body: str, data: Optional[Dict] = None):
        """Send push to a list of FCM tokens directly (for campaign use)."""
        if not tokens or not _fcm_initialized:
            logger.info("FCM dev mode: bulk push '%s' to %d tokens", title, len(tokens))
            return
        from firebase_admin import messaging
        messages = [
            messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data={k: str(v) for k, v in (data or {}).items()},
                token=tok,
            )
            for tok in tokens
        ]
        # Send in batches of 500 (FCM limit)
        for i in range(0, len(messages), 500):
            batch = messages[i:i + 500]
            try:
                resp = messaging.send_each(batch)
                logger.info("FCM bulk batch %d: %d sent, %d failed", i // 500, resp.success_count, resp.failure_count)
                # Deactivate invalid tokens
                for idx, r in enumerate(resp.responses):
                    if not r.success:
                        bad_token = tokens[i + idx]
                        await self.db.fcm_tokens.update_one({"token": bad_token}, {"$set": {"active": False}})
            except Exception as e:
                logger.error("FCM send_each error: %s", e)

    async def send_single(self, token: str, title: str, body: str, data: Optional[Dict] = None):
        """Send push to a single FCM token directly."""
        if not _fcm_initialized:
            logger.info("FCM dev mode: push '%s'", title)
            return
        from firebase_admin import messaging
        try:
            messaging.send(messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data={k: str(v) for k, v in (data or {}).items()},
                token=token,
            ))
        except Exception as e:
            logger.warning("FCM send_single failed: %s", e)
            await self.db.fcm_tokens.update_one({"token": token}, {"$set": {"active": False}})

    async def get_notification_preferences(self, user_id: str) -> Dict:
        prefs = await self.db.notification_prefs.find_one({"user_id": user_id}, {"_id": 0})
        if not prefs:
            return {
                "user_id": user_id,
                "match_starting": True,
                "contest_closing": True,
                "match_completed": True,
                "leaderboard_update": True,
                "payment_success": True,
                "daily_reminder": True,
            }
        return prefs

    async def update_preferences(self, user_id: str, prefs: Dict) -> Dict:
        now = datetime.now(timezone.utc).isoformat()
        update = {k: v for k, v in prefs.items() if isinstance(v, bool)}
        update["updated_at"] = now
        await self.db.notification_prefs.update_one(
            {"user_id": user_id},
            {"$set": update, "$setOnInsert": {"user_id": user_id, "created_at": now}},
            upsert=True,
        )
        return await self.get_notification_preferences(user_id)
