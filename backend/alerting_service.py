"""
Alerting Service for FREE11
============================
Slack webhook + email fallback for critical alerts.
"""

import os
import httpx
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(Enum):
    VOUCHER_FAILURE_RATE = "voucher_failure_rate"
    PROVIDER_DEGRADATION = "provider_degradation"
    HIGH_TICKET_VOLUME = "high_ticket_volume"
    SYSTEM_ERROR = "system_error"
    BETA_CAP_REACHED = "beta_cap_reached"


SEVERITY_EMOJI = {
    AlertSeverity.INFO: "ℹ️",
    AlertSeverity.WARNING: "⚠️",
    AlertSeverity.CRITICAL: "🚨"
}

SEVERITY_COLOR = {
    AlertSeverity.INFO: "#36a64f",
    AlertSeverity.WARNING: "#ff9800",
    AlertSeverity.CRITICAL: "#ff0000"
}


class AlertService:
    """Service for sending alerts via Slack and email"""
    
    def __init__(self):
        self.slack_webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
        self.alert_email = os.environ.get("ALERT_EMAIL")
        self.environment = os.environ.get("FREE11_ENV", "sandbox")
        
        # Throttle settings (prevent alert storms)
        self._last_alert_times: Dict[str, datetime] = {}
        self._throttle_minutes = 15  # Don't repeat same alert type within 15 min
    
    def _should_throttle(self, alert_type: AlertType) -> bool:
        """Check if alert should be throttled"""
        key = alert_type.value
        now = datetime.now(timezone.utc)
        
        if key in self._last_alert_times:
            time_since = (now - self._last_alert_times[key]).total_seconds() / 60
            if time_since < self._throttle_minutes:
                return True
        
        self._last_alert_times[key] = now
        return False
    
    async def send_slack_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        alert_type: AlertType,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send alert to Slack webhook"""
        if not self.slack_webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False
        
        if self._should_throttle(alert_type):
            logger.info(f"Alert throttled: {alert_type.value}")
            return False
        
        emoji = SEVERITY_EMOJI.get(severity, "📢")
        color = SEVERITY_COLOR.get(severity, "#808080")
        
        # Build Slack message
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} FREE11 Alert: {title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            }
        ]
        
        if details:
            detail_text = "\n".join([f"• *{k}*: {v}" for k, v in details.items()])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": detail_text
                }
            })
        
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Environment: *{self.environment}* | Type: `{alert_type.value}` | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
                }
            ]
        })
        
        payload = {
            "blocks": blocks,
            "attachments": [{
                "color": color,
                "fallback": f"{title}: {message}"
            }]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.slack_webhook_url,
                    json=payload,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"Slack alert sent: {title}")
                    return True
                else:
                    logger.error(f"Slack alert failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Slack alert error: {e}")
            return False
    
    async def send_email_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        alert_type: AlertType,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send alert via email (fallback)"""
        if not self.alert_email:
            logger.warning("Alert email not configured")
            return False
        
        # Import email service
        try:
            from email_service import email_service
            
            detail_html = ""
            if details:
                detail_items = "".join([f"<li><strong>{k}</strong>: {v}</li>" for k, v in details.items()])
                detail_html = f"<ul>{detail_items}</ul>"
            
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: {SEVERITY_COLOR.get(severity, '#808080')}; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                    <h2 style="margin: 0;">{SEVERITY_EMOJI.get(severity, '📢')} FREE11 Alert</h2>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">{title}</p>
                </div>
                <div style="background: #f8f9fa; padding: 20px; border: 1px solid #ddd; border-top: none;">
                    <p>{message}</p>
                    {detail_html}
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                    <p style="color: #666; font-size: 12px;">
                        Environment: {self.environment} | Alert Type: {alert_type.value}<br>
                        Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
                    </p>
                </div>
            </div>
            """
            
            success = await email_service.send_email(
                to_email=self.alert_email,
                to_name="FREE11 Admin",
                subject=f"[{severity.value.upper()}] FREE11 Alert: {title}",
                html_content=html_content
            )
            
            if success:
                logger.info(f"Email alert sent: {title}")
            return success
            
        except Exception as e:
            logger.error(f"Email alert error: {e}")
            return False
    
    async def send_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        alert_type: AlertType,
        details: Optional[Dict[str, Any]] = None
    ):
        """Send alert via Slack and email fallback for critical"""
        # Always try Slack first
        slack_sent = await self.send_slack_alert(title, message, severity, alert_type, details)
        
        # Send email as fallback for critical alerts or if Slack fails
        if severity == AlertSeverity.CRITICAL or not slack_sent:
            await self.send_email_alert(title, message, severity, alert_type, details)


# Global instance
alert_service = AlertService()


# ==================== Convenience Functions ====================

async def alert_high_failure_rate(failure_rate: float, threshold: float = 5.0):
    """Alert when voucher failure rate exceeds threshold"""
    await alert_service.send_alert(
        title="High Voucher Failure Rate",
        message=f"Voucher delivery failure rate ({failure_rate:.1f}%) exceeds threshold ({threshold}%)",
        severity=AlertSeverity.CRITICAL if failure_rate > 10 else AlertSeverity.WARNING,
        alert_type=AlertType.VOUCHER_FAILURE_RATE,
        details={
            "Current Rate": f"{failure_rate:.1f}%",
            "Threshold": f"{threshold}%",
            "Action": "Check provider health and review failed deliveries"
        }
    )


async def alert_provider_degradation(provider: str, success_rate: float):
    """Alert when provider success rate drops"""
    await alert_service.send_alert(
        title=f"Provider Degradation: {provider}",
        message=f"Provider {provider} success rate has dropped to {success_rate:.1f}%",
        severity=AlertSeverity.WARNING,
        alert_type=AlertType.PROVIDER_DEGRADATION,
        details={
            "Provider": provider,
            "Success Rate": f"{success_rate:.1f}%",
            "Action": "Consider pausing provider or checking API status"
        }
    )


async def alert_high_ticket_volume(open_tickets: int, threshold: int = 20):
    """Alert when support ticket volume is high"""
    await alert_service.send_alert(
        title="High Support Ticket Volume",
        message=f"Open support tickets ({open_tickets}) exceeds threshold ({threshold})",
        severity=AlertSeverity.WARNING,
        alert_type=AlertType.HIGH_TICKET_VOLUME,
        details={
            "Open Tickets": open_tickets,
            "Threshold": threshold,
            "Action": "Review tickets and identify common issues"
        }
    )


async def alert_beta_cap_warning(current: int, cap: int):
    """Alert when approaching beta cap"""
    remaining = cap - current
    pct_used = (current / cap) * 100
    
    await alert_service.send_alert(
        title="Beta Invite Cap Warning",
        message=f"Beta invites at {pct_used:.1f}% capacity ({remaining} remaining)",
        severity=AlertSeverity.WARNING if pct_used < 95 else AlertSeverity.CRITICAL,
        alert_type=AlertType.BETA_CAP_REACHED,
        details={
            "Used": current,
            "Cap": cap,
            "Remaining": remaining,
            "Action": "Consider increasing cap or closing beta"
        }
    )


async def alert_system_error(error_type: str, error_message: str, context: Dict[str, Any] = None):
    """Alert for unexpected system errors"""
    await alert_service.send_alert(
        title=f"System Error: {error_type}",
        message=error_message,
        severity=AlertSeverity.CRITICAL,
        alert_type=AlertType.SYSTEM_ERROR,
        details=context or {}
    )
