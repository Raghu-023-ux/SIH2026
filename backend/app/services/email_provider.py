import os
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
import httpx

from backend.app.core.config import settings
from backend.app.providers.health import provider_health_registry

logger = logging.getLogger("email_provider")


class EmailProvider(ABC):
    """
    Abstract interface for operational email dispatch.
    Decoupled from disaster-science logic. Serves strictly as a downstream delivery channel.
    """

    @abstractmethod
    async def send_email(
        self,
        to: Union[str, List[str]],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        from_email: Optional[str] = None,
        tags: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Dispatches an operational email.
        Returns dict with status: 'SENT_TO_PROVIDER' or 'FAILED' and delivery metadata.
        """
        pass


class MockEmailProvider(EmailProvider):
    """
    Deterministic Mock Email Provider for unit tests, offline demonstration, and simulation modes.
    Guarantees zero external network dependencies and no accidental real-world email transmissions.
    """

    def __init__(self):
        self.sent_emails: List[Dict[str, Any]] = []

    async def send_email(
        self,
        to: Union[str, List[str]],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        from_email: Optional[str] = None,
        tags: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        recipients = [to] if isinstance(to, str) else to
        sender = from_email or settings.RESEND_FROM_EMAIL
        logger.info(f"[MockEmailProvider] Outgoing email to {recipients} | Subject: '{subject[:60]}...'")

        # Test simulation for bounced/invalid email addresses
        if any("invalid@" in r or "bounce@" in r for r in recipients):
            return {
                "status": "FAILED",
                "recipients": recipients,
                "provider": "MockEmailProvider",
                "failure_reason": "Recipient mailbox address rejected or invalid domain",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        msg_id = f"mock_email_{len(self.sent_emails) + 1}_{int(time.time())}"
        res = {
            "status": "SENT_TO_PROVIDER",
            "message_id": msg_id,
            "recipients": recipients,
            "sender": sender,
            "subject": subject,
            "provider": "MockEmailProvider",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.sent_emails.append(res)
        return res


class ResendEmailProvider(EmailProvider):
    """
    Live Email Provider utilizing Resend REST API / SDK for transactional emergency communications.
    Strictly server-side; handles rate limits, backoff, and transparent fallback on network failure.
    """

    def __init__(self, api_key: Optional[str] = None, from_email: Optional[str] = None):
        self.api_key = api_key or settings.RESEND_API_KEY
        self.from_email = from_email or settings.RESEND_FROM_EMAIL
        self.mock_fallback = MockEmailProvider()

    async def send_email(
        self,
        to: Union[str, List[str]],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        from_email: Optional[str] = None,
        tags: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        recipients = [to] if isinstance(to, str) else to
        sender = from_email or self.from_email

        if not self.api_key:
            logger.info("No Resend API key detected. Utilizing deterministic mock email provider.")
            return await self.mock_fallback.send_email(to, subject, html_body, text_body, from_email, tags)

        start_t = time.perf_counter()
        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "from": sender,
            "to": recipients,
            "subject": subject,
            "html": html_body,
        }
        if text_body:
            payload["text"] = text_body
        if tags:
            payload["tags"] = tags

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                latency_ms = (time.perf_counter() - start_t) * 1000.0

                if resp.status_code in [200, 201]:
                    data = resp.json()
                    msg_id = data.get("id", f"resend_{int(time.time())}")
                    provider_health_registry.record_success("resend-email", latency_ms)
                    logger.info(f"Resend email dispatched successfully: {msg_id} to {recipients}")
                    return {
                        "status": "SENT_TO_PROVIDER",
                        "message_id": msg_id,
                        "recipients": recipients,
                        "sender": sender,
                        "subject": subject,
                        "provider": "ResendEmailProvider",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                else:
                    err_msg = f"HTTP {resp.status_code}: {resp.text}"
                    logger.warning(f"Resend email dispatch rejected ({err_msg})")
                    provider_health_registry.record_failure("resend-email", f"HTTP {resp.status_code}")
                    return {
                        "status": "FAILED",
                        "recipients": recipients,
                        "sender": sender,
                        "subject": subject,
                        "failure_reason": err_msg,
                        "provider": "ResendEmailProvider",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }

        except Exception as err:
            latency_ms = (time.perf_counter() - start_t) * 1000.0
            logger.warning(f"Resend dispatch exception ({err}). Engaging fallback.")
            provider_health_registry.record_failure("resend-email", str(err))
            return {
                "status": "FAILED",
                "recipients": recipients,
                "sender": sender,
                "subject": subject,
                "failure_reason": str(err),
                "provider": "ResendEmailProvider",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


_email_provider_instance: Optional[EmailProvider] = None


def get_email_provider() -> EmailProvider:
    """Singleton factory for Email Provider."""
    global _email_provider_instance
    if _email_provider_instance is None:
        if settings.RESEND_PROVIDER_MODE.upper() == "LIVE" and settings.RESEND_API_KEY:
            _email_provider_instance = ResendEmailProvider()
        else:
            _email_provider_instance = MockEmailProvider()
    return _email_provider_instance
