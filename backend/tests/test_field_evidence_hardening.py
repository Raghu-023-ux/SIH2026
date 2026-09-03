import pytest
from datetime import datetime, timezone
from backend.app.services.field_service import field_service, FieldOperationsService
from backend.app.schemas.field import (
    FieldReportCreate,
    FieldReportUpdate,
    TeamStatusUpdateRequest,
)
from backend.app.services.scientific_indicators_service import scientific_indicators_service


@pytest.mark.asyncio
async def test_field_evidence_submission_and_validation(db_session):
    # 1. Verify invalid severity rejection
    with pytest.raises(ValueError, match="Invalid severity"):
        invalid_sev = FieldReportCreate(
            location_id="NER-SIK-GANGTOK-01",
            report_type="LANDSLIDE",
            severity="SUPER_EXTREME",
            description="Test invalid severity",
        )
        await field_service.submit_field_report(db_session, invalid_sev)

    # 2. Verify invalid GPS coordinates rejection
    with pytest.raises(ValueError, match="Latitude must be between -90.0 and 90.0"):
        invalid_gps = FieldReportCreate(
            location_id="NER-SIK-GANGTOK-01",
            report_type="LANDSLIDE",
            severity="HIGH",
            description="Test invalid latitude",
            latitude=120.0,
            longitude=88.0,
        )
        await field_service.submit_field_report(db_session, invalid_gps)

    # 3. Valid submission with image storage keys
    valid_report_in = FieldReportCreate(
        location_id="NER-SIK-GANGTOK-01",
        team_id="NER-TEAM-ALPHA",
        reported_by="SDRF Quick Response Unit Alpha (ALPHA-1)",
        report_type="SLOPE_FAILURE",
        severity="HIGH",
        description="Fresh 4-meter tension crack observed along NH-10 road edge at Km 42.",
        latitude=27.3390,
        longitude=88.6068,
        location_accuracy=8.5,
        location_source="GPS",
        image_storage_keys=["field_evidence/gangtok_crack_01.jpg"]
    )
    report = await field_service.submit_field_report(db_session, valid_report_in)
    assert report.id is not None
    assert report.status == "SUBMITTED"
    assert report.report_type == "SLOPE_FAILURE"
    assert report.severity == "HIGH"
    
    # Format report response
    formatted = FieldOperationsService.format_report_response(report)
    assert formatted.id == report.id
    assert formatted.report_type == "SLOPE_FAILURE"
    assert len(formatted.images) == 1
    assert formatted.images[0].storage_key == "field_evidence/gangtok_crack_01.jpg"



@pytest.mark.asyncio
async def test_field_evidence_station360_integration(db_session):
    # Verify Station 360 payload includes field reports
    investigation = await scientific_indicators_service.build_investigation_response(
        db_session,
        "NER-SIK-GANGTOK-01"
    )
    assert investigation is not None
    assert hasattr(investigation, "field_reports")
    assert isinstance(investigation.field_reports, list)


@pytest.mark.asyncio
async def test_field_team_status_transitions(db_session):
    teams = await field_service.get_all_teams(db_session)
    alpha = teams[0]

    # Valid status transition: ASSIGNED -> EN_ROUTE -> ON_SITE -> ASSESSING
    for valid_status in ["ASSIGNED", "EN_ROUTE", "ON_SITE", "ASSESSING", "REPORT_SUBMITTED"]:
        updated = await field_service.update_team_status(
            db_session,
            alpha.id,
            status=valid_status,
            latitude=27.3392,
            longitude=88.6067
        )
        assert updated.status == valid_status

    # Invalid status rejection
    with pytest.raises(ValueError, match="Invalid field unit status"):
        await field_service.update_team_status(
            db_session,
            alpha.id,
            status="UNKNOWN_FANTASY_STATE"
        )
