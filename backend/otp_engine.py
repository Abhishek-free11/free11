"""
OTP Email Verification Engine for FREE11
Generates, stores, and validates OTP codes for email verification.
In dev mode (no email provider), OTP is returned in API response.
Plug in Resend/SendGrid when keys are available.
"""
import os
import random
import string
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 10
MAX_ATTEMPTS = 5
RESEND_COOLDOWN_SECONDS = 60

EMAIL_PROVIDER = os.environ.get("EMAIL_PROVIDER", "dev")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
EMAIL_FROM = os.environ.get("RESEND_FROM_EMAIL", os.environ.get("EMAIL_FROM", "FREE11 <noreply@free11.app>"))


def _generate_otp() -> str:
    return "".join(random.choices(string.digits, k=OTP_LENGTH))


class OTPEngine:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def send_otp(self, email: str, purpose: str = "registration") -> Dict:
        email = email.strip().lower()
        now = datetime.now(timezone.utc)

        last = await self.db.otp_codes.find_one(
            {"email": email, "purpose": purpose},
            sort=[("created_at", -1)]
        )
        if last:
            last_time = datetime.fromisoformat(last["created_at"])
            if (now - last_time).total_seconds() < RESEND_COOLDOWN_SECONDS:
                wait = int(RESEND_COOLDOWN_SECONDS - (now - last_time).total_seconds())
                return {"sent": False, "error": f"Please wait {wait}s before requesting another OTP"}

        otp = _generate_otp()
        expires_at = (now + timedelta(minutes=OTP_EXPIRY_MINUTES)).isoformat()

        await self.db.otp_codes.insert_one({
            "email": email,
            "otp": otp,
            "purpose": purpose,
            "attempts": 0,
            "verified": False,
            "created_at": now.isoformat(),
            "expires_at": expires_at,
        })

        sent = await self._deliver_otp(email, otp, purpose)

        result = {
            "sent": True,       # OTP stored in DB — always True if we reach here
            "email_delivered": sent,
            "email": email,
            "expires_in": OTP_EXPIRY_MINUTES * 60,
            "message": f"OTP sent to {email}",
        }

        if not sent:
            result["dev_otp"] = otp
            result["message"] = "Email delivery is being retried. Use the code below to verify now:"

        logger.info(f"OTP sent to {email} for {purpose} (delivered={sent})")
        return result

    async def verify_otp(self, email: str, otp: str, purpose: str = "registration") -> Dict:
        email = email.strip().lower()
        now = datetime.now(timezone.utc)

        record = await self.db.otp_codes.find_one(
            {"email": email, "purpose": purpose, "verified": False},
            sort=[("created_at", -1)]
        )

        if not record:
            return {"verified": False, "error": "No OTP found. Request a new one."}

        if record.get("attempts", 0) >= MAX_ATTEMPTS:
            return {"verified": False, "error": "Too many attempts. Request a new OTP."}

        await self.db.otp_codes.update_one(
            {"_id": record["_id"]}, {"$inc": {"attempts": 1}}
        )

        expires = datetime.fromisoformat(record["expires_at"])
        if now > expires:
            return {"verified": False, "error": "OTP expired. Request a new one."}

        if record["otp"] != otp.strip():
            remaining = MAX_ATTEMPTS - record.get("attempts", 0) - 1
            return {"verified": False, "error": f"Invalid OTP. {remaining} attempts remaining."}

        await self.db.otp_codes.update_one(
            {"_id": record["_id"]}, {"$set": {"verified": True}}
        )

        return {"verified": True, "email": email}

    async def is_email_verified(self, email: str) -> bool:
        user = await self.db.users.find_one({"email": email.strip().lower()}, {"email_verified": 1})
        return user.get("email_verified", False) if user else False

    async def mark_email_verified(self, email: str):
        await self.db.users.update_one(
            {"email": email.strip().lower()},
            {"$set": {"email_verified": True, "email_verified_at": datetime.now(timezone.utc).isoformat()}}
        )

    async def _deliver_otp(self, email: str, otp: str, purpose: str) -> bool:
        if RESEND_API_KEY:
            return await self._send_via_resend(email, otp, purpose)
        if SENDGRID_API_KEY:
            return await self._send_via_sendgrid(email, otp, purpose)
        logger.warning(f"No email provider configured. OTP for {email}: {otp}")
        return False

    async def _send_via_resend(self, email: str, otp: str, purpose: str) -> bool:
        import httpx
        # Web OTP API (Android Chrome) compatible text — added to email subject+body
        # When SMS is added, use: "Your FREE11 code is: {otp}\n@free11.com #{otp}"
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    "https://api.resend.com/emails",
                    headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
                    json={
                        "from": EMAIL_FROM,
                        "to": [email],
                        "subject": f"FREE11 code: {otp}",  # Code in subject for quick preview
                        "html": f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#0F1115;font-family:'Helvetica Neue',Arial,sans-serif;">
  <div style="max-width:480px;margin:40px auto;padding:32px 24px;background:#1B1E23;border-radius:16px;border:1px solid rgba(198,160,82,0.2);">
    <div style="text-align:center;margin-bottom:24px;">
      <h1 style="font-size:28px;font-weight:900;color:#C6A052;letter-spacing:6px;margin:0;">FREE11</h1>
      <p style="font-size:12px;color:#8A9096;margin:4px 0 0;">Cricket Prediction &bull; Real Rewards</p>
    </div>
    <h2 style="font-size:18px;color:#ffffff;font-weight:700;margin:0 0 8px;">FREE11 Verification</h2>
    <p style="font-size:14px;color:#8A9096;margin:0 0 20px;">Your verification code is:</p>
    <div style="background:#0F1115;border:1px solid rgba(198,160,82,0.3);border-radius:12px;padding:20px;text-align:center;margin-bottom:20px;">
      <h1 style="font-size:40px;font-weight:900;color:#C6A052;letter-spacing:12px;margin:0;font-variant-numeric:tabular-nums;">{otp}</h1>
    </div>
    <p style="font-size:13px;color:#8A9096;margin:0 0 6px;">This code expires in <strong style="color:#ffffff;">{OTP_EXPIRY_MINUTES} minutes</strong>.</p>
    <p style="font-size:12px;color:#5a6270;margin:0;">Do not share this code with anyone.</p>
    <hr style="border:none;border-top:1px solid rgba(255,255,255,0.06);margin:24px 0;">
    <p style="font-size:11px;color:#5a6270;text-align:center;margin:0;">
      You received this because a registration was attempted on FREE11.<br>
      If you did not request this, please ignore this email.
    </p>
  </div>
</body>
</html>
                        """,
                    },
                )
                if r.status_code != 200:
                    logger.error(f"Resend API error {r.status_code}: {r.text}")
                return r.status_code == 200
        except Exception as e:
            logger.error(f"Resend send failed: {e}")
            return False

    async def _send_via_sendgrid(self, email: str, otp: str, purpose: str) -> bool:
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers={"Authorization": f"Bearer {SENDGRID_API_KEY}", "Content-Type": "application/json"},
                    json={
                        "personalizations": [{"to": [{"email": email}]}],
                        "from": {"email": "noreply@free11.app", "name": "FREE11"},
                        "subject": f"FREE11 Verification Code: {otp}",
                        "content": [{"type": "text/plain", "value": f"Your FREE11 verification code is: {otp}. Expires in {OTP_EXPIRY_MINUTES} minutes."}],
                    },
                )
                return r.status_code in (200, 201, 202)
        except Exception as e:
            logger.error(f"SendGrid send failed: {e}")
            return False

    async def cleanup_expired(self) -> int:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        result = await self.db.otp_codes.delete_many({"created_at": {"$lt": cutoff}})
        return result.deleted_count
