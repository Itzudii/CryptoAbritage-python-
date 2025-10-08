"""
Notification service for sending alerts via Telegram and other channels.
"""
import os
import requests
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum, auto

class AlertLevel(Enum):
    INFO = auto()
    WARNING = auto()
    CRITICAL = auto()
    EMERGENCY = auto()

class NotificationService:
    """Handles sending alerts and notifications to various channels."""
    
    def __init__(self):
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.enabled = bool(self.telegram_token and self.telegram_chat_id)
        
        if not self.enabled:
            print("Warning: Telegram notifications disabled. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env to enable.")
    
    def _send_telegram(self, message: str, level: AlertLevel = AlertLevel.INFO) -> bool:
        """Send a message to Telegram."""
        if not self.enabled:
            return False
            
        try:
            # Add alert level emoji
            emoji = {
                AlertLevel.INFO: "ℹ️",
                AlertLevel.WARNING: "⚠️",
                AlertLevel.CRITICAL: "🔴",
                AlertLevel.EMERGENCY: "🚨"
            }.get(level, "")
            
            # Format message with timestamp and level
            formatted_msg = f"{emoji} *{level.name}* - {datetime.utcnow().isoformat()}Z\n{message}"
            
            response = requests.post(
                f"https://api.telegram.org/bot{self.telegram_token}/sendMessage",
                json={
                    "chat_id": self.telegram_chat_id,
                    "text": formatted_msg,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True
                },
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send Telegram notification: {e}")
            return False
    
    def send_alert(self, message: str, level: AlertLevel = AlertLevel.INFO) -> bool:
        """Send an alert to all configured notification channels."""
        if level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY]:
            # For critical alerts, try to send to all channels
            return self._send_telegram(message, level)
        else:
            # For non-critical, just use the primary channel (Telegram)
            return self._send_telegram(message, level)

# Global instance
notifier = NotificationService()

def send_risk_alert(
    title: str, 
    details: Dict[str, Any], 
    level: AlertLevel = AlertLevel.WARNING,
    context: Optional[Dict[str, Any]] = None
) -> bool:
    """Helper function to send formatted risk alerts."""
    # Format details into a readable message
    details_str = "\n".join(f"• {k}: {v}" for k, v in details.items())
    
    # Add context if provided
    context_str = ""
    if context:
        context_str = "\n\n*Context:*\n" + "\n".join(f"• {k}: {v}" for k, v in context.items())
    
    message = f"*{title}*\n{details_str}{context_str}"
    return notifier.send_alert(message, level)
