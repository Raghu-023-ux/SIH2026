from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_db
from backend.app.schemas.device import (
    DeviceRegisterRequest,
    DeviceUpdateRequest,
    DeviceRegisterResponse,
    FCMNotificationMessage,
)
from backend.app.services.device_service import device_service, DeviceService
from backend.app.services.fcm_provider import get_fcm_provider
from backend.app.core.logging import logger

router = APIRouter()


@router.post("/devices", response_model=DeviceRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_device(
    req: DeviceRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Registers or updates an Android, iOS, or Web FCM registration token.
    Idempotent: updates existing token attributes and GPS coordinates without duplicating rows.
    """
    try:
        device = await device_service.register_or_update_device(db, req)
        await db.commit()
        await db.refresh(device)
        return DeviceRegisterResponse(
            id=device.id,
            user_id=device.user_id,
            fcm_token=device.fcm_token,
            platform=device.platform,
            device_name=device.device_name,
            app_version=device.app_version,
            latitude=device.latitude,
            longitude=device.longitude,
            topic_subscriptions=device.topic_subscriptions or [],
            is_active=device.is_active,
            last_seen_at=device.last_seen_at,
            created_at=device.created_at,
            updated_at=device.updated_at,
            message="Device token registered successfully."
        )
    except Exception as err:
        logger.error(f"Device registration failed: {err}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device registration failed: {str(err)}"
        )


@router.put("/devices/{fcm_token}", response_model=DeviceRegisterResponse)
async def update_device(
    fcm_token: str,
    req: DeviceUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Updates GPS coordinates, app version, topic subscriptions, or active status for a registered device.
    """
    device = await device_service.update_device_location_or_preferences(db, fcm_token, req)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device token not found"
        )
    await db.commit()
    await db.refresh(device)
    return DeviceRegisterResponse(
        id=device.id,
        user_id=device.user_id,
        fcm_token=device.fcm_token,
        platform=device.platform,
        device_name=device.device_name,
        app_version=device.app_version,
        latitude=device.latitude,
        longitude=device.longitude,
        topic_subscriptions=device.topic_subscriptions or [],
        is_active=device.is_active,
        last_seen_at=device.last_seen_at,
        created_at=device.created_at,
        updated_at=device.updated_at,
        message="Device updated successfully."
    )


@router.delete("/devices/{fcm_token}", status_code=status.HTTP_200_OK)
async def unregister_device(
    fcm_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivates an FCM device registration token.
    Retains audit history in PostgreSQL while preventing future push dispatches.
    """
    deactivated = await device_service.deactivate_token(db, fcm_token, reason="User uninstalled or disabled push notifications")
    if not deactivated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device token not found"
        )
    await db.commit()
    return {"status": "DEACTIVATED", "fcm_token": fcm_token, "message": "Device token deactivated."}


@router.get("/devices", response_model=List[DeviceRegisterResponse])
async def list_devices(
    active_only: bool = Query(True),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists registered device tokens with metadata and active state (administrative/monitoring).
    """
    devices = await device_service.list_devices(db, active_only=active_only, limit=limit)
    return [
        DeviceRegisterResponse(
            id=d.id,
            user_id=d.user_id,
            fcm_token=d.fcm_token,
            platform=d.platform,
            device_name=d.device_name,
            app_version=d.app_version,
            latitude=d.latitude,
            longitude=d.longitude,
            topic_subscriptions=d.topic_subscriptions or [],
            is_active=d.is_active,
            last_seen_at=d.last_seen_at,
            created_at=d.created_at,
            updated_at=d.updated_at,
            message="Active device record."
        )
        for d in devices
    ]


@router.post("/send-test", status_code=status.HTTP_200_OK)
async def send_test_push_notification(
    msg: FCMNotificationMessage,
):
    """
    Dispatches a test push notification via FCM provider abstraction (to token or topic).
    """
    provider = get_fcm_provider()
    if msg.topic:
        res = await provider.send_to_topic(
            topic=msg.topic,
            title=msg.title,
            body=msg.body,
            data=msg.data,
            priority=msg.priority,
        )
    elif msg.fcm_token:
        res = await provider.send_to_token(
            fcm_token=msg.fcm_token,
            title=msg.title,
            body=msg.body,
            data=msg.data,
            priority=msg.priority,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'fcm_token' or 'topic' must be specified."
        )

    return res
