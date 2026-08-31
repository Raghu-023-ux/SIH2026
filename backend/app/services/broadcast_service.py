import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from backend.app.models.alerting import Broadcast, Notification
from backend.app.models.field import FieldTeam, OperationalMessage
from backend.app.models.device import DeviceToken
from backend.app.schemas.alerting import BroadcastCreate, BroadcastStatusResponse, NotificationItemResponse
from backend.app.services.sms_provider import get_sms_provider, SMSProvider
from backend.app.services.fcm_provider import get_fcm_provider, FCMProvider
from backend.app.services.email_provider import get_email_provider, EmailProvider
from backend.app.services.email_templates import email_template_renderer
from backend.app.services.device_service import DeviceService

logger = logging.getLogger("broadcast_service")


class BroadcastService:
    """
    Core emergency broadcast orchestration service.
    Dispatches critical alerts asynchronously across In-App, SMS, Firebase FCM, and Resend Email channels.
    """

    @staticmethod
    async def create_broadcast(
        session: AsyncSession,
        req: BroadcastCreate,
    ) -> Broadcast:
        # 1. Validation
        if not req.title.strip() or not req.message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Broadcast title and message body cannot be empty",
            )
        if len(req.title) > 150:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Broadcast title exceeds 150 character limit",
            )
        if len(req.message) > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Broadcast message exceeds 1000 character limit",
            )

        valid_targets = ["FIELD_TEAMS", "PUBLIC_USERS", "EVENT_AREA", "CUSTOM_GROUP"]
        if req.target_type not in valid_targets:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid target type '{req.target_type}'. Allowed: {valid_targets}",
            )

        # 2. Persist Broadcast record
        broadcast = Broadcast(
            event_id=req.event_id,
            sender_id=req.sender_id or "Central Command Duty Officer",
            priority=req.priority,
            title=req.title.strip(),
            message=req.message.strip(),
            target_type=req.target_type,
            target_filter=req.target_filter,
            created_at=datetime.now(timezone.utc),
        )
        session.add(broadcast)
        await session.flush()

        # 3. Resolve Recipients
        recipient_teams = []
        if req.target_type in ["FIELD_TEAMS", "EVENT_AREA", "CUSTOM_GROUP"]:
            team_stmt = select(FieldTeam)
            if req.target_type == "EVENT_AREA" and req.event_id:
                team_stmt = team_stmt.where(FieldTeam.assigned_event_id == req.event_id)
            res = await session.execute(team_stmt)
            teams = res.scalars().all()
            if teams:
                recipient_teams = [t.callsign for t in teams]
            else:
                recipient_teams = ["ALPHA-1", "BRAVO-2", "CHARLIE-3"]
        else:
            # PUBLIC_USERS or broader
            recipient_teams = ["PUBLIC_ZONE_NER_01", "PUBLIC_ZONE_NER_02", "ALL_FIELD_TEAMS"]

        # Default mock phone contacts for recipients
        recipient_contacts = {
            "ALPHA-1": "+919800011111",
            "BRAVO-2": "+919800022222",
            "CHARLIE-3": "+919800033333",
            "PUBLIC_ZONE_NER_01": "+919811100001",
            "PUBLIC_ZONE_NER_02": "+919811100002",
            "ALL_FIELD_TEAMS": "+919800099999",
        }

        requested_channels = req.channels or ["IN_APP", "SMS"]

        # 4. Create Notification Queue Jobs in DB
        notifications_to_create = []
        for recip in recipient_teams:
            if "IN_APP" in requested_channels:
                notifications_to_create.append(
                    Notification(
                        broadcast_id=broadcast.id,
                        recipient_id=recip,
                        channel="IN_APP",
                        status="QUEUED",
                        created_at=datetime.now(timezone.utc),
                    )
                )
            if "SMS" in requested_channels:
                phone = recipient_contacts.get(recip, "+919800012345")
                notifications_to_create.append(
                    Notification(
                        broadcast_id=broadcast.id,
                        recipient_id=f"{recip} ({phone})",
                        channel="SMS",
                        status="QUEUED",
                        created_at=datetime.now(timezone.utc),
                    )
                )

        # 5. FCM Push Delivery Channel
        if any(c in requested_channels for c in ["FCM", "PUSH", "IN_APP_PUSH"]):
            active_devices = await DeviceService.get_active_devices_by_target(
                session=session,
                target_type=req.target_type,
                target_filter=req.target_filter,
                limit=100
            )

            if active_devices:
                for dev in active_devices:
                    notifications_to_create.append(
                        Notification(
                            broadcast_id=broadcast.id,
                            recipient_id=f"device:{dev.id}:{dev.fcm_token}",
                            channel="FCM",
                            status="QUEUED",
                            created_at=datetime.now(timezone.utc),
                        )
                    )
            else:
                target_topic = f"region_{req.target_type.lower()}"
                notifications_to_create.append(
                    Notification(
                        broadcast_id=broadcast.id,
                        recipient_id=f"topic:{target_topic}",
                        channel="FCM",
                        status="QUEUED",
                        created_at=datetime.now(timezone.utc),
                    )
                )

        # 6. Resend Email Delivery Channel
        if any(c in requested_channels for c in ["EMAIL", "RESEND", "EMAIL_BULLETIN"]):
            custom_emails = (req.target_filter or {}).get("emails", [])
            if custom_emails and isinstance(custom_emails, list):
                email_recipients = custom_emails
            else:
                email_recipients = [
                    "duty.officer@sikkim.gov.in",
                    "sdma.response@ner.gov.in",
                ]

            for em in email_recipients:
                notifications_to_create.append(
                    Notification(
                        broadcast_id=broadcast.id,
                        recipient_id=em,
                        channel="EMAIL",
                        status="QUEUED",
                        created_at=datetime.now(timezone.utc),
                    )
                )

        session.add_all(notifications_to_create)
        await session.commit()
        await session.refresh(broadcast)

        return broadcast

    @staticmethod
    async def process_broadcast(
        session: AsyncSession,
        broadcast_id: str,
    ):
        """
        Executes notification dispatch across all channels for a given broadcast ID using the provided session.
        """
        sms_provider = get_sms_provider()
        fcm_provider = get_fcm_provider()
        email_provider = get_email_provider()

        stmt = select(Broadcast).where(Broadcast.id == broadcast_id)
        res = await session.execute(stmt)
        broadcast = res.scalar_one_or_none()
        if not broadcast:
            logger.error(f"Broadcast {broadcast_id} not found for processing")
            return

        notif_stmt = select(Notification).where(
            Notification.broadcast_id == broadcast_id,
            Notification.status == "QUEUED",
        )
        n_res = await session.execute(notif_stmt)
        notifications = n_res.scalars().all()

        for notif in notifications:
            now = datetime.now(timezone.utc)
            if notif.channel == "IN_APP":
                try:
                    op_msg = OperationalMessage(
                        event_id=broadcast.event_id,
                        sender_id=broadcast.sender_id,
                        recipient_team=notif.recipient_id,
                        priority="URGENT" if broadcast.priority in ["URGENT", "CRITICAL"] else "NORMAL",
                        message=f"[{broadcast.title}] {broadcast.message}",
                        created_at=now,
                    )
                    session.add(op_msg)
                    notif.status = "SENT"
                    notif.sent_at = now
                except Exception as e:
                    notif.status = "FAILED"
                    notif.failure_reason = str(e)
            elif notif.channel == "SMS":
                try:
                    phone = notif.recipient_id.split("(")[-1].rstrip(")") if "(" in notif.recipient_id else notif.recipient_id
                    sms_res = await sms_provider.send_sms(
                        phone_number=phone,
                        message=f"EMERGENCY ALERT [{broadcast.priority}]: {broadcast.title} - {broadcast.message}",
                        sender_id=broadcast.sender_id,
                        priority=broadcast.priority,
                    )
                    if sms_res.get("status") in ["SENT", "DELIVERED"]:
                        notif.status = "SENT"
                        notif.sent_at = now
                    else:
                        notif.status = "FAILED"
                        notif.failure_reason = sms_res.get("failure_reason", "SMS gateway error")
                except Exception as e:
                    notif.status = "FAILED"
                    notif.failure_reason = str(e)
            elif notif.channel in ["FCM", "PUSH"]:
                try:
                    fcm_data = {
                        "broadcast_id": str(broadcast.id),
                        "event_id": str(broadcast.event_id or ""),
                        "priority": str(broadcast.priority),
                    }
                    if notif.recipient_id.startswith("topic:"):
                        topic_name = notif.recipient_id.split("topic:")[-1]
                        fcm_res = await fcm_provider.send_to_topic(
                            topic=topic_name,
                            title=broadcast.title,
                            body=broadcast.message,
                            data=fcm_data,
                            priority=broadcast.priority,
                        )
                    else:
                        fcm_token = notif.recipient_id.split(":")[-1] if "device:" in notif.recipient_id else notif.recipient_id
                        fcm_res = await fcm_provider.send_to_token(
                            fcm_token=fcm_token,
                            title=broadcast.title,
                            body=broadcast.message,
                            data=fcm_data,
                            priority=broadcast.priority,
                        )

                    if fcm_res.get("status") == "SENT_TO_FCM":
                        notif.status = "SENT"
                        notif.sent_at = now
                    elif fcm_res.get("status") == "TOKEN_INVALID":
                        notif.status = "FAILED"
                        notif.failure_reason = "TOKEN_INVALID"
                        fcm_token = notif.recipient_id.split(":")[-1] if "device:" in notif.recipient_id else notif.recipient_id
                        await DeviceService.deactivate_token(session, fcm_token, reason="TOKEN_INVALID")
                    else:
                        notif.status = "FAILED"
                        notif.failure_reason = fcm_res.get("failure_reason", "FCM delivery error")
                except Exception as e:
                    notif.status = "FAILED"
                    notif.failure_reason = str(e)
            elif notif.channel in ["EMAIL", "RESEND", "EMAIL_BULLETIN"]:
                try:
                    rendered = email_template_renderer.render_broadcast(
                        title=broadcast.title,
                        message=broadcast.message,
                        priority=broadcast.priority,
                        sender_id=broadcast.sender_id,
                        event_id=broadcast.event_id,
                    )
                    email_res = await email_provider.send_email(
                        to=notif.recipient_id,
                        subject=rendered["subject"],
                        html_body=rendered["html"],
                        text_body=rendered["text"],
                    )
                    if email_res.get("status") == "SENT_TO_PROVIDER":
                        notif.status = "SENT"
                        notif.sent_at = now
                    else:
                        notif.status = "FAILED"
                        notif.failure_reason = email_res.get("failure_reason", "Email delivery error")
                except Exception as e:
                    notif.status = "FAILED"
                    notif.failure_reason = str(e)

        await session.commit()
        logger.info(f"Broadcast {broadcast_id} completed processing {len(notifications)} notifications.")

    @staticmethod
    async def process_broadcast_background(
        broadcast_id: str,
        session_factory,
    ):
        """
        Background task to process queued notifications asynchronously.
        """
        async with session_factory() as session:
            await BroadcastService.process_broadcast(session, broadcast_id)

    @staticmethod
    async def get_broadcast_status(
        session: AsyncSession,
        broadcast_id: str,
    ) -> BroadcastStatusResponse:
        stmt = select(Broadcast).where(Broadcast.id == broadcast_id)
        res = await session.execute(stmt)
        broadcast = res.scalar_one_or_none()
        if not broadcast:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Broadcast '{broadcast_id}' not found",
            )

        notif_stmt = select(Notification).where(Notification.broadcast_id == broadcast_id)
        n_res = await session.execute(notif_stmt)
        notifs = n_res.scalars().all()

        in_app_sent = sum(1 for n in notifs if n.channel == "IN_APP" and n.status in ["SENT", "DELIVERED"])
        in_app_failed = sum(1 for n in notifs if n.channel == "IN_APP" and n.status == "FAILED")
        in_app_pending = sum(1 for n in notifs if n.channel == "IN_APP" and n.status == "QUEUED")

        sms_sent = sum(1 for n in notifs if n.channel == "SMS" and n.status in ["SENT", "DELIVERED"])
        sms_failed = sum(1 for n in notifs if n.channel == "SMS" and n.status == "FAILED")
        sms_pending = sum(1 for n in notifs if n.channel == "SMS" and n.status == "QUEUED")

        fcm_sent = sum(1 for n in notifs if n.channel in ["FCM", "PUSH"] and n.status in ["SENT", "DELIVERED"])
        fcm_failed = sum(1 for n in notifs if n.channel in ["FCM", "PUSH"] and n.status == "FAILED")
        fcm_pending = sum(1 for n in notifs if n.channel in ["FCM", "PUSH"] and n.status == "QUEUED")

        email_sent = sum(1 for n in notifs if n.channel in ["EMAIL", "RESEND", "EMAIL_BULLETIN"] and n.status in ["SENT", "DELIVERED"])
        email_failed = sum(1 for n in notifs if n.channel in ["EMAIL", "RESEND", "EMAIL_BULLETIN"] and n.status == "FAILED")
        email_pending = sum(1 for n in notifs if n.channel in ["EMAIL", "RESEND", "EMAIL_BULLETIN"] and n.status == "QUEUED")

        return BroadcastStatusResponse(
            id=broadcast.id,
            event_id=broadcast.event_id,
            sender_id=broadcast.sender_id,
            priority=broadcast.priority,
            title=broadcast.title,
            message=broadcast.message,
            target_type=broadcast.target_type,
            created_at=broadcast.created_at,
            total_recipients=len(notifs),
            in_app_sent=in_app_sent,
            in_app_failed=in_app_failed,
            in_app_pending=in_app_pending,
            sms_sent=sms_sent,
            sms_failed=sms_failed,
            sms_pending=sms_pending,
            fcm_sent=fcm_sent,
            fcm_failed=fcm_failed,
            fcm_pending=fcm_pending,
            email_sent=email_sent,
            email_failed=email_failed,
            email_pending=email_pending,
            notifications=[NotificationItemResponse.model_validate(n) for n in notifs],
        )
