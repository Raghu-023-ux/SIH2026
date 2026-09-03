import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger("sms_provider")


class SMSProvider(ABC):
    """
    Abstract SMS notification provider.
    Enables pluggable SMS dispatch via MockSMSProvider, Twilio, AWS SNS, or Government Gateways.
    """

    @abstractmethod
    async def send_sms(
        self,
        phone_number: str,
        message: str,
        sender_id: Optional[str] = None,
        priority: str = "URGENT",
    ) -> Dict[str, Any]:
        """
        Sends an SMS to the target phone number.
        Returns a dictionary with status: "SENT", "DELIVERED", or "FAILED" and metadata.
        """
        pass


class MockSMSProvider(SMSProvider):
    """
    Deterministic Mock SMS provider for local development, unit tests, and demo mode.
    Simulates gateway transmission without requiring external API keys.
    """

    def __init__(self, failure_rate: float = 0.0):
        self.failure_rate = failure_rate
        self.sent_log = []

    async def send_sms(
        self,
        phone_number: str,
        message: str,
        sender_id: Optional[str] = None,
        priority: str = "URGENT",
    ) -> Dict[str, Any]:
        logger.info(f"[MockSMSProvider] Outgoing SMS to {phone_number} [{priority}]: {message[:80]}...")
        
        # Check invalid numbers or intentional mock failure
        if phone_number.endswith("9999") or phone_number.startswith("+00"):
            res = {
                "status": "FAILED",
                "phone_number": phone_number,
                "provider": "MockSMSProvider",
                "failure_reason": "Invalid or unreachable destination phone number",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        else:
            res = {
                "status": "SENT",
                "phone_number": phone_number,
                "provider": "MockSMSProvider",
                "message_id": f"sms_mock_{len(self.sent_log) + 1}",
                "character_count": len(message),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        
        self.sent_log.append(res)
        return res


class TwilioSMSProvider(SMSProvider):
    """
    Twilio SMS gateway provider used when TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN are configured.
    """

    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number

    async def send_sms(
        self,
        phone_number: str,
        message: str,
        sender_id: Optional[str] = None,
        priority: str = "URGENT",
    ) -> Dict[str, Any]:
        try:
            # If twilio library is installed, use it; otherwise mock fallback
            from twilio.rest import Client
            client = Client(self.account_sid, self.auth_token)
            msg = client.messages.create(
                body=message,
                from_=self.from_number,
                to=phone_number,
            )
            return {
                "status": "SENT",
                "phone_number": phone_number,
                "provider": "Twilio",
                "sid": msg.sid,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.error(f"[TwilioSMSProvider] SMS dispatch error: {e}")
            return {
                "status": "FAILED",
                "phone_number": phone_number,
                "provider": "Twilio",
                "failure_reason": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }


def get_sms_provider() -> SMSProvider:
    """
    Factory function returning the active SMS Provider based on environment configuration.
    """
    provider_type = os.getenv("SMS_PROVIDER", "mock").lower()

    if provider_type == "twilio":
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_FROM_NUMBER")
        if account_sid and auth_token and from_number:
            return TwilioSMSProvider(account_sid, auth_token, from_number)
        logger.warning("Twilio credentials missing. Falling back to MockSMSProvider.")

    return MockSMSProvider()
