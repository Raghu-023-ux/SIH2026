from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, update
from fastapi import HTTPException, status

from backend.app.models.device import DeviceToken
from backend.app.schemas.device import DeviceRegisterRequest, DeviceUpdateRequest
from backend.app.core.logging import logger


class DeviceService:
    """
    Device Registration & Token Management Service.
    Maintains authoritative device records in PostgreSQL and manages FCM token lifecycle.
    """

    @staticmethod
    async def register_or_update_device(
        session: AsyncSession,
        req: DeviceRegisterRequest,
    ) -> DeviceToken:
        token_str = req.fcm_token.strip()
        now = datetime.now(timezone.utc)

        # 1. Check if token is already registered
        stmt = select(DeviceToken).where(DeviceToken.fcm_token == token_str)
        res = await session.execute(stmt)
        device = res.scalar_one_or_none()

        if device:
            # Update existing device record (idempotent)
            device.platform = req.platform.upper()
            if req.user_id:
                device.user_id = req.user_id
            if req.device_name:
                device.device_name = req.device_name
            if req.app_version:
                device.app_version = req.app_version
            if req.latitude is not None and req.longitude is not None:
                device.latitude = req.latitude
                device.longitude = req.longitude
            if req.topic_subscriptions is not None:
                device.topic_subscriptions = req.topic_subscriptions
            
            device.is_active = True
            device.deactivation_reason = None
            device.last_seen_at = now
            device.updated_at = now
            logger.info(f"Updated active FCM device token: {device.id} ({device.platform})")
        else:
            # Create new device record
            device = DeviceToken(
                fcm_token=token_str,
                platform=req.platform.upper(),
                user_id=req.user_id,
                device_name=req.device_name,
                app_version=req.app_version,
                latitude=req.latitude,
                longitude=req.longitude,
                topic_subscriptions=req.topic_subscriptions or [],
                is_active=True,
                last_seen_at=now,
                created_at=now,
                updated_at=now,
            )
            session.add(device)
            logger.info(f"Registered new FCM device token: {device.id} ({device.platform})")

        await session.flush()
        return device

    @staticmethod
    async def update_device_location_or_preferences(
        session: AsyncSession,
        fcm_token: str,
        req: DeviceUpdateRequest,
    ) -> Optional[DeviceToken]:
        stmt = select(DeviceToken).where(DeviceToken.fcm_token == fcm_token.strip())
        res = await session.execute(stmt)
        device = res.scalar_one_or_none()
        if not device:
            return None

        now = datetime.now(timezone.utc)
        if req.latitude is not None and req.longitude is not None:
            device.latitude = req.latitude
            device.longitude = req.longitude
        if req.app_version:
            device.app_version = req.app_version
        if req.topic_subscriptions is not None:
            device.topic_subscriptions = req.topic_subscriptions
        if req.is_active is not None:
            device.is_active = req.is_active

        device.last_seen_at = now
        device.updated_at = now
        await session.flush()
        return device

    @staticmethod
    async def deactivate_token(
        session: AsyncSession,
        fcm_token: str,
        reason: Optional[str] = "Token unregistered or invalid",
    ) -> bool:
        stmt = select(DeviceToken).where(DeviceToken.fcm_token == fcm_token.strip())
        res = await session.execute(stmt)
        device = res.scalar_one_or_none()
        if not device:
            return False

        device.is_active = False
        device.deactivation_reason = reason
        device.updated_at = datetime.now(timezone.utc)
        await session.flush()
        logger.info(f"Deactivated invalid FCM device token: {device.id} (Reason: {reason})")
        return True

    @staticmethod
    async def get_active_devices_by_target(
        session: AsyncSession,
        target_type: str,
        target_filter: Optional[Dict[str, Any]] = None,
        limit: int = 500,
    ) -> List[DeviceToken]:
        """
        Resolves active devices based on audience criteria:
        - 'PUBLIC_USERS': All active devices
        - 'EVENT_AREA': Devices within bounding box / radius
        - 'FIELD_TEAMS': Devices belonging to field responders
        """
        stmt = select(DeviceToken).where(DeviceToken.is_active == True)

        if target_type == "EVENT_AREA" and target_filter:
            lat = target_filter.get("latitude")
            lon = target_filter.get("longitude")
            radius_km = target_filter.get("radius_km", 25.0)
            if lat is not None and lon is not None:
                # Approximate 1 deg lat ~ 111 km
                delta_deg = radius_km / 111.0
                stmt = stmt.where(
                    and_(
                        DeviceToken.latitude.between(lat - delta_deg, lat + delta_deg),
                        DeviceToken.longitude.between(lon - delta_deg, lon + delta_deg),
                    )
                )
        elif target_type == "FIELD_TEAMS":
            stmt = stmt.where(DeviceToken.user_id.is_not(None))

        stmt = stmt.limit(limit)
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def list_devices(
        session: AsyncSession,
        active_only: bool = True,
        limit: int = 100,
    ) -> List[DeviceToken]:
        stmt = select(DeviceToken)
        if active_only:
            stmt = stmt.where(DeviceToken.is_active == True)
        stmt = stmt.order_by(DeviceToken.last_seen_at.desc()).limit(limit)
        res = await session.execute(stmt)
        return list(res.scalars().all())


device_service = DeviceService()
