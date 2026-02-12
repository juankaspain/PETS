"""Alert manager for notifications."""

import logging
import os
from decimal import Decimal
from typing import Literal

import requests

logger = logging.getLogger(__name__)

AlertType = Literal[
    "circuit_breaker",
    "emergency_stop",
    "large_loss",
    "bot_error",
    "low_balance",
]


class AlertManager:
    """Alert manager for Slack, Email, and SMS notifications."""

    def __init__(self):
        """Initialize alert manager."""
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        self.email_enabled = os.getenv("EMAIL_ALERTS_ENABLED", "false") == "true"
        self.sms_enabled = os.getenv("SMS_ALERTS_ENABLED", "false") == "true"

    async def send_alert(
        self,
        alert_type: AlertType,
        title: str,
        message: str,
        severity: Literal["info", "warning", "error", "critical"] = "info",
        **extra_data,
    ) -> None:
        """Send alert to all configured channels.

        Args:
            alert_type: Type of alert
            title: Alert title
            message: Alert message
            severity: Alert severity
            **extra_data: Additional data
        """
        logger.info(
            f"Sending alert: {alert_type}",
            extra={
                "title": title,
                "message": message,
                "severity": severity,
                **extra_data,
            },
        )

        # Send to Slack
        if self.slack_webhook:
            await self._send_slack(alert_type, title, message, severity, **extra_data)

        # Send email for critical alerts
        if self.email_enabled and severity in ["error", "critical"]:
            await self._send_email(title, message, **extra_data)

        # Send SMS for critical alerts only
        if self.sms_enabled and severity == "critical":
            await self._send_sms(title, message)

    async def _send_slack(
        self,
        alert_type: AlertType,
        title: str,
        message: str,
        severity: str,
        **extra_data,
    ) -> None:
        """Send Slack notification.

        Args:
            alert_type: Alert type
            title: Title
            message: Message
            severity: Severity
            **extra_data: Extra data
        """
        if not self.slack_webhook:
            return

        # Color based on severity
        colors = {
            "info": "#36a64f",  # Green
            "warning": "#ff9800",  # Orange
            "error": "#f44336",  # Red
            "critical": "#d32f2f",  # Dark red
        }

        # Emoji based on alert type
        emojis = {
            "circuit_breaker": "⚠️",
            "emergency_stop": "🚨",
            "large_loss": "📉",
            "bot_error": "❌",
            "low_balance": "💰",
        }

        payload = {
            "attachments": [
                {
                    "color": colors.get(severity, "#808080"),
                    "title": f"{emojis.get(alert_type, '🔔')} {title}",
                    "text": message,
                    "fields": [
                        {"title": key, "value": str(value), "short": True}
                        for key, value in extra_data.items()
                    ],
                    "footer": "PETS - Polymarket Elite Trading System",
                    "ts": int(__import__("time").time()),
                }
            ]
        }

        try:
            response = requests.post(self.slack_webhook, json=payload, timeout=5)
            response.raise_for_status()
            logger.debug("Slack alert sent successfully")
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")

    async def _send_email(self, title: str, message: str, **extra_data) -> None:
        """Send email notification.

        Args:
            title: Title
            message: Message
            **extra_data: Extra data
        """
        # TODO: Implement email sending (SMTP)
        logger.info(f"Email alert: {title} - {message}")

    async def _send_sms(self, title: str, message: str) -> None:
        """Send SMS notification.

        Args:
            title: Title
            message: Message
        """
        # TODO: Implement SMS (Twilio)
        logger.info(f"SMS alert: {title} - {message}")

    # Convenience methods for common alerts

    async def circuit_breaker_triggered(
        self,
        bot_id: int,
        reason: str,
        consecutive_losses: int,
    ) -> None:
        """Alert for circuit breaker triggered."""
        await self.send_alert(
            alert_type="circuit_breaker",
            title="Circuit Breaker Triggered",
            message=f"Bot {bot_id} stopped: {reason}",
            severity="warning",
            bot_id=bot_id,
            reason=reason,
            consecutive_losses=consecutive_losses,
        )

    async def emergency_stop_triggered(self, reason: str, drawdown_pct: Decimal) -> None:
        """Alert for emergency stop."""
        await self.send_alert(
            alert_type="emergency_stop",
            title="🚨 EMERGENCY STOP TRIGGERED",
            message=f"All bots stopped: {reason}",
            severity="critical",
            reason=reason,
            drawdown_pct=float(drawdown_pct),
        )

    async def large_loss(
        self,
        bot_id: int,
        loss_amount: Decimal,
        loss_pct: Decimal,
    ) -> None:
        """Alert for large loss."""
        await self.send_alert(
            alert_type="large_loss",
            title="Large Loss Detected",
            message=f"Bot {bot_id} loss: ${loss_amount:.2f} ({loss_pct:.1f}%)",
            severity="error",
            bot_id=bot_id,
            loss_amount=float(loss_amount),
            loss_pct=float(loss_pct),
        )

    async def bot_error(self, bot_id: int, error: str) -> None:
        """Alert for bot error."""
        await self.send_alert(
            alert_type="bot_error",
            title="Bot Error",
            message=f"Bot {bot_id} error: {error}",
            severity="error",
            bot_id=bot_id,
            error=error,
        )

    async def low_balance_warning(self, balance: Decimal, threshold: Decimal) -> None:
        """Alert for low balance."""
        await self.send_alert(
            alert_type="low_balance",
            title="Low Balance Warning",
            message=f"Balance ${balance:.2f} below threshold ${threshold:.2f}",
            severity="warning",
            balance=float(balance),
            threshold=float(threshold),
        )
