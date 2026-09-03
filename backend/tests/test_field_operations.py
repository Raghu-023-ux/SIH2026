import pytest
from datetime import datetime, timezone
from backend.app.services.field_service import field_service
from backend.app.schemas.field import (
    FieldReportCreate,
    FieldReportUpdate,
    AssistanceRequestCreate,
    AssistanceRequestUpdate,
    OperationalMessageCreate,
)


@pytest.mark.asyncio
async def test_field_teams_and_status(db_session):
    # 1. Verify seeded teams
    teams = await field_service.get_all_teams(db_session)
    assert len(teams) >= 3
    alpha = next((t for t in teams if t.callsign == "ALPHA-1"), None)
    assert alpha is not None
    assert alpha.status in ["AVAILABLE", "DEPLOYED", "ON_SCENE", "NEED_ASSISTANCE"]

    # 2. Update team status
    updated = await field_service.update_team_status(
        session=db_session,
        team_id=alpha.id,
        status="ON_SCENE",
        latitude=27.3395,
        longitude=88.6070
    )
    assert updated is not None
    assert updated.status == "ON_SCENE"
    assert updated.latitude == 27.3395


@pytest.mark.asyncio
async def test_field_report_lifecycle(db_session):
    teams = await field_service.get_all_teams(db_session)
    alpha = teams[0]

    # 1. Submit report
    report_in = FieldReportCreate(
        location_id="NER-SIK-GANGTOK-01",
        team_id=alpha.id,
        reported_by="SDRF Unit Alpha",
        report_type="ROAD_BLOCKED",
        severity="HIGH",
        description="NH-10 blocked by 50 cubic meters of mud and tree debris.",
        latitude=27.3390,
        longitude=88.6068
    )
    report = await field_service.submit_field_report(db_session, report_in)
    assert report.id is not None
    assert report.status == "SUBMITTED"

    # 2. Acknowledge report
    update_in = FieldReportUpdate(
        status="ACKNOWLEDGED",
        reviewed_by="Command Officer",
        review_notes="Relayed to Border Roads Organisation."
    )
    reviewed = await field_service.update_report_status(db_session, report.id, update_in)
    assert reviewed.status == "ACKNOWLEDGED"
    assert reviewed.reviewed_by == "Command Officer"


@pytest.mark.asyncio
async def test_assistance_and_operational_messages(db_session):
    teams = await field_service.get_all_teams(db_session)
    alpha = teams[0]

    # 1. Request SOS Assistance
    req_in = AssistanceRequestCreate(
        team_id=alpha.id,
        request_type="EQUIPMENT",
        priority="CRITICAL",
        description="Heavy earthmover required to clear arterial road blockage.",
        latitude=27.3390,
        longitude=88.6068
    )
    sos = await field_service.request_assistance(db_session, req_in)
    assert sos.status == "REQUESTED"

    # Team status should automatically transition to NEED_ASSISTANCE
    updated_team = await field_service.get_team_by_id_or_callsign(db_session, alpha.id)
    assert updated_team.status == "NEED_ASSISTANCE"

    # 2. Central sends operational message
    msg_in = OperationalMessageCreate(
        sender_id="Central HQ",
        recipient_team=alpha.callsign,
        priority="URGENT",
        message="Earthmover en route from Gangtok municipal depot. ETA 20 mins."
    )
    msg = await field_service.send_operational_message(db_session, msg_in)
    assert msg.id is not None
    assert msg.acknowledged_at is None

    # 3. Field acknowledges message
    ack = await field_service.acknowledge_operational_message(db_session, msg.id, alpha.callsign)
    assert ack.acknowledged_at is not None
    assert ack.acknowledged_by == alpha.callsign
