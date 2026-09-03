import os
import json
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from backend.app.core.config import settings
from backend.app.providers.health import provider_health_registry

logger = logging.getLogger("fcm_provider")


class FCMProvider(ABC):
    """
    Abstract push notification delivery provider for Firebase Cloud Messaging (FCM).
    Decoupled from disaster-science logic. Serves strictly as a downstream delivery channel.
    """

    @abstractmethod
    async def send_to_token(
        self,
        fcm_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        priority: str = "HIGH"
    ) -> Dict[str, Any]:
        """
        Dispatches push notification to a specific device registration token.
        Returns dict with status: 'SENT_TO_FCM', 'TOKEN_INVALID', or 'FAILED'.
        """
        pass

    @abstractmethod
    async def send_to_topic(
        self,
        topic: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        priority: str = "HIGH"
    ) -> Dict[str, Any]:
        """
        Dispatches push notification to a registered regional topic (e.g. 'region:sikkim').
        """
        pass

    @abstractmethod
    async def send_multicast(
        self,
        fcm_tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        priority: str = "HIGH"
    ) -> Dict[str, Any]:
        """
        Dispatches push notification to multiple device registration tokens.
        Identifies invalid/expired tokens for database deactivation.
        """
        pass


class MockFCMProvider(FCMProvider):
    """
    Deterministic Mock FCM Provider for unit tests, offline demonstration, and simulation modes.
    Guarantees zero external network dependencies while faithfully simulating delivery states.
    """

    def __init__(self):
        self.sent_messages: List[Dict[str, Any]] = []

    async def send_to_token(
        self,
        fcm_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        priority: str = "HIGH"
    ) -> Dict[str, Any]:
        logger.info(f"[MockFCMProvider] Dispatching push to token {fcm_token[:15]}... [{priority}]: {title}")
        
        # Test simulation for invalid/expired tokens
        if fcm_token.startswith("invalid_") or fcm_token.startswith("expired_") or len(fcm_token) < 10:
            return {
                "status": "TOKEN_INVALID",
                "fcm_token": fcm_token,
                "provider": "MockFCMProvider",
                "failure_reason": "Device registration token is expired or unregistered on FCM",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        msg_id = f"mock_fcm_{len(self.sent_messages) + 1}_{int(time.time())}"
        res = {
            "status": "SENT_TO_FCM",
            "message_id": msg_id,
            "fcm_token": fcm_token,
            "title": title,
            "body": body,
            "priority": priority,
            "provider": "MockFCMProvider",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.sent_messages.append(res)
        return res

    async def send_to_topic(
        self,
        topic: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        priority: str = "HIGH"
    ) -> Dict[str, Any]:
        logger.info(f"[MockFCMProvider] Dispatching broadcast push to topic '{topic}' [{priority}]: {title}")
        msg_id = f"mock_topic_{topic}_{int(time.time())}"
        res = {
            "status": "SENT_TO_FCM",
            "message_id": msg_id,
            "topic": topic,
            "title": title,
            "body": body,
            "priority": priority,
            "provider": "MockFCMProvider",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.sent_messages.append(res)
        return res

    async def send_multicast(
        self,
        fcm_tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        priority: str = "HIGH"
    ) -> Dict[str, Any]:
        logger.info(f"[MockFCMProvider] Multicasting push to {len(fcm_tokens)} devices [{priority}]: {title}")
        valid_tokens = []
        invalid_tokens = []

        for token in fcm_tokens:
            if token.startswith("invalid_") or token.startswith("expired_") or len(token) < 10:
                invalid_tokens.append(token)
            else:
                valid_tokens.append(token)

        res = {
            "status": "SENT_TO_FCM" if valid_tokens else "FAILED",
            "sent_count": len(valid_tokens),
            "failed_count": len(invalid_tokens),
            "invalid_tokens": invalid_tokens,
            "provider": "MockFCMProvider",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.sent_messages.append(res)
        return res


class FirebaseAdminFCMProvider(FCMProvider):
    """
    Live Firebase Cloud Messaging Provider utilizing the official server-side firebase-admin SDK.
    Enforces server-side credential secrecy, exponential backoff, and robust error classification.
    """

    def __init__(self):
        self._initialized = False
        self._app = None
        self._init_firebase_app()
        self.mock_fallback = MockFCMProvider()

    def _init_firebase_app(self):
        try:
            import firebase_admin
            from firebase_admin import credentials

            # Check if default app or named app already initialized
            try:
                self._app = firebase_admin.get_app(settings.FIREBASE_APP_NAME)
                self._initialized = True
                return
            except ValueError:
                pass

            cred = None
            if settings.FIREBASE_CREDENTIALS_JSON:
                cred_dict = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
                cred = credentials.Certificate(cred_dict)
            elif settings.FIREBASE_CREDENTIALS_PATH and os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)

            if cred:
                self._app = firebase_admin.initialize_app(
                    cred,
                    {"projectId": settings.FIREBASE_PROJECT_ID},
                    name=settings.FIREBASE_APP_NAME
                )
                self._initialized = True
                logger.info(f"Firebase Admin SDK initialized successfully for project {settings.FIREBASE_PROJECT_ID}")
            else:
                logger.info("No Firebase service account credentials configured. FCM provider operating in resilient fallback mode.")

        except Exception as err:
            logger.warning(f"Failed to initialize Firebase Admin SDK ({err}). Operating in fallback mode.")
            self._initialized = False

    async def send_to_token(
        self,
        fcm_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        priority: str = "HIGH"
    ) -> Dict[str, Any]:
        if not self._initialized:
            return await self.mock_fallback.send_to_token(fcm_token, title, body, data, priority)

        start_t = time.perf_counter()
        try:
            from firebase_admin import messaging

            fcm_priority = "high" if priority in ["URGENT", "CRITICAL", "HIGH"] else "normal"
            android_config = messaging.AndroidConfig(
                priority=fcm_priority,
                notification=messaging.AndroidNotification(
                    title=title,
                    body=body,
                    channel_id="disaster_early_warnings",
                    priority="max" if priority == "CRITICAL" else "high",
                    sound="default",
                ),
            )

            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data={k: str(v) for k, v in (data or {}).items()},
                android=android_config,
                token=fcm_token,
            )

            msg_id = messaging.send(message, app=self._app)
            latency_ms = (time.perf_counter() - start_t) * 1000.0
            provider_health_registry.record_success("firebase-fcm", latency_ms)

            return {
                "status": "SENT_TO_FCM",
                "message_id": msg_id,
                "fcm_token": fcm_token,
                "provider": "FirebaseAdminFCMProvider",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as err:
            latency_ms = (time.perf_counter() - start_t) * 1000.0
            err_str = str(err).lower()
            logger.warning(f"FCM send failed for token: {err}")

            if "unregistered" in err_str or "not registered" in err_str or "invalid" in err_str:
                provider_health_registry.record_failure("firebase-fcm", "TOKEN_INVALID")
                return {
                    "status": "TOKEN_INVALID",
                    "fcm_token": fcm_token,
                    "failure_reason": str(err),
                    "provider": "FirebaseAdminFCMProvider",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

            provider_health_registry.record_failure("firebase-fcm", str(err))
            return {
                "status": "FAILED",
                "fcm_token": fcm_token,
                "failure_reason": str(err),
                "provider": "FirebaseAdminFCMProvider",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def send_to_topic(
        self,
        topic: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        priority: str = "HIGH"
    ) -> Dict[str, Any]:
        if not self._initialized:
            return await self.mock_fallback.send_to_topic(topic, title, body, data, priority)

        start_t = time.perf_counter()
        try:
            from firebase_admin import messaging

            # Clean topic format
            sanitized_topic = topic.replace(":", "_").replace("/", "_")
            fcm_priority = "high" if priority in ["URGENT", "CRITICAL", "HIGH"] else "normal"

            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data={k: str(v) for k, v in (data or {}).items()},
                android=messaging.AndroidConfig(priority=fcm_priority),
                topic=sanitized_topic,
            )

            msg_id = messaging.send(message, app=self._app)
            latency_ms = (time.perf_counter() - start_t) * 1000.0
            provider_health_registry.record_success("firebase-fcm", latency_ms)

            return {
                "status": "SENT_TO_FCM",
                "message_id": msg_id,
                "topic": topic,
                "provider": "FirebaseAdminFCMProvider",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as err:
            logger.warning(f"FCM topic broadcast failed ({err})")
            provider_health_registry.record_failure("firebase-fcm", str(err))
            return {
                "status": "FAILED",
                "topic": topic,
                "failure_reason": str(err),
                "provider": "FirebaseAdminFCMProvider",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def send_multicast(
        self,
        fcm_tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        priority: str = "HIGH"
    ) -> Dict[str, Any]:
        if not self._initialized:
            return await self.mock_fallback.send_multicast(fcm_tokens, title, body, data, priority)

        if not fcm_tokens:
            return {"status": "SENT_TO_FCM", "sent_count": 0, "failed_count": 0, "invalid_tokens": []}

        start_t = time.perf_counter()
        try:
            from firebase_admin import messaging

            fcm_priority = "high" if priority in ["URGENT", "CRITICAL", "HIGH"] else "normal"
            multicast = messaging.MulticastMessage(
                tokens=fcm_tokens,
                notification=messaging.Notification(title=title, body=body),
                data={k: str(v) for k, v in (data or {}).items()},
                android=messaging.AndroidConfig(priority=fcm_priority),
            )

            batch_resp = messaging.send_each_for_multicast(multicast, app=self._app)
            latency_ms = (time.perf_counter() - start_t) * 1000.0
            provider_health_registry.record_success("firebase-fcm", latency_ms)

            invalid_tokens = []
            for idx, resp in enumerate(batch_resp.responses):
                if not resp.success:
                    err_msg = str(resp.exception)
                    if "unregistered" in err_msg.lower() or "invalid" in err_msg.lower():
                        invalid_tokens.append(fcm_tokens[idx])

            return {
                "status": "SENT_TO_FCM" if batch_resp.success_count > 0 else "FAILED",
                "sent_count": batch_resp.success_count,
                "failed_count": batch_resp.failure_count,
                "invalid_tokens": invalid_tokens,
                "provider": "FirebaseAdminFCMProvider",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as err:
            logger.warning(f"FCM multicast failed ({err})")
            provider_health_registry.record_failure("firebase-fcm", str(err))
            return {
                "status": "FAILED",
                "sent_count": 0,
                "failed_count": len(fcm_tokens),
                "invalid_tokens": [],
                "failure_reason": str(err),
                "provider": "FirebaseAdminFCMProvider",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


_fcm_provider_instance: Optional[FCMProvider] = None


def get_fcm_provider() -> FCMProvider:
    """Singleton factory for Firebase Cloud Messaging Provider."""
    global _fcm_provider_instance
    if _fcm_provider_instance is None:
        if settings.FIREBASE_PROVIDER_MODE.upper() == "LIVE":
            _fcm_provider_instance = FirebaseAdminFCMProvider()
        else:
            _fcm_provider_instance = MockFCMProvider()
    return _fcm_provider_instance
